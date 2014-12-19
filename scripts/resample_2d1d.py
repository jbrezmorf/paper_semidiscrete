#
# This programmable filter behaves similarly as the ResampleWithDataset filter.
#
# Two inputs have to be provides, the first one (the geometry input) is supposed to 
# be a 2d-1d mesh with 1d fracture at X=0 line. The second (the data input  should be
# a 2d-2d mesh. 
# 
# Filter assumes vtkUnstructuredGrid output (same as the input.  Filter interpolates all data sets from 
# the data input to the cell data on the geometry input as follows:
# For every dataset in data input:
#   - dataset is evaluated in barycenters on 2d cells of the geometry input
#     which provides the cell data on these cells
#   - for every 1d cell with end points Y0, Y1 of the geometry input, we construct a regular grid of 
#     AVERAGE_POINTS x AVERAGE_POINTS points covering a rectangle (LEFT_SHIFT, RIGHT_SHIFT)x(Y0,Y1)
#   - dataset is evaluated in the points of the grid and we determine arithmetic mean over the grid 
#     corresponding to one 1D element; teh mean is set as the cell value of the 1D element
#


import math
import paraview.simple
import numpy as np
import paraview.numpy_support as ns
from vtk.numpy_interface import dataset_adapter as dsa

from ctypes import c_int
import vtk

# Script parameters ==================================

# 2d cells of the geometry input are shifted by LEFT_SHIFT (elements with barycenters with negative X coordinate 
# or RIGHT_SHIFT. Both shifts are positive in positive X direction, i.e. they are simply added to 
# the vertices of the cells.
LEFT_SHIFT = 0
RIGHT_SHIFT = 0.2

# number of points in single direction used to average values over rectangles corresponding to 1d elements
AVERAGE_POINTS=4

#=============================================
# Internal parameters
VTK_LINE=3
VTK_TRIANGLE=5


'''
Returns VTK array as a copy of numpy array and set a given name.
'''
def make_vtk_array(numpy_array, name):
    vtk_array=ns.numpy_to_vtk(numpy_array, deep=1)
    vtk_array.SetName(name)
    return vtk_array


def assert_eq(a,b):
    assert (a==b), "Non-equal values: '{0}'!='{1}'.".format(a,b)


#def make_probe(geometry_input, geom_2d_id, geom_1d_id):


"""
In geom assumes a 2D mesh in XY plane with compatible 1D fracture on Y axis.
"""
def resample_to_2d_1d(pdi, pdo, geom):

    # 
    geom_types=ns.vtk_to_numpy(geom.GetCellTypesArray())    
    geom_locations=ns.vtk_to_numpy(geom.GetCellLocationsArray())
    geom_2d_id=np.where(geom_types==VTK_TRIANGLE)[0]
    n_2d_cells=geom_2d_id.size
    #print geom_2d_id
    geom_2d_locations=geom_locations[geom_2d_id]

    geom_1d_id=np.where(geom_types==VTK_LINE)[0]
    n_1d_cells=geom_1d_id.size
    #print geom_1d_id
    geom_1d_locations=geom_locations[geom_1d_id]
    
    # should check that there are both 2d and 1d elements other
    # similarly we should check that there are only triangles in the pdi
    
    # create a sampling dataset
    aux_dataset=vtk.vtkUnstructuredGrid()
    # compute centroids
    input_copy = geom.NewInstance()
    input_copy.UnRegister(None)
    input_copy.ShallowCopy(geom)
    geom_centers=vtk.vtkCellCenters()
    geom_centers.SetInputData(geom)
    geom_centers.Update()
    output=geom_centers.GetOutput()
    barycenters=ns.vtk_to_numpy(output.GetPoints().GetData()).reshape(-1,3)
    barycenters_2d=barycenters[geom_2d_id]
    #print barycenters_2d
    # shift right half of points
    barycenters_2d[:,0]=np.where(barycenters_2d[:,0]<0, 
                                 barycenters_2d[:,0]+LEFT_SHIFT, 
                                 barycenters_2d[:,0]+RIGHT_SHIFT)
    
    
    # compute 1d avarage points
    cell_data=ns.vtk_to_numpy(geom.GetCells().GetData())
    grid = np.meshgrid( [0,1,2], geom_1d_locations )
    grid = map(np.ravel, grid)
    cell_data_selection=grid[0]+grid[1]
    array_of_1d_cells=(cell_data[cell_data_selection])
    assert(len(array_of_1d_cells)>0)
    
    geom_points_y=ns.vtk_to_numpy(geom.GetPoints().GetData())[:,1]
    x_points=np.array((0))
    y_points=np.array((0))
    # reference grid
    x=np.linspace(LEFT_SHIFT,RIGHT_SHIFT,AVERAGE_POINTS)
    y=np.linspace(0,1,AVERAGE_POINTS)
    ref_x, ref_y=map(np.ravel, np.meshgrid(x,y))
    assert( np.all(array_of_1d_cells[0::3]==2) )
    p0=geom_points_y[array_of_1d_cells[1::3]]
    p1=geom_points_y[array_of_1d_cells[2::3]]

    x_points=np.tile(ref_x, geom_1d_id.size)

    yy,y0=np.meshgrid(ref_y,p0)
    yy,y1=np.meshgrid(ref_y,p1)
    y_points=(y0*yy+y1*(1-yy)).ravel()
    assert(x_points.size==y_points.size)
    z_points=np.zeros(len(x_points))
    points_1d=np.hstack(( x_points.reshape((-1,1)),
                          y_points.reshape((-1,1)),
                          z_points.reshape((-1,1))
                          ))    
    #print points_1d
    
    
    all_points=append(barycenters_2d, points_1d)
    all_points.shape=(-1,3)
    
    # make a probe dataset
    points=vtk.vtkPoints()
    points.SetData(make_vtk_array(all_points, "points"))
    point_set=vtk.vtkUnstructuredGrid()
    point_set.SetPoints(points)
    
    probe=vtk.vtkProbeFilter()
    probe.SetSourceData(pdi)
    probe.SetInputData(point_set)
    probe.Update()
    out=probe.GetOutput()
    probe_data=out.GetPointData()
    
    # reconstruct element arrays 
    pdo.DeepCopy(geometry)   
    cell_data=pdo.GetCellData()
    for i_array in range(probe_data.GetNumberOfArrays()):
        
        # make interpolation array
        vtk_array=probe_data.GetArray(i_array)
        array_name=vtk_array.GetName()
        
        n_components=vtk_array.GetNumberOfComponents()
        n_tuples=vtk_array.GetNumberOfTuples()
        array=ns.vtk_to_numpy(vtk_array)
        array.shape=(n_tuples,n_components)
        
        new_array=np.zeros((pdo.GetNumberOfCells(),n_components), dtype=array.dtype)
        new_array[geom_2d_id,:]=array[0:n_2d_cells,:]
        
        array_1d=array[n_2d_cells:,:].reshape(n_1d_cells, AVERAGE_POINTS*AVERAGE_POINTS, n_components)
        new_array[geom_1d_id,:]=np.average(array_1d, axis=1)
        
        new_vtk_array=ns.numpy_to_vtk(new_array, deep=1)
        cell_data.AddArray(
            make_vtk_array(new_array, "interpol_"+vtk_array.GetName())
            )
        
        # compute difference array
        vtk_geometry_array=pdo.GetCellData().GetArray(array_name)
        if vtk_geometry_array:
            assert_eq(vtk_geometry_array.GetNumberOfComponents(), new_array.shape[1])
            assert_eq(vtk_geometry_array.GetNumberOfTuples(), new_array.shape[0])
            
            geometry_array=ns.vtk_to_numpy(vtk_geometry_array)
            geometry_array.shape=new_array.shape
            difference=geometry_array - new_array
            cell_data.AddArray(
              make_vtk_array(difference, "diff_"+vtk_array.GetName())
              )
            
    # add array with cell IDs    
    #cell_data.AddArray(make_vtk_array(np.arange(n_2d_cells+n_1d_cells), "ids"))
    
################################################
# The filter with appropriate predicate.

if self.GetNumberOfInputConnections(0) < 2:
    print "Error: Filter expects two inputs."
else:
    geometry=self.GetInputDataObject(0,0)
    #print "Geometry(1d2d):", geometry
    data=self.GetInputDataObject(0,1)
    #print "Data(2d2d):", data

    pdo =self.GetOutput()
    #pdo.DeepCopy(geometry)
    resample_to_2d_1d(data, pdo, geometry)
