#
# Submesh module provides functions to extract a submesh consisting of cells of given ids.
# Both input and output dataset is UnstructuredGrid, all data are transfered to the new submesh.
#

import numpy as np
import paraview.numpy_support as ns
import vtk

# Taken from vtkCellType.h
VTK_EMPTY_CELL=0
VTK_VERTEX=1
VTK_LINE=3
VTK_TRIANGLE=5
VTK_TETRA=10

type_for_dimension = [ VTK_VERTEX, VTK_LINE, VTK_TRIANGLE, VTK_TETRA ]



# Predicates for cell selection. Resulting mesh will contain only cells
# for which predicate returns true.
def is_line(cell):
    return cell.GetCellType() == 3
  
def is_triangle(cell):
    return cell.GetCellType() == 5

def is_quad(cell):
    return cell.GetCellType() == 9  
    
def is_XY_plane(cell):
    points=cell.GetPoints()
    z_center=0.0
    for i_point in range(points.GetNumberOfPoints()):
        point=points.GetPoint(i_point)
        z_center+=point[2]
    z_center/=points.GetNumberOfPoints()
    return abs(z_center) < 1e-5


def submesh(pdi, pdo, cell_ids):
    """
    Extract cells from pdi with id in the list cell_ids.
    Set extracted dataset to pdo. 
    This implementation is slow. We can make it better using the numpy API.
    """

    # mark necessary points,
    n_points_old=pdi.GetNumberOfPoints()
    points_mask=[0]*n_points_old;
    cell_old_id=cell_ids
    for i in cell_old_id:
        cell=pdi.GetCell(i)
        for i_point in range(cell.GetNumberOfPoints()):
            points_mask[cell.GetPointId(i_point)]=1

    pdo.DeepCopy(pdi)
    pdo.Reset()
    # make point list, point_new_id
    new_points = vtk.vtkPoints()
    point_new_id = [-1]* n_points_old
    for i_old in range(n_points_old):
        if points_mask[i_old] :
            new_id=new_points.InsertNextPoint(pdi.GetPoint(i_old))
            point_new_id[i_old]=new_id
    pdo.SetPoints(new_points)
    
    # make cell list, substitute point id refs
    for i_old in cell_old_id :
        cell = pdi.GetCell(i_old)
        new_cell_point_ids = vtk.vtkIdList()
        for i_point in range(cell.GetNumberOfPoints()):
            new_cell_point_ids.InsertNextId( point_new_id[ cell.GetPointId(i_point) ] )
        pdo.InsertNextCell( cell.GetCellType(), new_cell_point_ids); # InsertNextCell( int  type, vtkIdList *  ptIds );"""

    # make cell data arrays
    for i in range(pdi.GetCellData().GetNumberOfArrays()) :
        oldArray=pdi.GetCellData().GetArray(i)
        newArray = vtk.vtkDoubleArray()
        newArray.SetName(oldArray.GetName())
        newArray.SetNumberOfComponents(oldArray.GetNumberOfComponents())
        newArray.SetNumberOfTuples(cell_old_id.__len__())
        
        i_new=0
        for i_old in cell_old_id :
            newArray.SetTupleValue(i_new, oldArray.GetTuple(i_old) )
            i_new+=1            
        pdo.GetCellData().AddArray(newArray)

    # make point data arrays
    for i in range(pdi.GetPointData().GetNumberOfArrays()) :
        oldArray=pdi.GetPointData().GetArray(i)
        newArray = vtk.vtkDoubleArray()
        newArray.SetName(oldArray.GetName())
        newArray.SetNumberOfComponents(oldArray.GetNumberOfComponents())
        newArray.SetNumberOfTuples( new_points.GetNumberOfPoints() )
        
        
        for i_old in range( len( point_new_id ) ) :
            i_new = point_new_id[ i_old ]
            if ( i_new != -1 ) :
                newArray.SetTupleValue(i_new, oldArray.GetTuple(i_old) )
        
        pdo.GetPointData().AddArray(newArray)



def submesh_numpy(pdi, pdo, cell_list):
    """
    Extract cells from pdi with id in the list cell_ids.
    Create output dataset in pdo.
    This implementation is stub but aiming to be faster then submesh().
    """

    pdo.DeepCopy(pdi)
    pdo.Reset()

    cell_data=pdi.GetCellData()    
    selection_ids=cell_list


    # get number of points for every cell
    cell_types=ns.vtk_to_numpy(pdi.GetCellTypesArray())
    cell_0d_ids=np.where(cell_types==VTK_VERTEX)[0]
    cell_1d_ids=np.where(cell_types==VTK_LINE)[0]
    cell_2d_ids=np.where(cell_types==VTK_TRIANGLE)[0]
    cell_3d_ids=np.where(cell_types==VTK_TETRA)[0]
    cell_sizes=np.zeros(len(cell_types), dtype=int)
    cell_sizes[cell_0d_ids]=1
    cell_sizes[cell_1d_ids]=2
    cell_sizes[cell_2d_ids]=3
    cell_sizes[cell_3d_ids]=4
    assert(len(np.where(cell_sizes==0)[0])==0)

    # starts of cells in "cells" array
    cell_locations=ns.vtk_to_numpy(pdi.GetCellLocationsArray())

    cells=ns.vtk_to_numpy(pdi.GetCells().GetData())
    # padd cells
    row_ends = np.concatenate((cell_locations, [len(cells)]))
    lens = np.diff(row_ends)
    max_len=np.max(lens)
    pad_len = np.max(lens) - lens
    where_to_pad = np.repeat(row_ends[1:], pad_len)
    padding_value = -1.0
    padded_cells = np.insert(cells, where_to_pad, -1).reshape(-1, max_len)

    selected_cells=padded_cells[selection_ids]
    points=selected_cells[:, 1:].flatten()
    #points=points[points!=-1]

    np.set_printoptions(threshold=np.nan)
    #print cell_locations
    #print np_region_id
    #print selection_ids
    #print selected_cells
    #print points
    #pdo.SetPoints()
    #pdo.SetCells()



  
