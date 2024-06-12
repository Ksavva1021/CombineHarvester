from HiggsAnalysis.CombinedLimit.PhysicsModel import PhysicsModel
from HiggsAnalysis.CombinedLimit.SMHiggsBuilder import SMHiggsBuilder
import numpy as np
import ROOT
import imp
import os

class X2HDM(PhysicsModel):
    def __init__(self):
        PhysicsModel.__init__(self)
        self.model_dependent = False
        self.branching_ratio = False
        self.A_only_branching_ratio = False
        self.phi_only_branching_ratio = False
        self.m_A = [40,50,60,70,80,90,100,125,140,160,200,250,300,400,600,800]
        self.m_phi = [60,70,80,90,100,110,125,140,160,180,200,250,300]       
        self.base = '{}/Combine4tau'.format(os.getcwd().split("Combine4tau")[0])

    def setPhysicsOptions(self, physOptions):
        for po in physOptions:
          if po.startswith("model_dependent"):
            self.model_dependent = True
          if po.startswith("branching_ratio"):
            self.branching_ratio = True
          if po.startswith("A_only_branching_ratio"):
            self.A_only_branching_ratio = True
          if po.startswith("phi_only_branching_ratio"):
            self.phi_only_branching_ratio = True
          if po.startswith("mA"):
            #self.m_A = [po[2:]]
            self.m_A = [int(i) for i in po.split("[")[1].split("]")[0].split(",")]
          if po.startswith("mphi"):
            #self.mphi = [po[4:-1]]
            self.m_phi = [int(i) for i in po.split("[")[1].split("]")[0].split(",")]

    def doParametersOfInterest(self):
        """Create POI and other parameters, and define the POI set."""
        poiNames = []
        if self.model_dependent or self.A_only_branching_ratio or self.phi_only_branching_ratio:
          self.modelBuilder.doVar("tanb[1,1,90]")
          poiNames.append('tanb')
          self.modelBuilder.factory_('expr::tanb_capped("max(min(@0,90.0),1.3)", tanb)')
        elif self.branching_ratio:
          self.modelBuilder.doVar("br[1,0,1]")
          poiNames.append('br')
        else:
          for j in self.m_A:
            self.modelBuilder.doVar("r_A{}[1,0,20]".format(j))
            poiNames.append('r_A{}'.format(j))          

        self.modelBuilder.doSet('POI', ','.join(poiNames))
        
        if self.model_dependent or self.A_only_branching_ratio or self.phi_only_branching_ratio:
          wsptools = imp.load_source('wsptools', '{}/scripts/workspaceTools.py'.format(self.base))
          #f = ROOT.TFile("{}/input/typeX_info_v5.root".format(self.base))
          #f = ROOT.TFile("{}/input/mphi300only.root".format(self.base))
          f = ROOT.TFile("{}/input/typeX_BRs.root".format(self.base))

          for j in self.m_phi:
            name = "brs_mphi{}".format(str(float(j)).replace(".","p"))
            h = f.Get(name).Clone()
            wsptools.SafeWrapHist(self.modelBuilder.out, ['MH','tanb_capped'], h, name='brs_mphi{}'.format(j))
            self.modelBuilder.out.function('brs_mphi{}'.format(j)).setInterpolationOrder(2)

            if self.model_dependent:
              self.modelBuilder.factory_('expr::br_phi{}("max(@0,0.0)", {})'.format(j, "brs_mphi{}".format(j)))

          """
          for j in self.m_phi:
            for higgs in ["phi","A"]:

              if higgs == "phi" and self.A_only_branching_ratio: continue
              if higgs == "A" and self.phi_only_branching_ratio: continue

              if higgs == "phi":
                if j >= 125:
                  hHA = "H"
                else:
                  hHA = "h"
              else:
                hHA = "A"

              name = "br_mphi{}_csbma0p0_{}_to_tautau".format(str(float(j)).replace(".","p"),hHA)
              h = f.Get(name).Clone()
              #wsptools.SafeWrapHist(self.modelBuilder.out, ['MH','tanb'], h, name='br_{}_mphi{}'.format(higgs,j))
              wsptools.SafeWrapHist(self.modelBuilder.out, ['MH','tanb_capped'], h, name='br_{}_mphi{}'.format(higgs,j))
              self.modelBuilder.out.function('br_{}_mphi{}'.format(higgs,j)).setInterpolationOrder(1)

            if self.model_dependent:
              self.modelBuilder.factory_('expr::br_phi{}("max(@0*@1,0.0)", {}, {})'.format(j, "br_phi_mphi{}".format(j), "br_A_mphi{}".format(j)))

          """

    def getYieldScale(self, bin_, process):

        scalings = []
        if self.model_dependent:
          for j in self.m_phi:
            candidate = 'phi{}'.format(j)
            if candidate in process:
              scalings.append('br_phi{}'.format(j))
        elif self.branching_ratio:
          for j in self.m_phi:
            candidate = 'phi{}'.format(j)
            if candidate in process:
              scalings.append('br')
        elif self.A_only_branching_ratio:
          for j in self.m_phi:
            candidate = 'phi{}'.format(j)
            if candidate in process:
              scalings.append('br_A_mphi{}'.format(j))          
        elif self.phi_only_branching_ratio:
          for j in self.m_phi:
            candidate = 'phi{}'.format(j)
            if candidate in process:
              scalings.append('br_phi_mphi{}'.format(j)) 
        else:
          for j in self.m_A:
            candidate = 'A{}'.format(j)
            if candidate == process:
              scalings.append('r_A{}'.format(j))

        print("Scalings:")
        for s in scalings:
          print(s)

        if scalings:
          scaling = '_'.join(scalings)
          return scaling
        else:
          return 1

X2HDM = X2HDM()
