import os
import json
import copy
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument('--step', type=str, default='all', help="step to run")
parser.add_argument('--name', type=str, default='gof', help="Name")
args = parser.parse_args()

ws = "/vols/cms/gu18/4tau_v3/CMSSW_10_2_13/src/CombineHarvester/Combine4tau/outputs/0706_eett/all/cmb/ws.root"
freezepar = "r_A60,r_A70,r_A80,r_A90,r_A125,r_A140,r_A160"
poi = "r_A100"

sig_scale = 0
setpar = "r_A60=0,r_A70=0,r_A80=0,r_A90=0,r_A100={},r_A125=0,r_A140=0,r_A160=0".format(sig_scale)
shift = 1.0
parranges = "r_A100={},{}:r_A60=0,0:r_A70=0,0:r_A80=0,0:r_A90=0,0:r_A125=0,0:r_A140=0,0:r_A160=0,0".format(sig_scale-shift,sig_scale+shift)

mass = "100"
name = args.name


step = args.step

algo = "saturated"

ntoys = 2000
ntoysperjob = 20

if step in ["run","all"]:
  os.system("combine -M GoodnessOfFit -d %(ws)s -n .%(name)s_%(algo)s --algo=%(algo)s --setParameters %(setpar)s --fixedSignalStrength=0 -m %(mass)s" % vars())
  for i in range(0,int(ntoys/ntoysperjob)):
    seed = 1234 + i
    os.system("combineTool.py -M GoodnessOfFit -d %(ws)s -n .%(name)s_%(algo)s --algo=%(algo)s --setParameters %(setpar)s --fixedSignalStrength=0 -m %(mass)s -t %(ntoysperjob)s -s %(seed)s --job-mode SGE  --prefix-file ic --sub-opts \"-q hep.q -l h_rt=3:0:0\" --task-name=\"%(name)s_%(algo)s_%(i)i\"" % vars())

elif step in ["collect","all"]:
  inputs = ""
  for i in range(0,int(ntoys/ntoysperjob)):
    seed = 1234 + i
    inputs += "higgsCombine.%(name)s_%(algo)s.GoodnessOfFit.mH%(mass)s.root higgsCombine.%(name)s_%(algo)s.GoodnessOfFit.mH%(mass)s.%(seed)s.root " % vars()
  os.system("combineTool.py -M CollectGoodnessOfFit --input %(inputs)s -m 100.0 -o %(name)s_%(algo)s.json" % vars())
  os.system("plotGof.py %(name)s_%(algo)s.json --statistic %(algo)s --mass 100.0 -o %(name)s_%(algo)s_plot --title-right=\"138 fb^{-1} (13 TeV)\"" % vars())
