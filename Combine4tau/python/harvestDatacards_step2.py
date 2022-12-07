#!/usr/bin/env python

# Command to run:
#python python/harvestDatacards_step2.py --channel='cmb,emtt,ettt,mmtt,mttt,tttt,eett' --folder=output_X2HDM_0712  --limits --blind --collect_limits

# importing packages
import sys
from optparse import OptionParser
import os
import numpy as np
from datetime import datetime

parser = OptionParser()
parser.add_option('--channel',help= 'Name of input channels', default='tttt')
parser.add_option('--folder', help= 'Folder for processing', default='output')
parser.add_option('--year', help= 'Year for processing', default='all')
parser.add_option('--skip', help = 'Skip part 2', action='store_true')
parser.add_option('--limits',help= 'Run limits', action='store_true')
parser.add_option('--blind', help= 'Blinding', action='store_true')
parser.add_option('--grid_phi', help= 'Grid of Phi Masses', default='100,110,125,140,160,180,200,250,300')
parser.add_option('--grid_A', help= 'Grid of A Masses', default='60,70,80,90,100,125,140,160')
parser.add_option('--collect_limits', help='Collect limits in a single json file', action='store_true')
(options, args) = parser.parse_args()
# initialising variables
folder = options.folder
channels = options.channel.split(',')
year = options.year

print 'Folder:      %(folder)s' % vars()
print 'Processing channels:      %(channels)s' % vars()

cmssw_base = os.getcwd()
log_workspace = "workspace" + datetime.today().strftime('%d%m')
log_limits = "limits" + datetime.today().strftime('%d%m')

if (options.skip != True):
   for chan in channels:
      if chan != "cmb": 
         chan += "_inclusive"
      os.system("python %(cmssw_base)s/../CombineTools/scripts/combineTool.py -M T2W -o ws.root -P CombineHarvester.Combine4tau.X2HDM:X2HDM -i %(cmssw_base)s/%(folder)s/%(year)s/%(chan)s/ --parallel 4 | tee -a %(cmssw_base)s/logs/%(log_workspace)s_%(chan)s.txt" % vars())
       
grid_A = options.grid_A.split(',')
grid_phi = options.grid_phi

for chan in channels:
   if chan != "cmb":
      chan += "_inclusive"
   for mA in grid_A:
      if (os.path.exists("%(cmssw_base)s/%(folder)s/%(year)s/%(chan)s/m%(mA)s" %vars()) == False):
         os.mkdir("%(cmssw_base)s/%(folder)s/%(year)s/%(chan)s/m%(mA)s" %vars())
      os.system("cp %(cmssw_base)s/%(folder)s/%(year)s/%(chan)s/ws.root %(cmssw_base)s/%(folder)s/%(year)s/%(chan)s/m%(mA)s/ws.root" %vars())

def ParametersToFreeze(grid_A,mA):
  frozen_POIs=""
  frozen_POIs_SetToZero=""
  for A in grid_A:
    if A != mA:
       frozen_POIs += ("r_A"+ A + ",")
       frozen_POIs_SetToZero += ("r_A"+ A + "=0,")
  if frozen_POIs_SetToZero[-1] == ",": frozen_POIs_SetToZero = frozen_POIs_SetToZero[:-1]
  if frozen_POIs[-1] == ",": frozen_POIs = frozen_POIs[:-1]
  return frozen_POIs,frozen_POIs_SetToZero 

if (options.limits):
   for chan in channels:
      if chan != "cmb":
         chan += "_inclusive"
      for mA in grid_A:
	 POI = "r_A"+mA
         frozen_POIs,frozen_POIs_SetToZero = ParametersToFreeze(grid_A,mA)
         if (options.blind):
            os.system("python %(cmssw_base)s/../CombineTools/scripts/combineTool.py -M AsymptoticLimits -m %(grid_phi)s --redefineSignalPOIs %(POI)s --setParameters %(frozen_POIs_SetToZero)s --freezeParameters %(frozen_POIs)s -d %(cmssw_base)s/%(folder)s/%(year)s/%(chan)s/m%(mA)s/ws.root --X-rtd MINIMIZER_analytic --rAbsAcc 0 --rRelAcc 0.0005 --cminDefaultMinimizerStrategy 0 --cminDefaultMinimizerTolerance 0.01 -v 1 --there --run blind | tee -a %(cmssw_base)s/logs/%(log_limits)s_%(chan)s_mA%(mA)s.txt" %vars())
         else:
            os.system("python %(cmssw_base)s/../CombineTools/scripts/combineTool.py -M AsymptoticLimits -m %(grid_phi)s --redefineSignalPOIs %(POI)s --setParameters %(frozen_POIs_SetToZero)s --freezeParameters %(frozen_POIs)s -d %(cmssw_base)s/%(folder)s/%(year)s/%(chan)s/m%(mA)s/ws.root --X-rtd MINIMIZER_analytic --rAbsAcc 0 --rRelAcc 0.0005 --cminDefaultMinimizerStrategy 0 --cminDefaultMinimizerTolerance 0.01 -v 1 --there | tee -a %(cmssw_base)s/logs/%(log_limits)s_%(chan)s_mA%(mA)s.txt" %vars())

if (options.collect_limits):
   for chan in channels:
      if chan != "cmb":
         chan += "_inclusive"
      for mA in grid_A:
         os.system("python %(cmssw_base)s/../CombineTools/scripts/combineTool.py -M CollectLimits %(cmssw_base)s/%(folder)s/%(year)s/%(chan)s/m%(mA)s/higgsCombine.Test.AsymptoticLimits.mH*.root --use-dirs -o %(cmssw_base)s/%(folder)s/%(year)s/%(chan)s/limit.json" %vars()) 





