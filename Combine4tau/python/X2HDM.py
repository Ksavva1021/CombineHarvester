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
        self.cosbma = False
        self.m_A = [60,70,80,90,100,125,140,160]
        self.m_phi = [100,110,125,140,160,180,200,250,300]
        self.base = '{}/Combine4tau'.format(os.getcwd().split("Combine4tau")[0])
        self.type_2hdm = "X"

    def setPhysicsOptions(self, physOptions):
        for po in physOptions:
          if po.startswith("model_dependent"):
            self.model_dependent = True
          if po.startswith("cosbma"):
            self.cosbma = True
          if po.startswith("typeII"):
            self.type_2hdm = "II"

    def doParametersOfInterest(self):
        """Create POI and other parameters, and define the POI set."""
        poiNames = []
        if not (self.model_dependent or self.cosbma):
          for j in self.m_A:
            self.modelBuilder.doVar("r_A{}[1,0,20]".format(j))
            poiNames.append('r_A{}'.format(j))
        elif self.model_dependent or self.cosbma:
          for j in self.m_phi:
            self.modelBuilder.doVar("r_phi{}[1,0,20]".format(j))
            poiNames.append('r_phi{}'.format(j))
          self.modelBuilder.doVar("tanb[1,1,120]".format(j))
          poiNames.append('tanb')
        if self.cosbma:
          self.modelBuilder.doVar("cosbma[0,-1.0,1.0]".format(j))
          poiNames.append('cosbma')

        self.modelBuilder.doSet('POI', ','.join(poiNames))
        
        if self.model_dependent or self.cosbma:
          wsptools = imp.load_source('wsptools', '{}/scripts/workspaceTools.py'.format(self.base))
          f = ROOT.TFile("{}/input/type{}_BR_renscheme7_csbma_tanb_v2.root".format(self.base,self.type_2hdm))

          for j in self.m_phi:
            mA_num = None
            func = "(@0*("
            func_var = ["r_phi{}".format(j)]
            num = 1
            missing = False
            for i in self.m_A:
              for higgs in ["phi","A"]:
                name = "BR_mphi{}_mA{}_{}_to_tautau".format(j,i,higgs)
                if name not in f.GetListOfKeys():
                  missing = True
                  break
                h = f.Get(name)
                if self.model_dependent:
                  bin_number = h.GetXaxis().FindBin(0)
                  h1 = h.ProjectionY("h1", bin_number, bin_number)
                  wsptools.SafeWrapHist(self.modelBuilder.out, ['tanb'], h1, name='br_{}_mphi{}_mA{}'.format(higgs,j,i))
                else:
                  h1 = h.Clone()
                  wsptools.SafeWrapHist(self.modelBuilder.out, ['cosbma','tanb'], h1, name='br_{}_mphi{}_mA{}'.format(higgs,j,i))

                self.modelBuilder.out.function('br_{}_mphi{}_mA{}'.format(higgs,j,i)).setInterpolationOrder(1)
              if mA_num == None:
                mA_num = 1*num
                num += 1
                func_var.append("MH")
              else:
                func += " + "
              func += "((@{}=={})*@{}*@{})".format(mA_num,i,num,num+1)
              func_var.append('br_phi_mphi{}_mA{}'.format(j,i))
              func_var.append('br_A_mphi{}_mA{}'.format(j,i))
              num += 2
            func += "))"
            print "Setting branching ratio scaling"
            if not missing:
              print func, func_var
              self.modelBuilder.factory_('expr::br_phi{}("{}", {})'.format(j,func, ",".join(func_var)))
            else:
              print "skipping"
              self.modelBuilder.factory_('expr::br_phi{}("0*@0", r_phi{})'.format(j,j))

            if self.cosbma:
              if self.m_phi > 125:
                self.modelBuilder.factory_('expr::xs("TMath::Power(TMath::Sin(TMath::ACos(@0)),2)", cosbma)')
              else:
                self.modelBuilder.factory_('expr::xs("TMath::Power(TMath::Cos(TMath::ASin(@0)),2)", cosbma)')

              self.modelBuilder.factory_('expr::xs_br_phi{}("@0*@1", xs, br_phi{})'.format(j,j))



    def getYieldScale(self, bin_, process):

        scalings = []
        if not (self.model_dependent or self.cosbma):
          for j in self.m_A:
            candidate = 'A{}'.format(j)
            if candidate in process:
              scalings.append('r_A{}'.format(j))
        elif self.model_dependent:
          for j in self.m_phi:
            candidate = 'phi{}'.format(j)
            if candidate in process:
              scalings.append('br_phi{}'.format(j))
        elif self.cosbma:
          for j in self.m_phi:
            candidate = 'phi{}'.format(j)
            if candidate in process:
              scalings.append('xs_br_phi{}'.format(j))

        if scalings:
          scaling = '_'.join(scalings)
          return scaling
        else:
          return 1

X2HDM = X2HDM()
