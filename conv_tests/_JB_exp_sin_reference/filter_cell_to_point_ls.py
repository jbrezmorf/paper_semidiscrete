#sys.path.append('/usr/lib/pymodules/python2.7')

import scipy
import scipy.sparse.linalg.isolve.lsmr as lsmr
import scipy.sparse.linalg.isolve.lsqr as lsqr
import numpy as np
from scipy.sparse import csr_matrix
import paraview.numpy_support as ns


def lsq(A, b, x0, btol=1e-6):
    r0 = b - A * x0
    atol=btol*np.linalg.norm(r0)
    scaled_btol = btol*np.linalg.norm(b)/np.linalg.norm(r0)
    result=lsqr(A, r0, damp=10, iter_lim=100, show=True, atol=atol, btol=scaled_btol)
    return (x0 + result[0])


pdi = self.GetPolyDataInput()
pdo = self.GetOutput()


cell_locations=ns.vtk_to_numpy(pdi.GetCellLocationsArray())
cell_node_ids_vtk=np.copy(ns.vtk_to_numpy(pdi.GetCells().GetData()))
n_elements=pdi.GetNumberOfCells()
n_nodes=pdi.GetNumberOfPoints()
assert(n_elements == len(cell_locations))

# sparse matrix for PointData -> CellData interpolation (averages of nodal values)
row_starts = np.append(cell_locations, len(cell_node_ids_vtk))
nodes_per_cell_vtk = row_starts[1:] - row_starts[0:-1]

# remove cell sizes
nodes_per_cell=nodes_per_cell_vtk - 1
row_starts = np.cumsum(np.insert(nodes_per_cell,0,0))
cell_node_ids_vtk[cell_locations]=-1
cell_node_ids=cell_node_ids_vtk[cell_node_ids_vtk!=-1]
 

values = 1.0/repeat(nodes_per_cell, nodes_per_cell)

#print len(cell_node_ids_new), len(values), np.sum(nodes_per_cell_new), n_nodes, n_elements 
assert( np.sum(nodes_per_cell) == len(cell_node_ids) )
#assert( 1==0 )
interpolation_matrix = csr_matrix((values, cell_node_ids, row_starts), shape=(n_elements, n_nodes))

# prepare clean deep copy
#pdo.DeepCopy(pdi)
#cell_data=pdo.GetCellData()
#for i_array in range(cell_data.GetNumberOfArrays()):
#    cell_data.RemoveArray(i_array)
#point_data=pdo.GetPointData()
#for i_array in range(point_data.GetNumberOfArrays()):
#    point_data.RemoveArray(i_array)

pdi_data=pdi.GetCellData()
# for every data field compute least square approx. inverse
for i_array in range(pdi_data.GetNumberOfArrays()):
    
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
        print vtk_array.GetName(), i_comp
        # solution guess
        node_sum=np.zeros((n_nodes))
        node_counts=np.zeros((n_nodes))
        to_add=np.repeat(array[:,i_comp], nodes_per_cell)
        for i in range(len(cell_node_ids)):
            node_sum[cell_node_ids[i]]+=to_add[i]
            node_counts[cell_node_ids[i]]+=1
            
        #node_sum[cell_node_ids]=np.repeat(array[:,i_comp], nodes_per_cell)        
        #node_counts[cell_node_ids]=np.ones((len(cell_node_ids)))
        node_vals_0=node_sum/node_counts
        #print array[:,i_comp]
        #print node_vals_0
        # solve overdetermined system by least squares
        #new_array[:,i_comp]=node_vals_0
        new_array[:,i_comp]=lsq(interpolation_matrix, array[:,i_comp], node_vals_0)
            
    new_vtk_array=ns.numpy_to_vtk(new_array, deep=1)
    new_vtk_array.SetName(vtk_array.GetName())
    pdo.GetPointData().AddArray(new_vtk_array)


