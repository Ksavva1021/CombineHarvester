import os
import json
import copy

ws = "/vols/cms/gu18/4tau_v3/CMSSW_10_2_13/src/CombineHarvester/Combine4tau/outputs/1704_mi_test/all/cmb/ws.root"
setpar = "r_A60=0,r_A70=0,r_A80=0,r_A90=0,r_A100=0,r_A125=0,r_A140=0,r_A160=0"
freezepar = "r_A60,r_A70,r_A80,r_A90,r_A125,r_A140,r_A160"
poi = "r_A100"
parranges = "r_A100=-0.1,0.1"
mass = "140"

#step = "run"
step = "collect"

if step == "run":

  os.system("combineTool.py -M Impacts --redefineSignalPOIs %(poi)s --setParameters %(setpar)s --freezeParameters %(freezepar)s --setParameterRanges %(parranges)s --X-rtd MINIMIZER_analytic --cminDefaultMinimizerStrategy 0 -m %(mass)s -d %(ws)s --doInitialFit --robustFit 1 -t -1" % vars())
  os.system("combineTool.py -M Impacts --redefineSignalPOIs %(poi)s --setParameters %(setpar)s --freezeParameters %(freezepar)s --setParameterRanges %(parranges)s --X-rtd MINIMIZER_analytic --cminDefaultMinimizerStrategy 0 -m %(mass)s -d %(ws)s --doFits --robustFit 1 -v 3  -t -1 --job-mode SGE  --prefix-file ic --sub-opts \"-q hep.q -l h_rt=3:0:0\"" % vars())

elif step == "collect":

  os.system("combineTool.py -M Impacts --redefineSignalPOIs %(poi)s --setParameters %(setpar)s --freezeParameters %(freezepar)s --setParameterRanges %(parranges)s --X-rtd MINIMIZER_analytic --cminDefaultMinimizerStrategy 0 -m %(mass)s -d %(ws)s --o impacts.json -v 3  -t -1" % vars())

  # remove unconstrained nuissances
  with open("impacts.json") as jsonfile: impacts = json.load(jsonfile)
  new_impacts = copy.deepcopy(impacts)

  for k1, v1 in impacts.items():
    for v2 in v1:
      if k1 == "params" and v2["type"] == "Unconstrained":
        new_impacts[k1].remove(v2)
  with open("impacts.json", 'w') as outfile: json.dump(new_impacts, outfile) 

  os.system("plotImpacts.py -i impacts.json -o impacts")
