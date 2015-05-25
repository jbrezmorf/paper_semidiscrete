sys.path.append('/usr/lib/pymodules/python2.7')

import scipy
import scipy.sparse.linalg.lsmr as lsmr
import scipy.sparse.linalg.lsqr as lsqr
import numpy as np
from scipy.sparse import csr_matrix

def lsq(A, b, x0, btol=1e-6):
    r0 = b - A * x0
    scaled_btol = btol*norm(b)/norm(r0)
    result=lsqr(A, r0, iter_lim=100, show=True, btol=scaled_btol)
    return (x0 + result[0])


pdi = self.GetPolyDataInput()
pdo = self.GetOutput()


#cell_types=ns.vtk_to_numpy(pdi.GetCellTypesArray())    
cell_locations=ns.vtk_to_numpy(pdi.GetCellLocationsArray())
cell_node_ids=ns.vtk_to_numpy(pdi.GetCells().GetData())
n_elements=pdi.GetNumberOfCells()
n_nodes=pdi.GetNumberOfPoints()
assert(n_elements == len(cell_locations))

# sparse matrix for PointData -> CellData interpolation (averages of nodal values)
row_starts = cell_locations.append(len(cell_node_ids))
nodes_per_cell = row_starts[1:-1] - row_starts[0:-2] 
cols = cell_node_ids
values = 1.0/nodes_per_cell
interpolation_matrix = csr_matrix((values, cols, row_starts), shape=(3, 3))

# prepare clean deep copy
pdo.DeepCopy(pdi)
cell_data=pdo.GetCellData()
for i_array in range(cell_data.GetNumberOfArrays()):
    cell_data.RemoveArray(i_array)
point_data=pdo.GetPointData()
for i_array in range(point_data.GetNumberOfArrays()):
    point_data.RemoveArray(i_array)

# for every data field compute least square approx. inverse
for i_array in range(pdi.GetNumberOfArrays()):
    
    vtk_array=pdi_data.GetArray(i_array)
    #print i_array, vtk_array.GetName()
    n_components=vtk_array.GetNumberOfComponents()
    n_tuples=vtk_array.GetNumberOfTuples()
    assert(n_tuples == n_elements)
    array=ns.vtk_to_numpy(vtk_array)
    array.shape=(n_tuples,n_components)
    #print array
    
    new_array=np.empty((n_nodes,n_components), dtype=array.dtype)
    for i_comp in range(n_components):
        # solution guess
        node_sum_0=np.zeros((n_elements))
        node_sum[cell_node_ids]=array[:,i_comp]
        node_counts=np.zeros((n_elements))
        node_counts[cell_node_ids]=np.ones((n_elements))
        node_vals_0=node_sum/node_counts
        
        # solve overdetermined system by least squares
        new_array[:,i_comp]=lsq(interpolation_matrix, array[:,i_comp], node_vals_0[:,i_comp])
            
    new_vtk_array=ns.numpy_to_vtk(new_array, deep=1)
    new_vtk_array.SetName(vtk_array.GetName())
    cell_data.AddArray(new_vtk_array)


