#!/bin/bash
cd /vols/cms/gu18/4tau_v3/CMSSW_10_2_19//src/UserCode/ICHiggsTauTau/Analysis/4tau
source /vols/grid/cms/setup.sh
export SCRAM_ARCH=slc6_amd64_gcc481
eval 'scramv1 runtime -sh'
source /vols/cms/gu18/4tau_v3/CMSSW_10_2_19//src/UserCode/ICHiggsTauTau/Analysis/4tau/scripts/setup_libs.sh
ulimit -c 0
python /vols/cms/gu18/4tau_v3/CMSSW_10_2_19/src/UserCode/ICHiggsTauTau/Analysis/4tau/scripts/combined_year_4tauPlot.py --outputfolder=/vols/cms/gu18/4tau_v3/CMSSW_10_2_19/src/UserCode/ICHiggsTauTau/Analysis/4tau/0512/emtt --options="--folder=/vols/cms/gu18/Offline/output/4tau/2411_ff_v2 --no_signal --charges_non_zero --under_legend='FF_{total}' --method=2 --var='tau_decay_mode_4[0,1,2,3,4,5,6,7,8,9,10,11,12]' --vsjets=loose --ratio_range=0,2"  --channel=emtt --cat=inclusive --run_datacards --extra_name=tau_decay_mode_4_ff_full
