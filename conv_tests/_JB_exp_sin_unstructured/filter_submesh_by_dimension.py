"""
Paraview ProgrammableFilter.

This filter assumes a variable 'filter_parameters' that is dictionary conatining
key 'dimension_to_extract' with dimension of simplices to extract (allowed values are 0,1,2,3).

Example:
parameters={ "dimension_to_extract" : 2 }
ProgrammableFilter(Input=data_in, Script="filter_parameters="+str(parameters)+"\n"+this_file)
"""

import submesh
import numpy as np
import paraview.numpy_support as ns

pdi = self.GetPolyDataInput()
pdo = self.GetOutput()

dimension = filter_parameters["dimension_to_extract"]
type_to_extract = submesh.type_for_dimension[ dimension ]

cell_types=ns.vtk_to_numpy(pdi.GetCellTypesArray())
cell_list=np.where(cell_types == type_to_extract)[0]

submesh.submesh(pdi, pdo, cell_list)
