import os
import json
import copy
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument('--step', type=str, default='run', help="step to run")
parser.add_argument('--name', type=str, default='impacts', help="Name")
args = parser.parse_args()

ws = "/vols/cms/gu18/4tau_v3/CMSSW_10_2_13/src/CombineHarvester/Combine4tau/outputs/0405/all/cmb/ws.root"
freezepar = "r_A60,r_A70,r_A80,r_A90,r_A125,r_A140,r_A160"
poi = "r_A100"

# bkg only
sig_scale = 0
# sig + bkg
#sig_scale = 0.2902



setpar = "r_A60=0,r_A70=0,r_A80=0,r_A90=0,r_A100={},r_A125=0,r_A140=0,r_A160=0".format(sig_scale)
shift = 1.0
parranges = "r_A100={},{}:r_A60=0,0:r_A70=0,0:r_A80=0,0:r_A90=0,0:r_A125=0,0:r_A140=0,0:r_A160=0,0".format(sig_scale-shift,sig_scale+shift)

mass = "100"
name = args.name


step = args.step

if step == "run":

  os.system("combineTool.py -M Impacts --redefineSignalPOIs %(poi)s --setParameters %(setpar)s --freezeParameters %(freezepar)s --setParameterRanges %(parranges)s --X-rtd MINIMIZER_analytic --cminDefaultMinimizerStrategy 0 --cminDefaultMinimizerTolerance 1 -m %(mass)s -d %(ws)s --doInitialFit --robustFit 1 -t -1" % vars())
  os.system("combineTool.py -M Impacts --redefineSignalPOIs %(poi)s --setParameters %(setpar)s --freezeParameters %(freezepar)s --setParameterRanges %(parranges)s --X-rtd MINIMIZER_analytic --cminDefaultMinimizerStrategy 0 --cminDefaultMinimizerTolerance 1 -m %(mass)s -d %(ws)s --doFits --robustFit 1 -v 3  -t -1 --job-mode SGE  --prefix-file ic --sub-opts \"-q hep.q -l h_rt=3:0:0\"" % vars())

elif step == "collect":

  os.system("combineTool.py -M Impacts --redefineSignalPOIs %(poi)s --setParameters %(setpar)s --freezeParameters %(freezepar)s --setParameterRanges %(parranges)s --X-rtd MINIMIZER_analytic --cminDefaultMinimizerStrategy 0 -m %(mass)s -d %(ws)s --o %(name)s.json -v 3  -t -1" % vars())

  # remove unconstrained nuissances
  with open("%(name)s.json" % vars()) as jsonfile: impacts = json.load(jsonfile)
  new_impacts = copy.deepcopy(impacts)

  for k1, v1 in impacts.items():
    for v2 in v1:
      if k1 == "params" and v2["type"] == "Unconstrained":
        new_impacts[k1].remove(v2)
  with open("%(name)s.json" % vars(), 'w') as outfile: json.dump(new_impacts, outfile) 

  os.system("plotImpacts.py -i %(name)s.json -o %(name)s" % vars())
