import os
import json
import copy

ws = "/vols/cms/gu18/4tau_v3/CMSSW_10_2_13/src/CombineHarvester/Combine4tau/0806_unblinding/all/cmb/ws.root"
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


os.system("combine -M ChannelCompatibilityCheckRegexGroup -d %(ws)s -m %(mass)s --setParameters %(setpar)s --setParameterRanges %(parranges)s --redefineSignalPOIs %(poi)s --X-rtd MINIMIZER_analytic --X-rtd FITTER_NEW_CROSSING_ALGO --cminDefaultMinimizerStrategy 0 --cminDefaultMinimizerTolerance 0.1 --robustFit 1 --stepSize 0.1 -n .CCC.channel --saveFitResult -g eett -g mmtt -g ettt -g mttt -g emtt -g ttt -g tttt -v 1" % vars())
os.system("python scripts/plotting/plot_ccc.py higgsCombine.CCC.channel.ChannelCompatibilityCheckRegexGroup.mH%(mass)s.root -o ChannelCompatibilityCheck_FitResults_mH%(mass)s_channel -p %(poi)s --legend-position=0 -r m0.2,0.1" % vars())
