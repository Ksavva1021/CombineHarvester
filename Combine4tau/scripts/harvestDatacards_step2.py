# importing packages
import sys
import os
import numpy as np
from datetime import datetime
from prettytable import PrettyTable
from argparse import ArgumentParser
import yaml
import ROOT

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
build_combined_workspaces = setup["build_combined_workspaces"]
calculate_AsymptoticLimits = setup["calculate_AsymptoticLimits"]
calculate_combined_AsymptoticLimits = setup["calculate_combined_AsymptoticLimits"]
calculate_HybridNew = setup["calculate_HybridNew"]
unblind = setup["unblind"]
collect_limits = setup["collect_limits"]
collect_combined_limits = setup["collect_combined_limits"]
grid_A = setup["grid_A"]
grid_phi = setup["grid_phi"]
combine_categories = setup["combine_categories"]
categories = setup["categories"]
cmssw_base = os.getcwd()

pTable = PrettyTable()
column_names = ["Option", "Setting"]
pTable.add_column(column_names[0], ["Folder","Year","Channels","Build Workspaces","Build Combined Workspaces","Calculate AsymptoticLimits","Calculate Combined Asymptotic Limits","Calculate HybridNew","Unblind","Collect Limits","Collect Combined Limits","Grid of mA","Grid of m#phi"])
pTable.add_column(column_names[0], [folder,year,channels,build_workspaces,build_combined_workspaces,calculate_AsymptoticLimits,calculate_combined_AsymptoticLimits,calculate_HybridNew,unblind,collect_limits,collect_combined_limits,grid_A,grid_phi])
print(pTable)
# ------------------------------------

# Build the workspaces
log_workspace = "workspace" + datetime.today().strftime('%d%m')
if (os.path.exists("%(cmssw_base)s/%(folder)s/%(year)s/logs" %vars()) == False):
   os.mkdir("%(cmssw_base)s/%(folder)s/%(year)s/logs"%vars())

if (build_combined_workspaces == True):
   for chan in channels:
      category_folder = combine_categories['{}'.format(chan)]["folder"] 
      # first gather all root files and text datacards in new folder
      if (os.path.exists("%(cmssw_base)s/%(folder)s/%(year)s/%(category_folder)s" %vars()) == False):
         os.mkdir("%(cmssw_base)s/%(folder)s/%(year)s/%(category_folder)s"%vars())
         os.mkdir("%(cmssw_base)s/%(folder)s/%(year)s/%(category_folder)s/common"%vars())
      for cat in combine_categories['{}'.format(chan)]["categories"]:
         category = cat[1]
         os.system("cp -r %(cmssw_base)s/%(folder)s/%(year)s/%(chan)s_%(category)s/*.txt %(cmssw_base)s/%(folder)s/%(year)s/%(category_folder)s/"%vars())
         os.system("cp -r %(cmssw_base)s/%(folder)s/%(year)s/%(chan)s_%(category)s/common/*.root %(cmssw_base)s/%(folder)s/%(year)s/%(category_folder)s/common"%vars())
       
   for chan in channels:
      category_folder = combine_categories['{}'.format(chan)]["folder"]
      os.system("python %(cmssw_base)s/../CombineTools/scripts/combineTool.py -M T2W -o ws.root -P CombineHarvester.Combine4tau.X2HDM:X2HDM -i %(cmssw_base)s/%(folder)s/%(year)s/%(category_folder)s/ --parallel 4 | tee -a %(cmssw_base)s/%(folder)s/%(year)s/logs/%(log_workspace)s_%(category_folder)s.txt" % vars())

      # Make Directories for Limits
      if (os.path.exists("%(cmssw_base)s/%(folder)s/%(year)s/%(category_folder)s/limits" %vars()) == False):
         os.mkdir("%(cmssw_base)s/%(folder)s/%(year)s/%(category_folder)s/limits"%vars())
      for mA in grid_A:
         if (os.path.exists("%(cmssw_base)s/%(folder)s/%(year)s/%(category_folder)s/limits/A%(mA)s" %vars()) == False):
            os.mkdir("%(cmssw_base)s/%(folder)s/%(year)s/%(category_folder)s/limits/A%(mA)s" %vars())
        
if (build_workspaces == True):
   for chan in channels:
      if chan == "cmb":
         os.system("python %(cmssw_base)s/../CombineTools/scripts/combineTool.py -M T2W -o ws.root -P CombineHarvester.Combine4tau.X2HDM:X2HDM -i %(cmssw_base)s/%(folder)s/%(year)s/%(chan)s/ --parallel 4 | tee -a %(cmssw_base)s/%(folder)s/%(year)s/logs/%(log_workspace)s_%(chan)s.txt" % vars())
         # Make Directories for Limits
         if (os.path.exists("%(cmssw_base)s/%(folder)s/%(year)s/%(chan)s/limits" %vars()) == False):
            os.mkdir("%(cmssw_base)s/%(folder)s/%(year)s/%(chan)s/limits"%vars())
         for mA in grid_A:
            if (os.path.exists("%(cmssw_base)s/%(folder)s/%(year)s/%(chan)s/limits/A%(mA)s" %vars()) == False):
               os.mkdir("%(cmssw_base)s/%(folder)s/%(year)s/%(chan)s/limits/A%(mA)s" %vars())

      else:
         for cat in categories['{}'.format(chan)]:
            category = cat[1]
            os.system("python %(cmssw_base)s/../CombineTools/scripts/combineTool.py -M T2W -o ws.root -P CombineHarvester.Combine4tau.X2HDM:X2HDM -i %(cmssw_base)s/%(folder)s/%(year)s/%(chan)s_%(category)s/ --parallel 4 | tee -a %(cmssw_base)s/%(folder)s/%(year)s/logs/%(log_workspace)s_%(chan)s_%(category)s.txt" % vars())
         
            # Make Directories for Limits
            if (os.path.exists("%(cmssw_base)s/%(folder)s/%(year)s/%(chan)s_%(category)s/limits" %vars()) == False):
               os.mkdir("%(cmssw_base)s/%(folder)s/%(year)s/%(chan)s_%(category)s/limits"%vars())
            for mA in grid_A:
               if (os.path.exists("%(cmssw_base)s/%(folder)s/%(year)s/%(chan)s_%(category)s/limits/A%(mA)s" %vars()) == False):
                  os.mkdir("%(cmssw_base)s/%(folder)s/%(year)s/%(chan)s_%(category)s/limits/A%(mA)s" %vars())

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
log_limits = "AL" + datetime.today().strftime('%d%m')
grid_phi_str = ','.join(grid_phi)

if (calculate_combined_AsymptoticLimits):
   for chan in channels:
      category_folder = combine_categories['{}'.format(chan)]["folder"]
      for mA in grid_A:
         POI = "r_A"+mA
         frozen_POIs,frozen_POIs_SetToZero = ParametersToFreeze(grid_A,mA)
         if (unblind == False):
            os.system("python %(cmssw_base)s/../CombineTools/scripts/combineTool.py -M AsymptoticLimits -m %(grid_phi_str)s --redefineSignalPOIs %(POI)s --setParameters %(frozen_POIs_SetToZero)s --freezeParameters %(frozen_POIs)s -d %(cmssw_base)s/%(folder)s/%(year)s/%(category_folder)s/ws.root --X-rtd MINIMIZER_analytic --cminDefaultMinimizerStrategy 0 --run expected | tee -a %(cmssw_base)s/%(folder)s/%(year)s/logs/%(log_limits)s_%(category_folder)s_mA%(mA)s.txt" %vars())
         os.system("mv higgsCombine*Asymptotic*.root %(cmssw_base)s/%(folder)s/%(year)s/%(category_folder)s/limits/A%(mA)s"%vars())

if (calculate_AsymptoticLimits):
   for chan in channels:
      if chan == "cmb":
         for mA in grid_A:
            POI = "r_A"+mA
            frozen_POIs,frozen_POIs_SetToZero = ParametersToFreeze(grid_A,mA)
            if (unblind == False):
               os.system("python %(cmssw_base)s/../CombineTools/scripts/combineTool.py -M AsymptoticLimits -m %(grid_phi_str)s --redefineSignalPOIs %(POI)s --setParameters %(frozen_POIs_SetToZero)s --freezeParameters %(frozen_POIs)s -d %(cmssw_base)s/%(folder)s/%(year)s/%(chan)s/ws.root --X-rtd MINIMIZER_analytic --cminDefaultMinimizerStrategy 0 --run expected -v3| tee -a %(cmssw_base)s/%(folder)s/%(year)s/logs/%(log_limits)s_%(chan)s_mA%(mA)s.txt" %vars())
            os.system("mv higgsCombine*Asymptotic*.root %(cmssw_base)s/%(folder)s/%(year)s/%(chan)s/limits/A%(mA)s"%vars())

      else:
         for cat in categories['{}'.format(chan)]:
            category = cat[1]
            for mA in grid_A:
               POI = "r_A"+mA
               frozen_POIs,frozen_POIs_SetToZero = ParametersToFreeze(grid_A,mA)
               if (unblind == False):
                  os.system("python %(cmssw_base)s/../CombineTools/scripts/combineTool.py -M AsymptoticLimits -m %(grid_phi_str)s --redefineSignalPOIs %(POI)s --setParameters %(frozen_POIs_SetToZero)s --freezeParameters %(frozen_POIs)s -d %(cmssw_base)s/%(folder)s/%(year)s/%(chan)s_%(category)s/ws.root --X-rtd MINIMIZER_analytic --cminDefaultMinimizerStrategy 0 --run expected | tee -a %(cmssw_base)s/%(folder)s/%(year)s/logs/%(log_limits)s_%(chan)s_%(category)s_mA%(mA)s.txt" %vars())
               os.system("mv higgsCombine*Asymptotic*.root %(cmssw_base)s/%(folder)s/%(year)s/%(chan)s_%(category)s/limits/A%(mA)s"%vars())

#
if (calculate_HybridNew):
  for chan in channels:
     for cat in categories['{}'.format(chan)]:
        category = cat[1]
        for mA in grid_A:
          POI = "r_A"+mA
          frozen_POIs,frozen_POIs_SetToZero = ParametersToFreeze(grid_A,mA)
          for mphi in grid_phi:
             inFile = ROOT.TFile.Open("%(cmssw_base)s/%(folder)s/%(year)s/%(chan)s_%(category)s/limits/A%(mA)s/higgsCombine.Test.AsymptoticLimits.mH%(mphi)s.root"%vars())
             tree = inFile.Get("limit")
             tree.GetEvent(2)
             ALimit = tree.limit
             inFile.Close()
             lower_bound = 0.1 * ALimit
             upper_bound = 2.0 * ALimit
             if (unblind == False): 
               os.system("python %(cmssw_base)s/../CombineTools/scripts/combineTool.py -M HybridNew %(cmssw_base)s/%(folder)s/%(year)s/%(chan)s_%(category)s/ws.root -m %(mphi)s --LHCmode LHC-limits --redefineSignalPOIs %(POI)s --setParameters %(frozen_POIs_SetToZero)s --freezeParameters %(frozen_POIs)s --setParameterRanges %(POI)s=0,%(upper_bound)s --cminDefaultMinimizerStrategy 0 --expectedFromGrid 0.5 --rAbsAcc %(lower_bound)s --fork 16" %vars())
             os.system("mv higgsCombine*5*.root %(cmssw_base)s/%(folder)s/%(year)s/%(chan)s_%(category)s/limits/A%(mA)s"%vars())



# # ------------------------------------

# Collect Limits
if (collect_limits):
   for chan in channels:
      if chan == "cmb":
         for mA in grid_A:
            os.system("python %(cmssw_base)s/../CombineTools/scripts/combineTool.py -M CollectLimits %(cmssw_base)s/%(folder)s/%(year)s/%(chan)s/limits/A%(mA)s/higgsCombine.Test.AsymptoticLimits.mH*.root --use-dirs -o %(cmssw_base)s/%(folder)s/%(year)s/%(chan)s/limits/A%(mA)s/limit.json" %vars())
      else:
         for cat in categories['{}'.format(chan)]:
            category = cat[1]
            for mA in grid_A:
               os.system("python %(cmssw_base)s/../CombineTools/scripts/combineTool.py -M CollectLimits %(cmssw_base)s/%(folder)s/%(year)s/%(chan)s_%(category)s/limits/A%(mA)s/higgsCombine.Test.AsymptoticLimits.mH*.root --use-dirs -o %(cmssw_base)s/%(folder)s/%(year)s/%(chan)s_%(category)s/limits/A%(mA)s/limit.json" %vars()) 


if (collect_combined_limits):
   for chan in channels:
      category_folder = combine_categories['{}'.format(chan)]["folder"]
      for mA in grid_A:
         os.system("python %(cmssw_base)s/../CombineTools/scripts/combineTool.py -M CollectLimits %(cmssw_base)s/%(folder)s/%(year)s/%(category_folder)s/limits/A%(mA)s/higgsCombine.Test.AsymptoticLimits.mH*.root --use-dirs -o %(cmssw_base)s/%(folder)s/%(year)s/%(category_folder)s/limits/A%(mA)s/limit.json" %vars())







