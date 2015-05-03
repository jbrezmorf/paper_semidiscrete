import subprocess
import os
from multiprocessing import Pool
import postprocess
#import csv
import json
import time
import re
import conv_tables
import math
import sys

con_2d="flow_exp_sin_2d2d.con"
con_1d="flow_exp_sin_2d1d.con"
home = os.path.expanduser("~")
flow_path=home + "/workspace/flow123d/bin/flow123d"
#gmsh_path=home + "/local/gmsh-2.8.5-Linux/bin/gmsh"
gmsh_path="gmsh"


def run_gmsh(geo_file):   
    mesh_file=geo_file.replace(".geo", ".msh")
    if not os.path.isfile(mesh_file):
      subprocess.call([gmsh_path, geo_file, "-2", "-o", mesh_file])    
      



def file_substitute(filename_in, subst_list):
    """
    Replace parameters in file template "../filename_in".
    subst_list contain tuples: ( string_to_replace, value)    
    """
    with open("../" + filename_in, 'r') as in_file:
        content = in_file.read()
        for (pattern, value) in subst_list:
            content=content.replace(pattern, str(value))
        with open("./" + filename_in, 'w') as out_file:
            out_file.write(content)
            
class Chdir:           
    def __init__(self,  newPath):
        self.newPath=newPath
        
    def __enter__(self):  
        self.savedPath = os.getcwd()        
        if not os.path.exists(self.newPath):
            os.makedirs(self.newPath)
        os.chdir(self.newPath)
        return self.newPath

    def __exit__(self, type, value, traceback):
        os.chdir( self.savedPath )




class pbs_pool:

    def __init__(self, environment):
        self.pbs_jobs=[]
        self.pbs_environment=environment

    def __make_pbs_script(self, job):
            qsub_script=[
            '#!/bin/bash',
            '#PBS -S /bin/bash',
            '#PBS -N ' + job['name'],
            '#PBS -j oe',
            'cd ' + job['work_dir'],
            'pbsdsh hostname']
            if 'modules' in job:
                qsub_script.extend(
                    ['module purge', 'module add /software/modules/current/metabase']
                    + job['modules']
                )

            call=[ job['executable'] ] + job['arguments']
            qsub_script.append( " ".join(call) )
            return "\n".join(qsub_script)

    def start_job(self, job):
        """
        Start a job under PBS.
        job: dictionary with:
            "name" - OPTIONAL
            "work_dir" -
            "executable" - OBLIGATORY - path to executable, absolute or relative to work_dir
            "arguments" - list of arguments (will be separated by space)
            "modules" - list of modules to load before start, if specified we purge modules befor loading
                        otherwise we leave those loaded by default (e.g. provided in .profile)
            "n_proc" - number of processes
            "time_wall" - upper time estimate
            "mem_size"
            any other option from pbs_environment can be overwritten
        pbs_environment:
            "mpirun" - if provided, use given mpirun command to run executable
            "pbs_options'
        """
        print "start job: ", job
        if not job or not 'executable' in job:
            return -1
        if job.has_key('status'):
            self.pbs_jobs.append(job)
            return 0

        job.setdefault('name', 'flow123d')
        job.setdefault('work_dir', os.getcwd() )
        job.setdefault('arguments', [] )
        if not os.path.isfile(job['executable']):
            print "No job executable: " + job['executable']

        with Chdir(job['work_dir']) as changed_dir:
            job['work_dir']=os.getcwd() # abs path
            print "work dir: ", job['work_dir']
            qsub_script=job['name']+'.qsub'
            with open(qsub_script, "w") as f:
                f.write( self.__make_pbs_script(job) )

            n_proc = min( 16, job['n_proc'] )
            #result=subprocess.check_output(["qsub", "-l nodes=1:x86_64:walltime=" + job['wall_time'], qsub_script])
            result=subprocess.check_output(["qsub", "-q", "short", "-l", "nodes="+n_proc+":x86_64:mem=4gb:infiniband", qsub_script])
            print "qsub result: ", result
            match=re.match( r'([0-9]*)\.[a-z.]*', result)            
            job['pbs_id']=match.group(1)
            assert( self.__check_job_status(job)[1] == 'Q' )
            self.pbs_jobs.append( job )
        return job['pbs_id']

    def __check_job_status(self, job):
        job_id = job['pbs_id']
        out=subprocess.check_output(["qstat", job_id])
        status = out.split("\n")[2].split()
        print "job status: ", status
        # return time_use, status Q/R/C/E, queue
        return (status[3], status[4], status[5])

    def get_finished_jobs(self):
        """
        Return list of jobs finished till the last call.
        """
        results=[]
        new_jobs=[]
        for job in self.pbs_jobs:
            status = self.__check_job_status(job)[1]
            print job['pbs_id'], status
            if status in ['C', 'E']:
                job['final_status']=status
                job.pop('pbs_id', None)
                results.append(job)
            else:
                new_jobs.append(job)
        self.pbs_jobs=new_jobs
        return results

    def wait_for_results(self):
        """
        Return list of finished jobs with added key: 'final_status'
        """
        results=[]
        while self.pbs_jobs:
            results += self.get_finished_jobs()
            print "--- waiting"
            time.sleep(1)
        return results

class local_pool:

    def __init__(self, environment):
        self.pbs_jobs=[]
        self.pbs_environment=environment

    def start_job(self, job):
        print "start job: ", job
        if not job or not 'executable' in job:
            return -1
        if job.has_key('status'):
            self.pbs_jobs.append(job)
        else:
            job.setdefault('name', 'flow123d')
            job.setdefault('work_dir', os.getcwd() )
            job.setdefault('arguments', [] )
            print job['work_dir']
            with Chdir(job['work_dir']) as changed_dir:
                call=[ job['executable'] ] + job['arguments']
                result=subprocess.call( call )
                job['final_status']=(None, result, None)
                self.pbs_jobs.append( job )
        return len(self.pbs_jobs)

    def get_finished_jobs(self):
        result = self.pbs_jobs
        self.pbs_jobs=[]
        return result

    def wait_for_results(self):
        return self.pbs_jobs



def get_flow_job(rule_pair):
    (con_file, output_file) = rule_pair
    (out_dir,  dummy)=os.path.split(output_file)
    job= {'executable' : flow_path,
            'arguments' : ["-s", con_file, "-o", out_dir ],
            'work_dir' : os.getcwd()
            }
    if os.path.isfile(output_file):
        job['status']='C'
    return job


def msh_n_elements(file_name):
    with open(file_name) as f:
        for line in f:
            if "$Elements" in line:
                str_el = next(f)
                try:
                    return int(str_el)
                except ValueError:
                    print "Not a number:", str_el


def num(s):


                return next(f)


def make_jobs_for_case(case):
    """
    Return tuple of two jobs
    """
    ih, h, id_frac, d_frac, subdir = case

    print case
    with Chdir(subdir) as changed_dir:

        file_substitute("mesh_2d2d.geo", [ ("$d$", d_frac), ("$h$", h)])
        run_gmsh("mesh_2d2d.geo")
        file_substitute(con_2d, [ ("$rozevreni$", d_frac) ])
        output_2d="output_2d/flow_2d2d.pvd"

        file_substitute("mesh_2d1d.geo", [ ("$d$", d_frac), ("$h$", h)])
        run_gmsh("mesh_2d1d.geo")
        file_substitute(con_1d, [ ("$rozevreni$", d_frac) ])
        output_1d="output_1d/flow_2d1d.pvd"

        file_substitute("filter_resample_2d1d.py", [ ("$rozevreni$", d_frac) ])

        n_ele = msh_n_elements("mesh_2d2d.msh")
        print n_ele
        job_common={ 'wall_time' : '1:50:00',
                     'n_proc' : round(n_ele / 30000),
                     'case' : case
                     }
        job1=get_flow_job((con_1d, output_1d))
        job1.update(job_common)
        job2=get_flow_job((con_2d, output_2d))
        job2.update(job_common)
        return (job1, job2)


def make_cases(h_array, d_frac_array):
    # make cases
    case_list=[]
    for ih, h in enumerate(h_array):
        for id_frac, d_frac in enumerate(d_frac_array):
            if h > d_frac:
                continue
            subdir="h_" + str(h) + "_d_" + str(d_frac)
            case_list.append( (ih, h, id_frac, d_frac, subdir) )
    return case_list


def postprocess_finished_jobs(job_pairs):
    norm_list=[]
    for subdir, job_pair in job_pairs.items():
        if len(job_pair)==2:
            job1, job2 = job_pair
            assert( job1['case'] == job2['case'] )
            case = job1['case']
            with Chdir(subdir) as dir:
                output_1d="output_1d/flow_2d1d.pvd"
                output_2d="output_2d/flow_2d2d.pvd"
                print subdir
                try:
                    norms=postprocess.postprocess(output_1d, output_2d)
                except:
                    norms={"error" : str(sys.exc_info())}
                keys=[ "ih", "h", "id_frac", "d_frac", "subdir" ]
                case_dict = dict(zip(keys, case))
                norm_list.append( ( case_dict,  norms ) )
            del job_pairs[subdir]
    return norm_list

def compute_all_cases(cases):
    # make jobs
    #pool = pbs_pool({})
    pool=local_pool({})

    for case in cases:
        job_1d, job_2d = make_jobs_for_case(case)
        print "pool:", case
        pool.start_job(job_1d)
        pool.start_job(job_2d)    

    norm_list=[]
    finished_jobs=[]
    job_pairs={}
    while (pool.pbs_jobs or finished_jobs):
        if len(finished_jobs)>0:
            for job in finished_jobs:
                ih, h, id_frac, d_frac, subdir = job['case']
                job_pairs.setdefault(subdir, []).append(job)
            norm_list += postprocess_finished_jobs(job_pairs)
            tables_dict=conv_tables.make_table(norm_list)
            conv_tables.write_tables(tables_dict, "norm_tabs.csv")
        else:
            time.sleep(1)
        finished_jobs = pool.get_finished_jobs()
    return norm_list


def main():
    #d_frac_array = [0.1*pow(0.5, n) for n in range(-2, 5)]
    #h_array = [0.01*pow(0.5, n) for n in range(-1, 4)]
    h_array=[0.01, 0.02]
    #d_frac_array = [0.1*pow(0.5, n) for n in range(-1, 1)]
    #h_array = [0.01*pow(0.5, n) for n in range(-1, 1)]
    d_frac_array = [0.2, 0.025]
    #h_array = [0.005]

    norms_list = compute_all_cases( make_cases( h_array, d_frac_array ) )
    #with open("norms_raw.json", "wb") as f:
    #    json.dump(norms_list, f)

    tables_dict=conv_tables.make_table(norms_list)
    conv_tables.write_tables(tables_dict, "norm_tabs.csv")


if __name__ == "__main__":
   main()
