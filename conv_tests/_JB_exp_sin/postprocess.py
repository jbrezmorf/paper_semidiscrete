#from paraview.simple import *
import paraview.benchmark
import math
from paraview import servermanager
from paraview import simple

def programmable_filter(data_in, script_file, Parameters={}, CopyArrays=0):
        with open(script_file, "r") as resample_script_file:
            script=resample_script_file.read()
            script="filter_parameters="+str(Parameters)+"\n"+script
            pf=servermanager.filters.ProgrammableFilter(Input=data_in, CopyArrays=CopyArrays, Script=script)
            return pf

def fetch_integrate_variables(data_in):
    iv = programmable_filter(data_in, "../filter_iv.py")
    iv.UpdatePipeline()
    iv_output=paraview.servermanager.Fetch(iv)
    return (iv, iv_output)

def integrate(data_in, array_name):    
    array=data_in.GetCellData().GetArray(array_name)
    return array.GetTuple(0)[0]

def inf_norm(data_in, array_name):    
    array_range=data_in.CellData.GetArray(array_name).GetRange()
    return max( map(abs, array_range) )



def h1_norm(data_in, field_diff, diff_field_diff, base_out):
    l2_norm=math.sqrt(integrate(data_in, field_diff))
    diff_l2_norm=math.sqrt(integrate(data_in, diff_field_diff))
    return { base_out + "_H1" : math.sqrt(l2_norm*l2_norm + diff_l2_norm*diff_l2_norm),
             base_out + "_L2" : l2_norm,
             base_out + "_grad_L2" : diff_l2_norm }

def python_difference(data_a, array_a, data_b, array_b, result_name, component=-1):
    """
    Computes square of a difference of two arrays of two possibly different datasets.
    Result copy arrays form the first dataset.
    """
    array_a_obj=data_a.CellData.GetArray(array_a)
    if component>=0:
        comp_expr="[:,"+str(component)+"]"
    else:
        comp_expr=""

    def array_expr(i, array, comp):
        return "inputs[" + str(i) + "].CellData['" + array + "']"+ comp
      
    diff_expr="(" + array_expr(0, array_a, comp_expr) + "-" + array_expr(1, array_b, comp_expr) + ")"

    if component==-1 and array_a_obj.GetNumberOfComponents() > 1:
        expr="dot(" + diff_expr + ", " +diff_expr + ")"
    else:
        expr=diff_expr + "*" + diff_expr
        
    print expr
    return servermanager.filters.PythonCalculator(Input=[data_a, data_b],
                            Expression=expr,
                            ArrayAssociation='Cell Data',
                            ArrayName=result_name)


def postprocess(output_pvd_2d1d, output_pvd_2d2d):
  
    servermanager.Connect()

    print "connected"
    data_reader_1d = servermanager.sources.PVDReader(FileName=output_pvd_2d1d)
    data_reader_2d = servermanager.sources.PVDReader(FileName=output_pvd_2d2d)


    #iv=paraview.simple.IntegrateVariables(data_reader_2d)
  
    resampled_2d_data=programmable_filter([data_reader_1d, data_reader_2d], "./filter_resample_2d1d.py")
    writer=servermanager.writers.DataSetWriter(FileName="./resampled_data.vtk", Input=resampled_2d_data)
    writer.UpdatePipeline()

    p_diff_data=python_difference(resampled_2d_data, "pressure_p0",
                                  data_reader_1d, "pressure_p0", "diff2_pressure_p0" )
    p_diff_data.UpdatePipeline()
    both_diff_data = python_difference(p_diff_data, "velocity_p0", data_reader_1d, "velocity_p0", "diff2_velocity_p0" )
    both_diff_data.UpdatePipeline()


    diff_data_1d=programmable_filter( [both_diff_data], "../filter_submesh_by_dimension.py",
                             Parameters={"dimension_to_extract" : 1})
    data_reader_1d_only=programmable_filter( [data_reader_1d], "../filter_submesh_by_dimension.py",
                             Parameters={"dimension_to_extract" : 1})
    
    diff_data_1d=python_difference(diff_data_1d, "velocity_p0",
                                   data_reader_1d_only, "velocity_p0", "diff2_velocity_Y", component=1 )
    
    diff_data_2d=programmable_filter( [both_diff_data], "../filter_submesh_by_dimension.py",
                             Parameters={"dimension_to_extract" : 2})
    iv_1d, iv_arrays_1d = fetch_integrate_variables(diff_data_1d)
    iv_2d, iv_arrays_2d = fetch_integrate_variables(diff_data_2d)

    writer=servermanager.writers.DataSetWriter(FileName="./resampled_data_1d.vtk", Input=diff_data_1d)
    writer.UpdatePipeline()
    writer=servermanager.writers.DataSetWriter(FileName="./resampled_data_2d.vtk", Input=diff_data_2d)
    writer.UpdatePipeline()

    norms={}

    norms.update( h1_norm(iv_arrays_1d, "diff2_pressure_p0", "diff2_velocity_Y", "p_12_diff_1d") )
    norms.update( h1_norm(iv_arrays_2d, "diff2_pressure_p0", "diff2_velocity_p0", "p_12_diff_2d") )

    print "resampled"
    #########################################################################
    # Estimate norms of second X derivative of the pressure on the fracture
    dx_p_data=servermanager.filters.PythonCalculator(Input=data_reader_2d,
                            Expression="(-1)*inputs[0].CellData['velocity_p0'][:,0]",
                            ArrayAssociation='Cell Data',
                            ArrayName="dx_p")
    grad_dx_p_data=servermanager.filters.GradientOfUnstructuredDataSet(Input=dx_p_data,
                            ScalarArray=['CELLS',"dx_p"],
                            ResultArrayName="grad_dx_p")
    ddxx_p_data=servermanager.filters.PythonCalculator(Input=grad_dx_p_data,
                            Expression="inputs[0].CellData['grad_dx_p'][:,0]",
                            ArrayAssociation='Cell Data',
                            ArrayName="ddxx_p")
    ddxx_p_data=servermanager.filters.PythonCalculator(Input=ddxx_p_data,
                            Expression="inputs[0].CellData['ddxx_p']*inputs[0].CellData['ddxx_p']",
                            ArrayAssociation='Cell Data',
                            ArrayName="ddxx_p_2")
    ddxx_p_on_2d_fracture = programmable_filter([ddxx_p_data], "../filter_submesh_by_region.py",
                             Parameters={"region_id_to_extract" : 2})
    iv_ddxx, iv_ddxx_arrays = fetch_integrate_variables(ddxx_p_on_2d_fracture)

    writer=servermanager.writers.DataSetWriter(FileName="./ddxx_p.vtk", Input=ddxx_p_on_2d_fracture)
    writer.UpdatePipeline()

    norms["dx_dx_p_fracture_L2"] = math.sqrt(integrate(iv_ddxx_arrays, "ddxx_p_2"))
    norms["dx_dx_p_fracture_Linf"] = inf_norm(ddxx_p_on_2d_fracture, "ddxx_p")

    print "ddxx"
    #########################################################################
    # Diferences on 2D against exact solution
    coords_data = servermanager.filters.Calculator(Input=ddxx_p_data,
                            Function="coords",
                            ResultArrayName="coords")
    cell_coords_data = servermanager.filters.PointDatatoCellData(Input=coords_data)
    pressure_exact  = servermanager.filters.Calculator(Input=cell_coords_data,
                            Function="exp(coords_X)*sin(coords_Y)",
                            ResultArrayName="exact_pressure",
                            AttributeMode="Cell Data")
    """
    ddxx_pressure_exact  = Calculator(Input=pressure_exact,
                            Function="exp(coord_X)*sin(coord_Y)",
                            ResultArrayName="exact_grad_pressure",
                            AttributeMode="Cell Data")
    """



    p_diff_data=python_difference(pressure_exact, "pressure_p0",
                                  pressure_exact, "exact_pressure", "diff2_pressure_exact" )
    p_diff_data.UpdatePipeline()
    all_diff_data=python_difference(p_diff_data, "ddxx_p",
                                  p_diff_data, "exact_pressure", "diff2_ddxx_p_exact" )
    all_diff_data=servermanager.filters.PythonCalculator(Input=all_diff_data,
                            Expression="sqrt(inputs[0].CellData['diff2_ddxx_p_exact'])",
                            ArrayAssociation='Cell Data',
                            ArrayName="diff_ddxx_p_exact")
    all_diff_fracture = programmable_filter([all_diff_data], "../filter_submesh_by_region.py",
                             Parameters={"region_id_to_extract" : 2})

    iv_diff, iv_diff_arrays = fetch_integrate_variables(all_diff_fracture)

    writer=servermanager.writers.DataSetWriter(FileName="./exact_calculations.vtk", Input=all_diff_fracture)
    writer.UpdatePipeline()

    norms["p_diff_exact_L2"] = math.sqrt(integrate(iv_diff_arrays, "diff2_pressure_exact"))
    norms["dx_dx_p_diff_exact_L2"]=math.sqrt(integrate(iv_diff_arrays, "diff2_ddxx_p_exact"))
    norms["dx_dx_p_diff_exact_Linf"]=inf_norm(all_diff_fracture, "diff_ddxx_p_exact")
    
    print "exact"
    
    servermanager.Disconnect()
    print paraview.benchmark.get_memuse()
    return norms



if __name__ == "__main__":
   print postprocess("./output_1d/flow_2d1d.pvd", "./output_2d/flow_2d2d.pvd")