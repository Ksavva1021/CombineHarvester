import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
import os, sys, re
import CombineHarvester.CombineTools.ch as ch
from CombineHarvester.CombineTools.ch import CombineHarvester, MassesFromRange, SystMap, BinByBinFactory, CardWriter, SetStandardBinNames, AutoRebin
import CombineHarvester.CombinePdfs.morphing as morphing
from CombineHarvester.CombinePdfs.morphing import BuildRooMorphing
from CombineHarvester.CombinePdfs.morphing import BuildCMSHistFuncFactory
import ROOT
from ROOT import RooWorkspace, TFile, RooRealVar
from datetime import datetime
import yaml
from prettytable import PrettyTable
from argparse import ArgumentParser

# HI
description = '''This script makes datacards with CombineHarvester.'''
parser = ArgumentParser(prog="harvesterDatacards",description=description,epilog="Success!")
parser.add_argument('-c', '--config', dest='config', type=str, default='config/harvestDatacards.yml', action='store', help="set config file")
args = parser.parse_args()

with open(args.config, 'r') as file:
   setup = yaml.safe_load(file)
# ------------------------------------
# Setup from config file
output_folder = setup["output_folder"]
analysis = setup["analysis"]
era_tag = setup["year"]
channels = setup["channels"]
categories = setup["categories"]
variable = setup["variable"]
bkg_procs = setup["background_processes"]
sig_procs = setup["signal_processes"]
mass_shifts = setup["mass_shifts"]
auto_rebin = setup["auto_rebin"]
use_automc = setup["auto_mc"]
verbose = setup["verbose"]

base_path = os.getcwd()
input_dir_path = base_path + "/shapes/"
pTable = PrettyTable()
column_names = ["Option", "Setting"]
pTable.add_column(column_names[0], ["Output Folder","Analysis","Year","Channels","Variable","Signal Processes","Mass Shifts","Auto Rebin","AutoMC","Verbose"])
pTable.add_column(column_names[0], [output_folder,analysis,era_tag,channels,variable,sig_procs,mass_shifts,auto_rebin,use_automc,verbose])
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

def NegativeBins(p):
  '''Replaces negative bins in hists with 0'''
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

# Create an empty CombineHarvester instance
harvester = CombineHarvester()
for chn in channels:
  # Adding Data,Signal Processes and Background processes to the harvester instance
  harvester.AddObservations(['*'], [analysis], [era_tag], [chn], cats[chn])
  harvester.AddProcesses(['*'], [analysis], [era_tag], [chn], bkg_procs[chn], cats[chn], False)
  harvester.AddProcesses(mass_shifts, [analysis], [era_tag], [chn], sig_procs, cats[chn], True)

# Populating Observation, Process and Systematic entries in the harvester instance
for chn in channels:
   #filename = input_dir_path + era_tag + "/" + chn + "/" + variable + "_signal_" + chn + "_inclusive_" + era_tag + "_rebinned" + ".root"
   filename = input_dir_path + '2201/' + era_tag + "/" + chn + "/" + variable + "_" + chn + "_multicat_" + era_tag + ".root"
   print ">>>   file %s"%(filename)
   print(chn)
   harvester.cp().channel([chn]).process(bkg_procs[chn]).ExtractShapes(filename, "$BIN/$PROCESS", "$BIN/$PROCESS_$SYSTEMATIC")
   harvester.cp().channel([chn]).process(sig_procs).ExtractShapes(filename, "$BIN/$PROCESS$MASS_norm", "$BIN/$PROCESS$MASS_$SYSTEMATIC")

if(auto_rebin):
  rebin = AutoRebin()
  rebin.SetBinThreshold(100)
  rebin.SetBinUncertFraction(0.5)
  rebin.SetRebinMode(1)
  rebin.SetPerformRebin(True)
  rebin.SetVerbosity(1) 
  rebin.Rebin(harvester,harvester)

# Replacing negative bins
print(green("Removing NegativeBins"))
harvester.ForEachProc(NegativeBins)

workspace = RooWorkspace(analysis,analysis)
# RooVar
Mphi = RooRealVar("MH","Mass of H/h in GeV", 100., 300.)
Mphi.setConstant(True)

# MORPHING
print green(">>> morphing...")
BuildCMSHistFuncFactory(workspace, harvester, Mphi, "A60phi,A70phi,A80phi,A90phi,A100phi,A125phi,A140phi,A160phi")

workspace.writeToFile("workspace_py.root")

# EXTRACT PDFs
print green(">>> add workspace and extract pdf...")
harvester.AddWorkspace(workspace, False)
harvester.ExtractPdfs(harvester, analysis, "$BIN_$PROCESS_morph", "")  # Extract all processes (signal and bkg are named the same way)
harvester.ExtractData(analysis, "$BIN_data_obs")  # Extract the RooDataHist

if (use_automc):
   # Set the autoMCStats line (with -1 = no bbb uncertainties)
   # Set threshold to 0.3 to use Poisson PDF instead
   harvester.SetAutoMCStats(harvester, 0.3, 0, 1)


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
if (os.path.exists("{}/{}/cmb".format(output_folder,era_tag)) == False):
   os.system("mkdir {}/{}/cmb".format(output_folder,era_tag))
if (os.path.exists("{}/{}/cmb/common".format(output_folder,era_tag)) == False):
   os.system("mkdir {}/{}/cmb/common".format(output_folder,era_tag))
os.system("cp -r {}/{}/*/*/*.root {}/{}/cmb/common/".format(output_folder,era_tag,output_folder,era_tag))
os.system("cp -r {}/{}/*/*.txt {}/{}/cmb/".format(output_folder,era_tag,output_folder,era_tag))
os.system("mv workspace_py.root {}/{}/".format(output_folder,era_tag))



