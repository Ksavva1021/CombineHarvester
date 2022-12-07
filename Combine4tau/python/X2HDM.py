from HiggsAnalysis.CombinedLimit.PhysicsModel import PhysicsModel
from HiggsAnalysis.CombinedLimit.SMHiggsBuilder import SMHiggsBuilder
import numpy as np
import ROOT

class X2HDM(PhysicsModel):
    def __init__(self):
        PhysicsModel.__init__(self)

    def doParametersOfInterest(self):
        """Create POI and other parameters, and define the POI set."""
        poiNames = []
        self.modelBuilder.doVar("r[1,0,20]")
        poiNames.append('r') 
        m_A = [60,70,80,90,100,125,140,160]
        for j in m_A:
          self.modelBuilder.doVar("r_A{}[1,0,20]".format(j))
          poiNames.append('r_A{}'.format(j))

        self.modelBuilder.doSet('POI', ','.join(poiNames))

    def getYieldScale(self, bin_, process):

        scalings = []
        m_A = [60,70,80,90,100,125,140,160] 
        for j in m_A:
             candidate = 'A{}'.format(j)
             if candidate in process:
               scalings.append('r_A{}'.format(j))

        if scalings:
          scaling = '_'.join(scalings)
	  return scaling
	else:
	  return 1

X2HDM = X2HDM()
