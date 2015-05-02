#from paraview.simple import *
from paraview import servermanager
import paraview.benchmark

#print dir(servermanager)
#print dir(servermanager.sources)
#print dir(servermanager.filters)
#print dir(servermanager.writers)


def make_chain():
    print "start"
    frac = servermanager.sources.HierarchicalFractal()
    frac.RectilinearGrids = 1
    frac.TwoDimensional = 0
    frac.MaximumLevel = 8
    frac.UpdatePipeline()

    info=frac.GetDataInformation()
    print info.GetMemorySize()
    #print paraview.benchmark.get_memuse()
    print "frac\n"

    calc = servermanager.filters.Calculator(Input = frac, 
                      Function="Fractal Volume Fraction^2",
                      ResultArrayName="square",
                      AttributeMode="Cell Data")
    calc.UpdatePipeline()
    info=calc.GetDataInformation()
    print info.GetMemorySize()
    #print paraview.benchmark.get_memuse()
    print "calc\n"

    writer=servermanager.writers.DataSetWriter(FileName="./frac.vtk", Input=calc)
    writer.UpdatePipeline()

    info=writer.GetDataInformation()
    #help(info)
    #print paraview.benchmark.get_memuse()
    print "writer\n"
    

print paraview.benchmark.get_memuse()    
servermanager.Connect()    
make_chain()    
print "before DC"
servermanager.Disconnect()
print paraview.benchmark.get_memuse()

servermanager.Connect()
print "after DC"
make_chain()    
servermanager.Disconnect()
print paraview.benchmark.get_memuse()