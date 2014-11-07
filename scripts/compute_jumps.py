#
# This script computes left and right jumps along fracture for given scalar point dataset.
# Name of the dataset is specified by the "jump_point_data" variable.
# Left jump is fracture_value - left_side_value
# Right jump is fracture_value - right_side_value


import math
from ctypes import c_int

VTK_LINE=3
VTK_QUAD=9

jump_point_data_name="pressure_p1"

"""
Assumes mesh resulting from reconstruct_shift.py script.
That is, points along fracture (all points of all 1D elements) are stored as three shifted points
which are stored as a triplet left, right, middle.
Therefore points on sides of a fracture are stored just before the fracture point.
"""

# Find dataset, create dataset for left and right jumps, initialize to zero
pdi = self.GetPolyDataInput()
pdo = self.GetOutput()
jump_data=pdi.GetPointData().GetArray(jump_point_data_name);
n_points=pdi.GetNumberOfPoints()

jump_left = vtk.vtkDoubleArray()
jump_left.SetName("left_jump_" + jump_point_data_name)
jump_left.SetNumberOfComponents(jump_data.GetNumberOfComponents())
jump_left.SetNumberOfTuples( n_points )

jump_right = vtk.vtkDoubleArray()
jump_right.SetName("right_jump_" + jump_point_data_name)
jump_right.SetNumberOfComponents(jump_data.GetNumberOfComponents())
jump_right.SetNumberOfTuples( n_points )

zero_tuple=[0]*jump_data.GetNumberOfComponents()
one_tuple[1]*jump_data.GetNumberOfComponents()
for i in range(n_points) :
    jump_left.SetTupleValue(i,zero_tuple)
    jump_right.SetTupleValue(i,zero_tuple)
    
# pass through points of 1d elements
for i_cell in range(pdi.GetNumberOfCells()):
    cell=pdi.GetCell(i)
    if ( cell.GetCellType() == VTK_LINE ) :
        points=cell.GetPoints()
        for i_point in range(points.GetNumberOfPoints()) :
            point=points.GetPoint(i_point)
            fracture_value=jump_data.GetTuple(point)
            left_value=jump_data.GetTuple(point-2)
            right_value=jump_data.GetTuple(point-1)
            
            print fracture_value - left_value
            jump_left.SetTuple(point, one_tuple)
            #jump_left.SetTuple(point, fracture_value - left_value)
            #jump_right.SetTuple(point, fracture_value - right_value)

pdo.GetPointData().AddArray(jump_left)
pdo.GetPointData().AddArray(jump_right)
