#
# This programmable filter behaves similarly as the ResampleWithDataset filter.
# The SourceName variable should be set to name of the entry of the pipeline that describes
# geometry of the result, we assume 2d-1d mesh with single fracture running in direction of the Y axis.
# The input of the filter is a dataset used to sample values.
#
# The script resample values in barycenters of 2d elements and computes an average over a rectangle
# corresponding to every 1d element. 

import numpy as np
import paraview.numpy_support as ns
import vtk

# shift of 2d elements in 2d-1d mesh so that 2d part match corresponding part in simply 2d mesh
X_FR=1.0
X_SHIFT_LEFT = $rozevreni$/2
X_SHIFT_RIGHT = $rozevreni$/2
# number of points in every direction used to average values over rectagles corresponding to 1d elements
AVERAGE_POINTS_X=int($average_points_x$)
AVERAGE_POINTS_Y=5


VTK_LINE=3
VTK_TRIANGLE=5


"""
In geom assumes a 2D mesh in XY plane with compatible 1D fracture on Y axis.
"""
def resample_to_2d_1d(pdi, pdi_frac, pdo, geom):

    # 
    geom_types=ns.vtk_to_numpy(geom.GetCellTypesArray())    
    geom_locations=ns.vtk_to_numpy(geom.GetCellLocationsArray())
    geom_2d_id=np.where(geom_types==VTK_TRIANGLE)[0]
    n_2d_cells=geom_2d_id.size
    #print geom_2d_id
    #geom_2d_locations=geom_locations[geom_2d_id]

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
    barycenters_2d[:,0]=np.where(barycenters_2d[:,0]<X_FR, barycenters_2d[:,0]-X_SHIFT_LEFT, barycenters_2d[:,0]+X_SHIFT_RIGHT)
    
    
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

    # trapezoid rule
    """
    def weights(N):
        return np.array([0.5] + (N-2)*[1.0] + [0.5])
    average_weights=np.outer( weights(AVERAGE_POINTS_X), weights(AVERAGE_POINTS_Y)).flatten()
    # reference grid
    x=np.linspace(-X_SHIFT_LEFT, X_SHIFT_RIGHT, AVERAGE_POINTS_X)
    y=np.linspace(0,1,AVERAGE_POINTS_Y)
    """
    
    def weights(N):
        # trapezoidal weights
        return np.array([0.5] + (N-2)*[1.0] + [0.5])
 
    # midpoint rule in both directions (avoid problems at boundary)
    average_weights=np.outer( np.ones(AVERAGE_POINTS_Y), np.ones(AVERAGE_POINTS_X) ).flatten()
    # reference grid
    N=float(AVERAGE_POINTS_X)
    dx=(X_SHIFT_RIGHT + X_SHIFT_LEFT)/N
    x=np.linspace(X_FR-X_SHIFT_LEFT+dx/2, X_FR+X_SHIFT_RIGHT-dx/2,N)
    N=float(AVERAGE_POINTS_Y)
    y=np.linspace(1/(2*N),1-1/(2*N),N)
    #print "weights: ", average_weights
    #print "y: ", y
    
    ref_x, ref_y=map(np.ravel, np.meshgrid(x,y))
    #print "y: ", ref_y
    #print "x: ", ref_x
    assert( np.all(array_of_1d_cells[0::3]==2) )
    p0=geom_points_y[array_of_1d_cells[1::3]]
    p1=geom_points_y[array_of_1d_cells[2::3]]
    x_points=np.tile(ref_x, geom_1d_id.size)

    
    yy,y0=np.meshgrid(ref_y,p0)
    yy,y1=np.meshgrid(ref_y,p1)
    y_points=(y0*yy+y1*(1-yy)).ravel()
    #print average_weights.size, x_points.size, y_points.size
    assert(x_points.size==y_points.size)
    assert(AVERAGE_POINTS_X*AVERAGE_POINTS_Y==average_weights.size)    
    z_points=np.zeros(len(x_points))
    points_1d=np.hstack(( x_points.reshape((-1,1)),
                          y_points.reshape((-1,1)),
                          z_points.reshape((-1,1))
                          ))    
    #print points_1d
    
    barycenters_2d.shape=(-1,3)
    points_1d.shape=(-1,3)
    #all_points=append(barycenters_2d, points_1d)
    #all_points.shape=(-1,3)
    
    # make a dataset

    # probe on fracture dataset
    points_f=vtk.vtkPoints()
    points_f.SetData(ns.numpy_to_vtk(points_1d, deep=1))
    point_set_f=vtk.vtkUnstructuredGrid()
    point_set_f.SetPoints(points_f)
    
    probe_f=vtk.vtkProbeFilter()
    probe_f.SetSourceData(pdi_frac)
    probe_f.SetInputData(point_set_f)
    probe_f.Update()
    out_f=probe_f.GetOutput()
    probe_data_f=out_f.GetPointData()
    
    # probe on continuum dataset
    points=vtk.vtkPoints()
    points.SetData(ns.numpy_to_vtk(barycenters_2d, deep=1))
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
    for i_array in range(cell_data.GetNumberOfArrays()):
        cell_data.RemoveArray(i_array)
    point_data=pdo.GetPointData()
    for i_array in range(point_data.GetNumberOfArrays()):
        point_data.RemoveArray(i_array)
    
    assert(probe_data.GetNumberOfArrays() == probe_data_f.GetNumberOfArrays() )
    for i_array in range(probe_data.GetNumberOfArrays()):
        vtk_array=probe_data.GetArray(i_array)
        array=ns.vtk_to_numpy(vtk_array)
        n_components=vtk_array.GetNumberOfComponents()
        n_tuples=vtk_array.GetNumberOfTuples()
        assert(n_tuples == n_2d_cells)
        array.shape=(n_tuples,n_components)        

        vtk_array_f=probe_data_f.GetArray(i_array)
        array_f=ns.vtk_to_numpy(vtk_array_f)
        n_components_f=vtk_array_f.GetNumberOfComponents()
        n_tuples_f=vtk_array_f.GetNumberOfTuples()        
        assert(n_components == n_components_f)
        assert( n_1d_cells*len(average_weights) == n_tuples_f)
        assert( array.dtype == array_f.dtype)
        array_f.shape=(n_1d_cells, len(average_weights), n_components)
        #print vtk_array.GetName()
        #print array_f.shape
        #print array_f
        
        new_array=np.zeros((pdo.GetNumberOfCells(),n_components), dtype=array.dtype)
        new_array[geom_2d_id,:]=array
        new_array[geom_1d_id,:]=np.average(array_f, weights=average_weights, axis=1)
        
        new_vtk_array=ns.numpy_to_vtk(new_array, deep=1)
        new_vtk_array.SetName(vtk_array.GetName())
        cell_data.AddArray(new_vtk_array)
    
    #ids=ns.numpy_to_vtk(np.arange(n_2d_cells+n_1d_cells), deep=1)
    #ids.SetName('ids')
    #cell_data.AddArray(ids)
    '''
    
    
    
    points=vtk.vtkPoints()
    n_points=all_points.shape[0]
    points.SetData(ns.numpy_to_vtk(all_points,deep=1))
    pdo.SetPoints(points)

    point_cells=vtk.vtkCellArray()   
    cell_list=np.empty(2*n_points, dtype='int64')
    cell_list[0::2]=np.ones(n_points)
    cell_list[1::2]=np.arange(n_points)
    point_cells.SetCells(n_points, ns.numpy_to_vtkIdTypeArray(cell_list,deep=1))
    pdo.SetVerts(point_cells)
    '''
    
################################################
# The filter with appropriate predicate.
pdo =self.GetOutput()

n_connections=self.GetNumberOfInputConnections(0)
geometry=self.GetInputDataObject(0,0)
#print "Geometry(1d2d):", geometry
data=self.GetInputDataObject(0,1)
#print "Data(2d2d):", data

if (n_connections == 3):
    data_fracture=self.GetInputDataObject(0,2)
    #pdo.DeepCopy(geometry)
    resample_to_2d_1d(data, data_fracture, pdo, geometry)
else:
    assert(n_connections == 2)
    #pdo.DeepCopy(geometry)
    resample_to_2d_1d(data, data, pdo, geometry)
