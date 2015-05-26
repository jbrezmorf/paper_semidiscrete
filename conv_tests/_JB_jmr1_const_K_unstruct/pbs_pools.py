import subprocess
import os
import time
import re


class Chdir:
    """
    Context manager - possibly create a directory and change to it,
    on destruction change back
    """
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
            with open(job['modules_file'], "r") as f:
                modules = f.read().split("\n")
            qsub_script.extend(['module purge', 'module add /software/modules/current/metabase'])
            for module in modules:
                qsub_script.append("module add " + module)

            mpiexec = self.pbs_environment['mpiexec']
            call=[ mpiexec, job['executable'] ] + job['arguments']
            qsub_script.append( " ".join(call) )
            return "\n".join(qsub_script)

    def start_job(self, job):
        """
        Start a job under PBS. Jobs that have status at start are
        not started but directly added into pbs_jobs list.

        job is a dictionary with:
            "name" - OPTIONAL
            "work_dir" -
            "executable" - OBLIGATORY - path to executable, absolute or relative to work_dir
            "arguments" - list of arguments (will be separated by space)
            "modules" - list of modules to load before start, if specified we purge modules befor loading
                        otherwise we leave those loaded by default (e.g. provided in .profile)
            "modules_file"
            "n_proc" - number of processes
            "time_wall" - upper time estimate
            "mem_size"
            any other option from pbs_environment can be overwritten
        pbs_environment:
            "mpiexec" - if provided, use given mpirun command to run executable
            "pbs_options"
        """
        print "starting job: ", job
        if not job or not 'executable' in job:
            return -1
        if job.has_key('status'):
            job['pbs_id']=0
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

            n_proc = min( 24, int(job['n_proc']) )
            mem_limit = min( 16000, int(job['memory'])) 
            infiniband=""
            if n_proc>1: infiniband=":infiniband"
            call_list=["qsub", "-q", "short", "-l", "nodes="+str(n_proc)+":x86_64:mem=" + str(mem_limit) + "mb"+infiniband, qsub_script]
            print call_list
            #result=subprocess.check_output(["qsub", "-l nodes=1:x86_64:walltime=" + job['wall_time'], qsub_script])
            result=subprocess.check_output(call_list)
            print "qsub result: ", result
            match=re.match( r'([0-9]*)\.[a-z.]*', result)
            job['pbs_id']=match.group(1)
            assert( self.__check_job_status(job)[1] == 'Q' )
            self.pbs_jobs.append( job )
        return job['pbs_id']

    def __check_job_status(self, job):
        if job.has_key('status'): return (None, job['status'], None)
        job_id = job['pbs_id']
        out=subprocess.check_output(["qstat", job_id])
        status = out.split("\n")[2].split()
        print "job status: ", status, job['case'].workdir
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
            #print job['pbs_id'], status
            if status in ['C', 'E']:
                job['status']=status
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
                job['status']=(None, result, None)
                self.pbs_jobs.append( job )
        return len(self.pbs_jobs)

    def get_finished_jobs(self):
        result = self.pbs_jobs
        self.pbs_jobs=[]
        return result

    def wait_for_results(self):
        return self.pbs_jobs

