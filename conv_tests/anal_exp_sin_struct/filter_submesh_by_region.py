"""
Paraview ProgrammableFilter.

This filter assumes a variable 'filter_parameters' that is dictionary containing
key 'region_id_to_extract'. The cells where dataset 'region_id' is equal to provided value are extracted.

Example:
parameters={ "dimension_to_extract" : 2 }
ProgrammableFilter(Input=data_in, Script="filter_parameters="+str(parameters)+"\n"+this_file)
"""


import submesh
import numpy as np
import paraview.numpy_support as ns

pdi = self.GetPolyDataInput()
pdo = self.GetOutput()

region_id = filter_parameters["region_id_to_extract"]
region_id_array = ns.vtk_to_numpy( pdi.GetCellData().GetArray("region_id") )
cell_list=np.where(abs(region_id_array - region_id) < 0.5)[0]

submesh.submesh(pdi, pdo, cell_list)
