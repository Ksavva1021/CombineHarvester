import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
import os, sys, re
import CombineHarvester.CombineTools.ch as ch
from CombineHarvester.CombineTools.ch import CombineHarvester, MassesFromRange, SystMap, BinByBinFactory, CardWriter, SetStandardBinNames, AutoRebin, BinByBinFactory
import CombineHarvester.CombinePdfs.morphing as morphing
from CombineHarvester.CombinePdfs.morphing import BuildRooMorphing
from CombineHarvester.CombinePdfs.morphing import BuildCMSHistFuncFactory
import ROOT
from ROOT import RooWorkspace, TFile, RooRealVar
from datetime import datetime
import yaml
import json
import copy
from prettytable import PrettyTable
from argparse import ArgumentParser

# HI
description = '''This script makes datacards with CombineHarvester.'''
parser = ArgumentParser(prog="harvesterDatacards",description=description,epilog="Success!")
parser.add_argument('--output_folder', dest='output_folder', type=str, default='outputs/', action='store', help="set config file")
parser.add_argument('-c', '--config', dest='config', type=str, default='config/run_combine.yml', help="Output folder")
parser.add_argument('--model_dep', help= 'Run model dependent limits',  action='store_true')
parser.add_argument('--cosbma', help= 'Run tanb-cosbma limits',  action='store_true')
parser.add_argument('--only_harvest', help= 'Only harvest txt datacards',  action='store_true')
parser.add_argument('--only_ws', help= 'Only run ws',  action='store_true')
parser.add_argument('--only_limit', help= 'Only run limit',  action='store_true')
parser.add_argument('--run', help= 'Run the harvesting, ws and limits',  action='store_true')
parser.add_argument('--collect', help= 'Collect the limits and plot',  action='store_true')
args = parser.parse_args()

with open(args.config, 'r') as file:
   setup = yaml.safe_load(file)
# ------------------------------------
# Setup from config file
output_folder = args.output_folder
analysis = setup["analysis"]
era_tag = setup["year"]
channels = setup["channels"]
categories = setup["categories"]
variable = setup["variable"]
bkg_procs = setup["background_processes"]
A_masses = setup["A_masses"]
phi_masses = setup["phi_masses"]
auto_rebin = setup["auto_rebin"]
use_automc = setup["auto_mc"]
verbose = setup["verbose"]
do_systematics = setup["do_systematics"]
systematics = setup["systematics"]
input_dir_path = setup["path"]
cmssw_base = os.getcwd()


pTable = PrettyTable()
column_names = ["Option", "Setting"]
pTable.add_column(column_names[0], ["Output Folder","Analysis","Year","Channels","Variable","A Masses","phi Masses","Auto Rebin","AutoMC","Verbose"])
pTable.add_column(column_names[0], [output_folder,analysis,era_tag,channels,variable,A_masses,phi_masses,auto_rebin,use_automc,verbose])
print(pTable)
# ------------------------------------

# Reformatting categories
cats = {}
x = lambda a : tuple(a)
for chn in channels:
   temp = []
   for cat in categories[chn]:
      temp.append(x(cat))
   cats['{}'.format(chn)] = temp   

def green(string,**kwargs):
    return kwargs.get('pre',"")+"\x1b[0;32;40m%s\033[0m"%string

def SetRateForNegativeHistSyst(p):
  if p.type() != "shape": return
  histU = p.shape_u().Clone()
  histD = p.shape_d().Clone()
  if histU.Integral() < 0 and histD.Integral() < 0:
    print "Setting Rate For Negative Histograms Systematic"
    nom = harvester.cp().process([p.process()]).channel([p.channel()]).bin([p.bin()]).GetShape()
    p.set_value_u(histU.Integral()/nom.Integral())
    p.set_value_d(histD.Integral()/nom.Integral())
    histU.Scale(-1.0)
    histD.Scale(-1.0)
    p.set_shapes(histU,histD,None)

def SetRateForNegativeHist(p):
  hist = p.shape().Clone()
  if p.rate() < 0:
    print "Setting Rate For Negative Histograms"
    p.set_rate(p.rate()*-1.0)
    harvester.cp().process([p.process()]).channel([p.channel()]).bin([p.bin()]).AddSyst(harvester, "rate_minus","rateParam",SystMap()(-1.0))
    harvester.GetParameter("rate_minus").set_range(-1.0,-1.0)


def NegativeBins(p):
  '''Replaces negative bins in hists with 0'''
  print("Process is: ",p.process())
  hist = p.shape()
  has_negative = False
  for i in range(1,hist.GetNbinsX()+1):
    if hist.GetBinContent(i) < 0:
       has_negative = True
       print("Process: ",p.process()," has negative bins.")
  if (has_negative):
    for i in range(1,hist.GetNbinsX()+1):
       if hist.GetBinContent(i) < 0:
          hist.SetBinContent(i,0)
  p.set_shape(hist,False)

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

if args.model_dep or args.cosbma:
  sig_procs = ["phi"+i for i in phi_masses] 
  mass_shifts = A_masses 
else:
  sig_procs = ["A"+i for i in A_masses]
  mass_shifts = phi_masses

po_ws = ""
split_higgs = "A"
other_higgs = "phi"
if args.model_dep:
  po_ws = "--PO model_dependent"
  split_higgs = "phi"
  other_higgs = "A"
elif args.cosbma:
  po_ws = "--PO cosbma"
  split_higgs = "phi"
  other_higgs = "A"

if not (args.model_dep or args.cosbma):
  grid_str = ','.join(phi_masses)
else:
  grid_str = ','.join(A_masses)


if args.run:

  ### Harvest datacards ###

  if args.only_harvest or not (args.only_ws or args.only_limit):
  
    if (os.path.exists("{}/{}".format(output_folder,era_tag))):
      os.system("rm -r {}/{}".format(output_folder,era_tag))
    
    # Create an empty CombineHarvester instance
    harvester = CombineHarvester()
    for chn in channels:
      # Adding Data,Signal Processes and Background processes to the harvester instance
      harvester.AddObservations(['*'], [analysis], [era_tag], [chn], cats[chn])
      harvester.AddProcesses(['*'], [analysis], [era_tag], [chn], [i for j in bkg_procs[chn] for i in j], cats[chn], False)
      harvester.AddProcesses(mass_shifts, [analysis], [era_tag], [chn], sig_procs, cats[chn], True)
    
    if do_systematics:
       for syst in systematics:
          sysDef = copy.deepcopy(systematics[syst])
    
          do_sig_procs = False
          if "sig_procs" in sysDef["processes"]:
            do_sig_procs = True
            sysDef["processes"].remove("sig_procs")
            sysDef["processes"] = [i for j in sysDef["processes"] for i in j]
    
          scaleFactor = 1.0
          if "scaleFactor" in sysDef:
             scaleFactor = sysDef["scaleFactor"]
          
          if ("all" in sysDef["channel"] and ("YEAR" not in syst)):
             harvester.cp().process(sysDef["processes"]).AddSyst(harvester,sysDef["name"] if "name" in sysDef else syst, sysDef["effect"], SystMap()(scaleFactor)) 
             if do_sig_procs:
               harvester.cp().process(sig_procs).mass(mass_shifts).AddSyst(harvester,sysDef["name"] if "name" in sysDef else syst, sysDef["effect"], SystMap()(scaleFactor))
    
    
          elif ("YEAR" not in syst):
             harvester.cp().process(sysDef["processes"]).channel(sysDef["channel"]).AddSyst(harvester,sysDef["name"] if "name" in sysDef else syst, sysDef["effect"], SystMap()(scaleFactor))
             if do_sig_procs:
               harvester.cp().process(sig_procs).mass(mass_shifts).channel(sysDef["channel"]).AddSyst(harvester,sysDef["name"] if "name" in sysDef else syst, sysDef["effect"], SystMap()(scaleFactor))
    
    
          if "YEAR" in syst:
    #         for year in ["2016_preVFP","2016_postVFP","2017","2018"]:
             for year in ["2018"]:
    
                name = sysDef["name"].replace("YEAR",year)
                if ("all" in sysDef["channel"]):
                  harvester.cp().process(sysDef["processes"]).AddSyst(harvester,name, sysDef["effect"], SystMap()(scaleFactor))
                  if do_sig_procs:
                    harvester.cp().process(sig_procs).mass(mass_shifts).AddSyst(harvester,name, sysDef["effect"], SystMap()(scaleFactor))
    
                else:
                  harvester.cp().process(sysDef["processes"]).channel(sysDef["channel"]).AddSyst(harvester,name, sysDef["effect"], SystMap()(scaleFactor))
                  if do_sig_procs:
                    harvester.cp().process(sig_procs).mass(mass_shifts).channel(sysDef["channel"]).AddSyst(harvester,name, sysDef["effect"], SystMap()(scaleFactor))
    
    
       if args.model_dep or args.cosbma:
          with open("input/4tau_xs_uncerts.json") as jsonfile: sig_xs = json.load(jsonfile)
          for k,v in sig_xs.items():
            phi_mass = k.split("phi")[1].split("A")[0]
            A_mass = k.split("A")[1].split("To")[0]
            for syst, lnN in v.items():
               harvester.cp().process(["phi{}".format(phi_mass)]).mass([str(A_mass)]).AddSyst(harvester,str(syst)+"_yield","lnN",SystMap()([lnN["Down"],lnN["Up"]]))
    
    
    # Populating Observation, Process and Systematic entries in the harvester instance
    for chn in channels:
      filename = input_dir_path + '/' + era_tag + "/" + chn + "/" + variable + "_" + chn + "_multicat_" + era_tag + ".root"
      print ">>>   file %s"%(filename)
      print(chn)
      harvester.cp().channel([chn]).process([i for j in bkg_procs[chn] for i in j]).ExtractShapes(filename, "$BIN/$PROCESS", "$BIN/$PROCESS_$SYSTEMATIC")
      if not (args.model_dep or args.cosbma):
        harvester.cp().channel([chn]).process(sig_procs).ExtractShapes(filename, "$BIN/$PROCESSphi$MASS_norm", "$BIN/$PROCESSphi$MASS_$SYSTEMATIC")
      else:
        harvester.cp().channel([chn]).process(sig_procs).ExtractShapes(filename, "$BIN/A$MASS$PROCESS", "$BIN/A$MASS$PROCESS_$SYSTEMATIC")
       
    if(auto_rebin):
      rebin = AutoRebin()
      rebin.SetBinThreshold(0)
      rebin.SetBinUncertFraction(1.0)
      rebin.SetRebinMode(1)
      rebin.SetPerformRebin(True)
      rebin.SetVerbosity(1) 
      rebin.Rebin(harvester,harvester)
    
    # Replacing negative bins
    harvester.ForEachSyst(SetRateForNegativeHistSyst)
    harvester.ForEachProc(SetRateForNegativeHist)
    
    harvester.PrintAll()
    
    workspace = RooWorkspace(analysis,analysis)
    
    # RooVar
    Mphi = RooRealVar("MH","Mass of H/h in GeV", float(mass_shifts[0]), float(mass_shifts[-1]))
    Mphi.setConstant(True)
    
    # MORPHING
    print green(">>> morphing...")
    BuildCMSHistFuncFactory(workspace, harvester, Mphi, ",".join(sig_procs))
    
    workspace.writeToFile("workspace_py.root")
    
    # EXTRACT PDFs
    print green(">>> add workspace and extract pdf...")
    harvester.AddWorkspace(workspace, False)
    harvester.ExtractPdfs(harvester, analysis, "$BIN_$PROCESS_morph", "")  # Extract all processes (signal and bkg are named the same way)
    harvester.ExtractData(analysis, "$BIN_data_obs")  # Extract the RooDataHist
    #
    if (use_automc):
       # Set the autoMCStats line (with -1 = no bbb uncertainties)
       # Set threshold to 0.3 to use Poisson PDF instead
       harvester.SetAutoMCStats(harvester, 0.5, 0, 1)
    
    if verbose>0:
        print green("\n>>> print observation...\n")
        harvester.PrintObs()
        print green("\n>>> print processes...\n")
        harvester.PrintProcs()
        print green("\n>>> print systematics...\n")
        harvester.PrintSysts()
        print green("\n>>> print parameters...\n")
        harvester.PrintParams()
        print "\n"
    
    # WRITER
    print green(">>> writing datacards...")
    datacardtxt  = "%s/%s/$BIN/$BIN.txt"%(output_folder,era_tag)
    datacardroot = "%s/%s/$BIN/common/$BIN_input_%s.root"%(output_folder,era_tag,era_tag)
    writer = CardWriter(datacardtxt,datacardroot)
    writer.SetVerbosity(1)
    writer.SetWildcardMasses([ ])
    writer.WriteCards("cmb", harvester)
    
    # You have to delete the workspace as otherwise you will get a memory management seg val (You can avoid this if you use a newer version of PyROOT or if you run the file within a function)
    workspace.Delete()
    
    # Relocating outputs to ease further processing
    if (os.path.exists("{}/{}/cmb".format(output_folder,era_tag))):
      os.system("rm -r {}/{}/cmb".format(output_folder,era_tag))
    os.system("mkdir {}/{}/cmb".format(output_folder,era_tag))
    
    if (os.path.exists("{}/{}/cmb/common".format(output_folder,era_tag))):
      os.system("rm -r {}/{}/cmb/common".format(output_folder,era_tag))
    os.system("mkdir {}/{}/cmb/common".format(output_folder,era_tag))
    
    os.system("cp -r {}/{}/*/*/*.root {}/{}/cmb/common/".format(output_folder,era_tag,output_folder,era_tag))
    os.system("cp -r {}/{}/*/*.txt {}/{}/cmb/".format(output_folder,era_tag,output_folder,era_tag))
    os.system("mv workspace_py.root {}/{}/".format(output_folder,era_tag))
  
  ### Run Workspace ###
  
  if args.only_ws or not (args.only_harvest or args.only_limit):
    # Build the workspaces
    log_workspace = "workspace" + datetime.today().strftime('%d%m')
    if (os.path.exists("%(cmssw_base)s/%(output_folder)s/%(era_tag)s/logs" %vars()) == False):
       os.mkdir("%(cmssw_base)s/%(output_folder)s/%(era_tag)s/logs"%vars())
  
    os.system("python %(cmssw_base)s/../CombineTools/scripts/combineTool.py -M T2W -o ws.root %(po_ws)s -P CombineHarvester.Combine4tau.X2HDM:X2HDM -i %(cmssw_base)s/%(output_folder)s/%(era_tag)s/cmb/ --parallel 4 | tee -a %(cmssw_base)s/%(output_folder)s/%(era_tag)s/logs/%(log_workspace)s_cmb.txt" % vars())
    # Make Directories for Limits
    if (os.path.exists("%(cmssw_base)s/%(output_folder)s/%(era_tag)s/cmb/limits" %vars()) == False):
       os.mkdir("%(cmssw_base)s/%(output_folder)s/%(era_tag)s/cmb/limits"%vars())
    for m in setup[split_higgs+"_masses"]:
       if (os.path.exists("%(cmssw_base)s/%(output_folder)s/%(era_tag)s/cmb/limits/%(split_higgs)s%(m)s" %vars()) == False):
          os.mkdir("%(cmssw_base)s/%(output_folder)s/%(era_tag)s/cmb/limits/%(split_higgs)s%(m)s" %vars())
  
  
  ### Run Limits ###
  if args.only_limit or not (args.only_harvest or args.only_ws):
    for m in setup[split_higgs+"_masses"]:
      if not args.model_dep:
        POI = "r_"+split_higgs+m
      else:
        POI = "tanb"
      frozen_POIs,frozen_POIs_SetToZero = ParametersToFreeze(setup[split_higgs+"_masses"],m,split_higgs,sto=args.model_dep,satz=args.cosbma)
      method = "-M AsymptoticLimits"
      blinding = "--run expected"
      log_limits = "AL" + datetime.today().strftime('%d%m')
      if args.cosbma:
        method = "-M AsymptoticGrid %(cmssw_base)s/input/cosbma_tanb_grid.json" % vars()
        blinding = "-t -1"
      add_cond = ""
      if not (args.model_dep or args.cosbma): add_cond += " --rMin 0 --rMax 0.02"
      loop_mass = [grid_str]
      name_ext = ""
      if args.cosbma: 
        #loop_mass=grid_str.split(",")
        loop_mass = ["200"]
      for grid_str in loop_mass:
        if args.cosbma: name_ext = other_higgs + grid_str
        os.system("pushd %(cmssw_base)s/%(output_folder)s/%(era_tag)s/cmb/limits/%(split_higgs)s%(m)s; python %(cmssw_base)s/../CombineTools/scripts/combineTool.py %(method)s -m %(grid_str)s --redefineSignalPOIs %(POI)s --setParameters %(frozen_POIs_SetToZero)s --freezeParameters %(frozen_POIs)s -d %(cmssw_base)s/%(output_folder)s/%(era_tag)s/cmb/ws.root --X-rtd MINIMIZER_analytic --cminDefaultMinimizerStrategy 0 %(blinding)s  --job-mode SGE  --prefix-file ic --sub-opts \"-q hep.q -l h_rt=3:0:0\" --task-name %(split_higgs)s%(m)s%(name_ext)s%(add_cond)s --dry-run | tee -a %(cmssw_base)s/%(output_folder)s/%(era_tag)s/logs/%(log_limits)s_cmb_m%(split_higgs)s%(m)s.txt; popd" %vars())

if args.collect:

  if args.model_dep or not args.cosbma:

    for m in setup[split_higgs+"_masses"]:
      os.system("python %(cmssw_base)s/../CombineTools/scripts/combineTool.py -M CollectLimits %(cmssw_base)s/%(output_folder)s/%(era_tag)s/cmb/limits/%(split_higgs)s%(m)s/higgsCombine.Test.AsymptoticLimits.mH*.root --use-dirs -o %(cmssw_base)s/%(output_folder)s/%(era_tag)s/cmb/limits/%(split_higgs)s%(m)s/limit.json" %vars())

    if not args.cosbma:
      os.system("python scripts/plotting/plot_all_model_independent_limits.py --folder=%(output_folder)s" % vars()) 
    elif args.model_dep:
      for m in phi_masses:
        os.system("python scripts/plotting/plot_model_dependent_limits.py %(output_folder)s/%(era_tag)s/cmb/limits/phi%(m)s/limit_phi%(m)s.json --excluded-mass=%(m)s --logy --scenario-label=\"m_{#phi} = %(m)s GeV\" --output=\"md_mphi$%(m)s_hb\" --title-left=\"Type X 2HDM Alignment Scenario\"" % vars())
        os.system("python scripts/plotting/plot_model_dependent_limits.py %(output_folder)s/%(era_tag)s/cmb/limits/phi%(m)s/limit_phi%(m)s.json --logy --scenario-label=\"m_{#phi} = %(m)s GeV\" --output=\"md_mphi$%(m)s\" --title-left=\"Type X 2HDM Alignment Scenario\"" % vars())


