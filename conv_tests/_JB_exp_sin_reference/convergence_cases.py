import os
import subprocess
import postprocess
import sys
import json


"""
File collecting various at least slightly general functions and
classes for convergence tests. All test specific and environment specific
settings should be made in run_all.py
"""

class ConvergenceTestSetting:
    """
    Class with setting.
    """

    #
    h1d_array=[]        # mesh steps used for 2d2d cases
    h2d_array=[]        # mesh stpes used for 2d1d cases
    d_frac_array = []   # fracture aperture

    con_2d="flow_2d2d.con"  # main CON file for 2d2d cases
    con_1d="flow_2d1d.con"  # main CON file for 2d1d cases

    flow_path=""            # flow binary path
    modules_file=""         # file to set modules (PBS pool)
    mpiexec="mpiexec"       # mpiexec binary
    gmsh_path="gmsh"        # gmsh binary
    pool=None


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


def up_to_date( _out, _in):
    """
    Return true if file _out is newer then file _in.
    """
    if  ( os.path.isfile(_out)
          and os.path.getmtime(_out) > os.path.getmtime(_in)
          ) : return True
    else : return False


def run_gmsh(geo_file):
    path, ext = os.path.splitext(geo_file)
    if ext == ".geo":
        mesh_file=path+".msh"
    else:
        mesh_file=geo_file+".msh"

    if not up_to_date(mesh_file, geo_file):
        print 'gmsh:', ConvergenceTestSetting.gmsh_path
        print 'geo: ', geo_file
        assert( os.path.isfile(ConvergenceTestSetting.gmsh_path) )
        subprocess.call([ConvergenceTestSetting.gmsh_path, geo_file, "-2", "-algo", "front2d", "-o", mesh_file])
    return mesh_file


def file_substitute(file_in, subst_list, file_out=""):
    """
    Replace parameters in file template "filename_in".
    subst_list contain tuples: ( string_to_replace, value)
    In the name of the new file is not given explicitely through file_out,
    use basename of file_in.
    """
    if not file_out:
        file_out=os.path.join(os.getcwd(), os.path.basename(file_in))
    if not up_to_date(file_out, file_in):
        with open(file_in, 'r') as in_file:
            content = in_file.read()
            for (pattern, value) in subst_list:
                content=content.replace(pattern, str(value))
        with open(file_out, 'w') as out_file:
            out_file.write(content)
    return file_out


def get_flow_job(case):
    (out_dir,  basename)=os.path.split(case.file_output)
    job= {'executable' : ConvergenceTestSetting.flow_path,
          'modules_file' : ConvergenceTestSetting.modules_file,
          'arguments' : ["-s", case.file_con, "-o", out_dir ],
          'work_dir' : os.getcwd()
         }
    if up_to_date(case.file_output_vtk, case.file_con) \
            and up_to_date(case.file_output_vtk, case.file_mesh):
        job['status']='C'
    return job


def msh_n_elements(file_name):
    """
    Return number of elements of a mesh in GMSH format.
    """
    with open(file_name) as f:
        for line in f:
            if "$Elements" in line:
                str_el = next(f)
                try:
                    return int(str_el)
                except ValueError:
                    print "Not a number:", str_el


class Bunch(dict):
    """
    Base class for collection any data together.
    """
    def __init__(self, **kw):
        dict.__init__(self, kw)
        self.__dict__ = self

    def __getstate__(self):
        return self

    def __setstate__(self, state):
        self.update(state)
        self.__dict__ = self



def pool_cases(cases):
    for case in cases:
        assert(isinstance(case, Bunch))
        with Chdir(case.workdir):
            print case.workdir
            file_geo_template = os.path.join("..", "mesh_" + case.prefix + ".geo")
            h1d=case.h/11
            file_geo = file_substitute(
              file_geo_template, 
              [ ("$d$", case.d_frac), 
                ("$h$", case.h),
                ("$h1d$", h1d)
                ])
            case.file_mesh = run_gmsh(file_geo)
            file_con_template=os.path.join("..", ConvergenceTestSetting.con_base + "_" + case.prefix + ".con")
            case.file_con = file_substitute(file_con_template, [ ("$rozevreni$", case.d_frac) ])
            case.file_output = os.path.join(case.workdir, "output_" + case.prefix, "flow_"+case.prefix+".pvd")
            case.file_output_vtk = os.path.join(case.workdir, "output_" + case.prefix, "flow_"+case.prefix, "flow_"+case.prefix+"-000000.vtu")

            if hasattr(case, 'reference_case'):
                file_resample = os.path.join("..", "filter_resample_2d1d.py")
                n_avg_pt=int(max(9, 3*int(8*case.d_frac/case.reference_case.h)))
                file_substitute(
                    file_resample,
                    [ ("$rozevreni$", case.d_frac),
                      ("$average_points_x$", n_avg_pt )
                      ])
                print "avg pt: ", n_avg_pt, case.workdir   

            file_resample = os.path.join("..", "filter_resample_2d1d.py")
            file_substitute(
                file_resample,
                [ ("$rozevreni$", case.d_frac),
                  ("$average_points_x$", int(max(6, 2*int(case.d_frac/case.h))) )
                  ])

            n_ele = msh_n_elements(case.file_mesh)
            n_proc=max(1, int(round(n_ele / 100000)))
            print "N elements:", n_ele, "N proc:", n_proc
            
            mem_limit=4000
            if n_ele> 1e6 : mem_limit = 8000
            if n_ele> 4e6 : mem_limit = 16000
            if n_ele>8e6 : 
                print "Mesh too big: ", n_ele
                sys.exit()
            job_common={ 'wall_time' : '1:50:00',
                         'n_proc' : n_proc,
                         'memory' : mem_limit,
                         'case' : case
                         }
            job=get_flow_job(case)
            job.update(job_common)            
            ConvergenceTestSetting.pool.start_job(job)
            print job['case'].workdir






def postprocess_finished(case):
    file_norms=os.path.join(case.workdir, "norms_raw.json")
    if hasattr(case, 'reference_case'):
        reference_case=case.reference_case
        if not reference_case.flow123d_finished:
            return False
    else:
        reference_case=None

    print case.workdir	
    with Chdir(case.workdir) as dir:
        print "postprocess in ", case.workdir
        norms=[]
        #try:
        if 1:
            if reference_case:
                ref_file_norms=os.path.join(reference_case.workdir, "norms_raw.json")
                # is 2d1d case
                if not up_to_date(file_norms, case.file_output_vtk) or \
                        not up_to_date(file_norms, reference_case.file_output_vtk) or \
                        not up_to_date(file_norms, ref_file_norms):
                    norms=postprocess.error_2d1d(case.file_output, reference_case.file_output)
                    norms.update(postprocess.exact_2d1d(case.file_output, "2d1d_", case.d_frac))
                    norms.update(postprocess.exact_2d1d("./resampled_data.vtk", "2d2d_", case.d_frac))
                    with open(ref_file_norms, "r") as f:
                        ref_norms=json.load(f)
                        dxdx_Linf=ref_norms[1]["dx_dx_p_fracture_Linf"]
                        dxdx_L2=ref_norms[1]["dx_dx_p_fracture_L2"]
                        p_2d2d_L2=ref_norms[1]["p_L2"]
                    norms.update({
                        'p_H1_1d_over_dxx_Linf' : norms['p_12_diff_H1_1d'] / dxdx_Linf,
                        'p_H1_2d_over_dxx_Linf' : norms['p_12_diff_H1_2d'] / dxdx_Linf,
                        'p_H1_1d_over_dxx_L2' : norms['p_12_diff_H1_1d'] / dxdx_L2,
                        'p_H1_2d_over_dxx_L2' : norms['p_12_diff_H1_2d'] / dxdx_L2,
                        'p_L2_1d_over_L2' : norms['p_12_diff_L2_1d'] / p_2d2d_L2,
                        'p_L2_2d_over_L2' : norms['p_12_diff_L2_2d'] / p_2d2d_L2
                    })

            else:
                # is 2d2d case
                if not up_to_date(file_norms, case.file_output_vtk):
                    norms=postprocess.dxdx_2d2d(case.file_output)
                    norms.update(postprocess.exact_2d2d(case.file_output))


        #except:
        #    print "Postprocess exception:"
        #    print sys.exc_info()

        if norms:
            case_result = ( case,  norms )
            with open(file_norms, "wb") as f:
                json.dump(case_result, f)

    case.flow123d_finished=True
    return True


def main():
    pass

if __name__ == "__main__":
   main()
