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
combine_categories = setup["combine_categories"] if "combine_categories" in setup else []
categories = setup["categories"] if "categories" in setup else []
model_dependent = setup["model_dependent"]
cosbma = setup["cosbma"]
cmssw_base = os.getcwd()

po_ws = ""
split_higgs = "A"
if model_dependent: 
  po_ws = "--PO model_dependent"
  split_higgs = "phi"  
elif cosbma:
  po_ws = "--PO cosbma"
  split_higgs = "phi"

pTable = PrettyTable()
column_names = ["Option", "Setting"]
pTable.add_column(column_names[0], ["Folder","Year","Channels","Build Workspaces","Build Combined Workspaces","Calculate AsymptoticLimits","Calculate Combined Asymptotic Limits","Calculate HybridNew","Unblind","Collect Limits","Collect Combined Limits","Grid of mA","Grid of m#phi","Model Dependent"])
pTable.add_column(column_names[0], [folder,year,channels,build_workspaces,build_combined_workspaces,calculate_AsymptoticLimits,calculate_combined_AsymptoticLimits,calculate_HybridNew,unblind,collect_limits,collect_combined_limits,grid_A,grid_phi,model_dependent])
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
      os.system("python %(cmssw_base)s/../CombineTools/scripts/combineTool.py -M T2W -o ws.root %(po_ws)s -P CombineHarvester.Combine4tau.X2HDM:X2HDM -i %(cmssw_base)s/%(folder)s/%(year)s/%(category_folder)s/ --parallel 4 | tee -a %(cmssw_base)s/%(folder)s/%(year)s/logs/%(log_workspace)s_%(category_folder)s.txt" % vars())

      # Make Directories for Limits
      if (os.path.exists("%(cmssw_base)s/%(folder)s/%(year)s/%(category_folder)s/limits" %vars()) == False):
         os.mkdir("%(cmssw_base)s/%(folder)s/%(year)s/%(category_folder)s/limits"%vars())
      for m in setup["grid_"+split_higgs]:
         if (os.path.exists("%(cmssw_base)s/%(folder)s/%(year)s/%(category_folder)s/limits/%(split_higgs)s%(m)s" %vars()) == False):
            os.mkdir("%(cmssw_base)s/%(folder)s/%(year)s/%(category_folder)s/limits/%(split_higgs)s%(m)s" %vars())
        
if (build_workspaces == True):
   for chan in channels:
      if chan == "cmb":
         os.system("python %(cmssw_base)s/../CombineTools/scripts/combineTool.py -M T2W -o ws.root %(po_ws)s -P CombineHarvester.Combine4tau.X2HDM:X2HDM -i %(cmssw_base)s/%(folder)s/%(year)s/%(chan)s/ --parallel 4 | tee -a %(cmssw_base)s/%(folder)s/%(year)s/logs/%(log_workspace)s_%(chan)s.txt" % vars())
         # Make Directories for Limits
         if (os.path.exists("%(cmssw_base)s/%(folder)s/%(year)s/%(chan)s/limits" %vars()) == False):
            os.mkdir("%(cmssw_base)s/%(folder)s/%(year)s/%(chan)s/limits"%vars())
         for m in setup["grid_"+split_higgs]:
            if (os.path.exists("%(cmssw_base)s/%(folder)s/%(year)s/%(chan)s/limits/%(split_higgs)s%(m)s" %vars()) == False):
               os.mkdir("%(cmssw_base)s/%(folder)s/%(year)s/%(chan)s/limits/%(split_higgs)s%(m)s" %vars())

      else:
         for cat in categories['{}'.format(chan)]:
            category = cat[1]
            os.system("python %(cmssw_base)s/../CombineTools/scripts/combineTool.py -M T2W -o ws.root %(po_ws)s -P CombineHarvester.Combine4tau.X2HDM:X2HDM -i %(cmssw_base)s/%(folder)s/%(year)s/%(chan)s_%(category)s/ --parallel 4 | tee -a %(cmssw_base)s/%(folder)s/%(year)s/logs/%(log_workspace)s_%(chan)s_%(category)s.txt" % vars())
         
            # Make Directories for Limits
            if (os.path.exists("%(cmssw_base)s/%(folder)s/%(year)s/%(chan)s_%(category)s/limits" %vars()) == False):
               os.mkdir("%(cmssw_base)s/%(folder)s/%(year)s/%(chan)s_%(category)s/limits"%vars())
            for m in setup["grid_"+split_higgs]:
               if (os.path.exists("%(cmssw_base)s/%(folder)s/%(year)s/%(chan)s_%(category)s/limits/%(split_higgs)s%(m)s" %vars()) == False):
                  os.mkdir("%(cmssw_base)s/%(folder)s/%(year)s/%(chan)s_%(category)s/limits/%(split_higgs)s%(m)s" %vars())

# ------------------------------------


def ParametersToFreeze(grid, m, h, sto=False, satz=False):
  '''Returns the POIs to be freezed for each mass'''
  frozen_POIs=""
  frozen_POIs_SetToZero=""
  for i in grid:
    if i != m:
       frozen_POIs += ("r_" + h + i + ",")
       frozen_POIs_SetToZero += ("r_"+ h + i + "=0,")
    elif i == m and sto:
       frozen_POIs += ("r_" + h + i + ",")
       frozen_POIs_SetToZero += ("r_"+ h + i + "=1,")
    elif satz:
       frozen_POIs_SetToZero += ("r_"+ h + i + "=0,")
  if frozen_POIs_SetToZero[-1] == ",": frozen_POIs_SetToZero = frozen_POIs_SetToZero[:-1]
  if frozen_POIs[-1] == ",": frozen_POIs = frozen_POIs[:-1]
  return frozen_POIs,frozen_POIs_SetToZero 

# Calculate AsymptoticLimits 
log_limits = "AL" + datetime.today().strftime('%d%m')
if not (model_dependent or cosbma):
  grid_str = ','.join(grid_phi)
else:
  grid_str = ','.join(grid_A)

if (calculate_combined_AsymptoticLimits):
   for chan in channels:
      category_folder = combine_categories['{}'.format(chan)]["folder"]
      for m in setup["grid_"+split_higgs]:
         if not model_dependent:
           POI = "r_"+split_higgs+m
         else:
           POI = "tanb"
         frozen_POIs,frozen_POIs_SetToZero = ParametersToFreeze(setup["grid_"+split_higgs],m,split_higgs,sto=model_dependent)
         if (unblind == False):
            add_cond = ""
            os.system("python %(cmssw_base)s/../CombineTools/scripts/combineTool.py -M AsymptoticLimits -m %(grid_str)s --redefineSignalPOIs %(POI)s --setParameters %(frozen_POIs_SetToZero)s --freezeParameters %(frozen_POIs)s -d %(cmssw_base)s/%(folder)s/%(year)s/%(category_folder)s/ws.root --X-rtd MINIMIZER_analytic --cminDefaultMinimizerStrategy 0 --rMin 0 --rMax 1 --run expected | tee -a %(cmssw_base)s/%(folder)s/%(year)s/logs/%(log_limits)s_%(category_folder)s_m%(split_higgs)s%(m)s.txt" %vars())
         os.system("mv higgsCombine*Asymptotic*.root %(cmssw_base)s/%(folder)s/%(year)s/%(category_folder)s/limits/%(split_higgs)s%(m)s"%vars())

if (calculate_AsymptoticLimits):
   for chan in channels:
      if chan == "cmb":
         for m in setup["grid_"+split_higgs]:
            if not model_dependent:
              POI = "r_"+split_higgs+m
            else:
              POI = "tanb"
            frozen_POIs,frozen_POIs_SetToZero = ParametersToFreeze(setup["grid_"+split_higgs],m,split_higgs,sto=model_dependent,satz=cosbma)
            method = "-M AsymptoticLimits"
            blinding = "--run expected"
            if cosbma: 
              method = "-M AsymptoticGrid %(cmssw_base)s/input/cosbma_tanb_grid.json" % vars()
              blinding = "-t -1"
            if (unblind == False):
               add_cond = ""
               if not (model_dependent or cosbma): add_cond += " --rMin 0 --rMax 0.02"
               os.system("pushd %(cmssw_base)s/%(folder)s/%(year)s/%(chan)s/limits/%(split_higgs)s%(m)s; python %(cmssw_base)s/../CombineTools/scripts/combineTool.py %(method)s -m %(grid_str)s --redefineSignalPOIs %(POI)s --setParameters %(frozen_POIs_SetToZero)s --freezeParameters %(frozen_POIs)s -d %(cmssw_base)s/%(folder)s/%(year)s/%(chan)s/ws.root --X-rtd MINIMIZER_analytic --cminDefaultMinimizerStrategy 0 %(blinding)s  --job-mode SGE  --prefix-file ic --sub-opts \"-q hep.q -l h_rt=3:0:0\" --task-name %(split_higgs)s%(m)s%(add_cond)s --dry-run | tee -a %(cmssw_base)s/%(folder)s/%(year)s/logs/%(log_limits)s_%(chan)s_m%(split_higgs)s%(m)s.txt; popd" %vars())
            #os.system("mv higgsCombine*Asymptotic*.root %(cmssw_base)s/%(folder)s/%(year)s/%(chan)s/limits/%(split_higgs)s%(m)s"%vars())

      else:
         for cat in categories['{}'.format(chan)]:
            category = cat[1]
            for m in setup["grid_"+split_higgs]:
               if not model_dependent:
                 POI = "r_"+split_higgs+m
               else:
                 POI = "tanb"
 
               frozen_POIs,frozen_POIs_SetToZero = ParametersToFreeze(setup["grid_"+split_higgs],m,split_higgs,sto=model_dependent)
               #frozen_POIs += ",alpha"
               if (unblind == False):
                  os.system("python %(cmssw_base)s/../CombineTools/scripts/combineTool.py -M AsymptoticLimits -m %(grid_str)s --redefineSignalPOIs %(POI)s --setParameters %(frozen_POIs_SetToZero)s --freezeParameters %(frozen_POIs)s -d %(cmssw_base)s/%(folder)s/%(year)s/%(chan)s_%(category)s/ws.root --X-rtd MINIMIZER_analytic --cminDefaultMinimizerStrategy 0 --rMin 0 --rMax 0.5 --run expected | tee -a %(cmssw_base)s/%(folder)s/%(year)s/logs/%(log_limits)s_%(chan)s_%(category)s_m%(split_higgs)s%(m)s.txt" %vars())
               os.system("mv higgsCombine*Asymptotic*.root %(cmssw_base)s/%(folder)s/%(year)s/%(chan)s_%(category)s/limits/%(split_higgs)s%(m)s"%vars())

#
if (calculate_HybridNew):
  for chan in channels:
     for cat in categories['{}'.format(chan)]:
        category = cat[1]
        for m in setup["grid_"+split_higgs]:
          if not model_dependent:
            POI = "r_"+split_higgs+m
          else:
            POI = "tanb"
          frozen_POIs,frozen_POIs_SetToZero = ParametersToFreeze(setup["grid_"+split_higgs],m,split_higgs,sto=model_dependent)
          for mphi in grid_phi:
             inFile = ROOT.TFile.Open("%(cmssw_base)s/%(folder)s/%(year)s/%(chan)s_%(category)s/limits/%(split_higgs)s%(m)s/higgsCombine.Test.AsymptoticLimits.mH%(mphi)s.root"%vars())
             tree = inFile.Get("limit")
             tree.GetEvent(2)
             ALimit = tree.limit
             inFile.Close()
             lower_bound = 0.1 * ALimit
             upper_bound = 2.0 * ALimit
             if (unblind == False): 
               os.system("python %(cmssw_base)s/../CombineTools/scripts/combineTool.py -M HybridNew %(cmssw_base)s/%(folder)s/%(year)s/%(chan)s_%(category)s/ws.root -m %(mphi)s --LHCmode LHC-limits --redefineSignalPOIs %(POI)s --setParameters %(frozen_POIs_SetToZero)s --freezeParameters %(frozen_POIs)s --setParameterRanges %(POI)s=0,%(upper_bound)s --cminDefaultMinimizerStrategy 0 --expectedFromGrid 0.5 --rAbsAcc %(lower_bound)s --fork 16" %vars())
             os.system("mv higgsCombine*5*.root %(cmssw_base)s/%(folder)s/%(year)s/%(chan)s_%(category)s/limits/%(split_higgs)s%(m)s"%vars())



# # ------------------------------------

# Collect Limits
if (collect_limits):
   for chan in channels:
      if chan == "cmb":
         for m in setup["grid_"+split_higgs]:
            os.system("python %(cmssw_base)s/../CombineTools/scripts/combineTool.py -M CollectLimits %(cmssw_base)s/%(folder)s/%(year)s/%(chan)s/limits/%(split_higgs)s%(m)s/higgsCombine.Test.AsymptoticLimits.mH*.root --use-dirs -o %(cmssw_base)s/%(folder)s/%(year)s/%(chan)s/limits/%(split_higgs)s%(m)s/limit.json" %vars())
      else:
         for cat in categories['{}'.format(chan)]:
            category = cat[1]
            for m in setup["grid_"+split_higgs]:
               os.system("python %(cmssw_base)s/../CombineTools/scripts/combineTool.py -M CollectLimits %(cmssw_base)s/%(folder)s/%(year)s/%(chan)s_%(category)s/limits/%(split_higgs)s%(m)s/higgsCombine.Test.AsymptoticLimits.mH*.root --use-dirs -o %(cmssw_base)s/%(folder)s/%(year)s/%(chan)s_%(category)s/limits/%(split_higgs)s%(m)s/limit.json" %vars()) 


if (collect_combined_limits):
   for chan in channels:
      category_folder = combine_categories['{}'.format(chan)]["folder"]
      for m in setup["grid_"+split_higgs]:
         os.system("python %(cmssw_base)s/../CombineTools/scripts/combineTool.py -M CollectLimits %(cmssw_base)s/%(folder)s/%(year)s/%(category_folder)s/limits/%(split_higgs)s%(m)s/higgsCombine.Test.AsymptoticLimits.mH*.root --use-dirs -o %(cmssw_base)s/%(folder)s/%(year)s/%(category_folder)s/limits/%(split_higgs)s%(m)s/limit.json" %vars())






