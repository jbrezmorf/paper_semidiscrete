import vtk

iv=vtk.vtkIntegrateAttributes()
for i in range(self.GetNumberOfInputConnections(0)):
    iv.AddInputConnection(0,self.GetInputConnection(0,i))
iv.Update()
self.GetOutput().ShallowCopy(iv.GetOutput())

