# CombineHarvester

Full documentation: http://cms-analysis.github.io/CombineHarvester

## Quick start

A new full release area can be set up and compiled in the following steps:

    export SCRAM_ARCH=slc7_amd64_gcc700
    cmsrel CMSSW_10_2_13
    cd CMSSW_10_2_13/src
    cmsenv
    git clone https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit.git HiggsAnalysis/CombinedLimit
    cd $CMSSW_BASE/src/HiggsAnalysis/CombinedLimit
    git fetch origin
    git checkout v8.2.0
    scramv1 b clean; scramv1 b # always make a clean build

    cd $CMSSW_BASE/src/
    git clone -b 4tau git@github.com:Ksavva1021/CombineHarvester.git CombineHarvester
    scram b

