"""
Logic of the scripts is as follows.

1) make 'cases' list from d_frac_array and h_array (see make_cases)
2) for every case make its work directory and substitute into template files:
   'filter_resample_12d.py',
   'mesh_2d2d.geo', 'mesh_2d1d.geo'
   con_2d, con_1d
   Files are created only if they doesn't exist.
   (see make_jobs_for_case)
3) If output PVD file doesn't exist the job execution is added to the pool.
4) When some case have both jobs completed, and the file 'norms_raw.json'
   does'nt exist the postprocess script is run to compute norms.
   Since pvpython is unstable, one have to restart this step few times. BAD.
5) After you have created all 'norm_raw.py' , possibly restarting 'run_all.py' few times.
 You can call conv_tables.py (can use python), to
 1) colect norms from subdirectories into norms_all.json (if it doesn't exist)
 2) make tables and plots
"""



#from multiprocessing import Pool
#import postprocess
#import csv
import json
import time
import copy
#import re
#import conv_tables
#import math
#import sys
from pbs_pools import *

from convergence_cases import *
from convergence_cases import ConvergenceTestSetting as cts

# setting
cts.con_base="flow_jmr1" # full name: con_base + "_" + prefix +".con"
home = os.path.expanduser("~")
cts.flow_path=home + "/workspace/flow123d/bin/flow123d"
cts.modules_file=home + "/workspace/flow123d/build_modules"
cts.mpiexec=home + "/workspace/flow123d/bin/mpiexec"
cts.gmsh_path=home + "/local/gmsh-2.8.5-Linux/bin/gmsh"
#cts.gmsh_path="gmsh"

#cts.d_frac_array = [0.1*pow(0.5, n) for n in range(-2, 5)]
#cts.h_array = [0.01*pow(0.5, n) for n in range(-1, 4)]
cts.h1d_array=[0.2, 0.1, 0.05, 0.02, 0.01, 0.005, 0.0025]
cts.h2d_array=[ 0.05, 0.02, 0.01] #, 0.005] 
cts.d_frac_array = [0.25, 0.1, 0.05, 0.025, 0.01, 0.005, 0.0025]

cts.pool = pbs_pool({'mpiexec' : cts.mpiexec })
#cts.pool = local_pool({})


#################################################################
"""
attributes of case:
id_frac
d_frac
flow123d_finished
prefix
ih
h
workdir
file_mesh
file_con
file_output
"""

def make_h_cases(prefix, case_common, h_array):
    # make cases
    case_list=[]
    for ih, h in enumerate(h_array):
        #if h > case_common.d_frac:
        #    continue
        case=copy.copy(case_common)

        case.prefix = prefix
        case.ih=ih
        case.h=h
        subdir=prefix + "_h_" + str(h) + "_d_" + str(case.d_frac)
        case.workdir= os.path.join( os.getcwd(), subdir )
        case_list.append( case )

    return case_list

def main():

    # create and poll cases
    cases_2d = []
    cases_1d = []
    reference_cases = []
    for id_frac, d_frac in enumerate(cts.d_frac_array):
        cases_common=Bunch(id_frac=id_frac, d_frac=d_frac, flow123d_finished=False)
        cases_2d_tmp = make_h_cases("2d2d", cases_common, cts.h2d_array)
        reference_cases.append( cases_2d_tmp.pop() )
        cases_2d += cases_2d_tmp
        cases_1d_tmp = make_h_cases("2d1d", cases_common, cts.h1d_array)
        for c in  cases_1d_tmp:
            c.reference_case = reference_cases[-1]
        cases_1d += cases_1d_tmp

    for cc in [reference_cases, cases_1d, cases_2d]:
        pool_cases(cc)    
    
    # wait for completition of cases
    norm_list=[]
    finished_cases=[]
    while (cts.pool.pbs_jobs or finished_cases):
        #print cts.pool.pbs_jobs
        #print finished_cases
        time.sleep(5)        

        finished_jobs = cts.pool.get_finished_jobs()
        for job in finished_jobs:
            case = job['case']
            finished_cases.append( case )
        new_cases=[]
        for case in finished_cases:
            if not postprocess_finished(case):
                new_cases.append(case)
        for job in cts.pool.pbs_jobs:
            print job['case'].workdir
        finished_cases=new_cases

    # make tebles


if __name__ == "__main__":
   main()
