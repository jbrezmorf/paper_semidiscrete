#from paraview.simple import *
from paraview import servermanager 

servermanager.Connect()    
frac = servermanager.sources.HierarchicalFractal()
#frac.UpdatePipeline()
iv = servermanager.filters.IntegrateVariables(frac)
#script="""
#import vtk
#pdi = self.GetPolyDataInput()
#pdo = self.GetOutput()
#iv=vtk.vtkIntegrateAttributes()
#iv.SetInputData(pdi)
#iv.Update()
#pdo=iv.GetOutput()
#"""
#pf=servermanager.filters.ProgrammableFilter(Input=frac, Script=script)
#pf.UpdatePipeline()

servermanager.Disconnect()
