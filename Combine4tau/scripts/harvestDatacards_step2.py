# importing packages
import sys
import os
import numpy as np
from datetime import datetime
from prettytable import PrettyTable
from argparse import ArgumentParser
import yaml

description = '''This script makes datacards with CombineHarvester.'''
parser = ArgumentParser(prog="harvesterDatacards_step2",description=description,epilog="Success!")
parser.add_argument('-c', '--config', dest='config', type=str, default='config/harvestDatacards_step2.yml', action='store', help="set config file")
args = parser.parse_args()

with open(args.config, 'r') as file:
   setup = yaml.safe_load(file)
# ------------------------------------
# Setup from config file
folder = setup["folder"]
year = setup["year"]
channels = setup["channels"]
build_workspaces = setup["build_workspaces"]
calculate_limits = setup["calculate_limits"]
unblind = setup["unblind"]
collect_limits = setup["collect_limits"]
grid_A = setup["grid_A"]
grid_phi = setup["grid_phi"]

cmssw_base = os.getcwd()

pTable = PrettyTable()
column_names = ["Option", "Setting"]
pTable.add_column(column_names[0], ["Folder","Year","Channels","Build Workspaces","Calculate Limits","Unblind","Collect Limits","Grid of mA","Grid of m#phi"])
pTable.add_column(column_names[0], [folder,year,channels,build_workspaces,calculate_limits,unblind,collect_limits,grid_A,grid_phi])
print(pTable)
# ------------------------------------

# Build the workspaces
log_workspace = "workspace" + datetime.today().strftime('%d%m')
if (build_workspaces == True):
   for chan in channels:
      if chan != "cmb": 
         chan += "_inclusive"
      os.system("python %(cmssw_base)s/../CombineTools/scripts/combineTool.py -M T2W -o ws.root -P CombineHarvester.Combine4tau.X2HDM:X2HDM -i %(cmssw_base)s/%(folder)s/%(year)s/%(chan)s/ --parallel 4 | tee -a %(cmssw_base)s/logs/%(log_workspace)s_%(chan)s.txt" % vars())

# Gather all workspaces in the appropriate directories 
for chan in channels:
   if chan != "cmb":
      chan += "_inclusive"
   for mA in grid_A:
      if (os.path.exists("%(cmssw_base)s/%(folder)s/%(year)s/%(chan)s/m%(mA)s" %vars()) == False):
         os.mkdir("%(cmssw_base)s/%(folder)s/%(year)s/%(chan)s/m%(mA)s" %vars())
      os.system("cp %(cmssw_base)s/%(folder)s/%(year)s/%(chan)s/ws.root %(cmssw_base)s/%(folder)s/%(year)s/%(chan)s/m%(mA)s/ws.root" %vars())

# ------------------------------------

def ParametersToFreeze(grid_A,mA):
  '''Returns the POIs to be freezed for each mA'''
  frozen_POIs=""
  frozen_POIs_SetToZero=""
  for A in grid_A:
    if A != mA:
       frozen_POIs += ("r_A"+ A + ",")
       frozen_POIs_SetToZero += ("r_A"+ A + "=0,")
  if frozen_POIs_SetToZero[-1] == ",": frozen_POIs_SetToZero = frozen_POIs_SetToZero[:-1]
  if frozen_POIs[-1] == ",": frozen_POIs = frozen_POIs[:-1]
  return frozen_POIs,frozen_POIs_SetToZero 

# Calculate AsymptoticLimits 
log_limits = "limits" + datetime.today().strftime('%d%m')
grid_phi_str = ','.join(grid_phi)
if (calculate_limits):
   for chan in channels:
      if chan != "cmb":
         chan += "_inclusive"
      for mA in grid_A:
        POI = "r_A"+mA
        frozen_POIs,frozen_POIs_SetToZero = ParametersToFreeze(grid_A,mA)
        if (unblind == False):
           os.system("python %(cmssw_base)s/../CombineTools/scripts/combineTool.py -M AsymptoticLimits -m %(grid_phi_str)s --redefineSignalPOIs %(POI)s --setParameters %(frozen_POIs_SetToZero)s --freezeParameters %(frozen_POIs)s -d %(cmssw_base)s/%(folder)s/%(year)s/%(chan)s/m%(mA)s/ws.root --X-rtd MINIMIZER_analytic --rAbsAcc 0 --rRelAcc 0.0005 --cminDefaultMinimizerStrategy 0 --cminDefaultMinimizerTolerance 0.01 -v 1 --there --run blind | tee -a %(cmssw_base)s/logs/%(log_limits)s_%(chan)s_mA%(mA)s.txt" %vars())
        else:
           os.system("python %(cmssw_base)s/../CombineTools/scripts/combineTool.py -M AsymptoticLimits -m %(grid_phi_str)s --redefineSignalPOIs %(POI)s --setParameters %(frozen_POIs_SetToZero)s --freezeParameters %(frozen_POIs)s -d %(cmssw_base)s/%(folder)s/%(year)s/%(chan)s/m%(mA)s/ws.root --X-rtd MINIMIZER_analytic --rAbsAcc 0 --rRelAcc 0.0005 --cminDefaultMinimizerStrategy 0 --cminDefaultMinimizerTolerance 0.01 -v 1 --there | tee -a %(cmssw_base)s/logs/%(log_limits)s_%(chan)s_mA%(mA)s.txt" %vars())

# ------------------------------------

# Collect Limits
if (collect_limits):
   for chan in channels:
      if chan != "cmb":
         chan += "_inclusive"
      for mA in grid_A:
         os.system("python %(cmssw_base)s/../CombineTools/scripts/combineTool.py -M CollectLimits %(cmssw_base)s/%(folder)s/%(year)s/%(chan)s/m%(mA)s/higgsCombine.Test.AsymptoticLimits.mH*.root --use-dirs -o %(cmssw_base)s/%(folder)s/%(year)s/%(chan)s/limit.json" %vars()) 


