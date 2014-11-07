import paraview.simple as ps
import vtk

with open("/home/jb/Projekty/14_clanek_modeling/scripty/resample_2d1d.py","rt") as f:
    request_data_script=f.read()

program=vtk.vtkPythonProgrammableFilter()
#program.SetOutputDataSetType(0) # vtkMultiblockDataSet
program.SetScript(request_data_script)

for i in range(self.GetNumberOfInputConnections(0)):
    program.AddInputConnection(0,self.GetInputConnection(0,i))
program.Update()

self.GetOutput().ShallowCopy(program.GetOutput())
