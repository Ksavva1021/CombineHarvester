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

def green(string,**kwargs):
    return kwargs.get('pre',"")+"\x1b[0;32;40m%s\033[0m"%string

#Define program options

output_folder = "output"
analysis = "X2HDM"
output_folder = output_folder + "_" + analysis + "_" + datetime.today().strftime('%d%m')
base_path = os. getcwd() + "/shapes/" 
era_tag = "all"
channel = "all"
category = "all"
variable = "mvis_min_sum_dR_1"
auto_rebin = False
use_automc = True
verbose = False

input_dir={}
if channel == "all":
  chns = ["mmtt", "emtt", "ettt","mttt","tttt","eett"] 
else:
  chns = ["{}".format(channel)]
bkg_procs = {}
bkgs = ["VVJF","VVLF","VVR","VVV","WGam","WJF","WLF","WR","ZJF","ZLF","ZR","jetFakes"]
cats = {}
for chn in chns:
  input_dir["{}".format(chn)] = base_path + era_tag + "/" + chn + "/"
  bkg_procs["{}".format(chn)] = bkgs
  cats["{}".format(chn)] = [(1,"{}_inclusive".format(chn))]

mass_shifts = ["100","110","125","140","160","180","200","250","300"]
sig_procs = ["A60phi","A70phi","A80phi","A90phi","A100phi","A125phi","A140phi","A160phi"]


harvester = CombineHarvester()
for chn in chns:
  harvester.AddObservations(['*'], [analysis], [era_tag], [chn], cats[chn])
  harvester.AddProcesses(['*'], [analysis], [era_tag], [chn], bkg_procs[chn], cats[chn], False)
  harvester.AddProcesses(mass_shifts, [analysis], [era_tag], [chn], sig_procs, cats[chn], True)

for chn in chns:
   filename = base_path + era_tag + "/" + chn + "/" + variable + "_signal_" + chn + "_inclusive_" + era_tag + "_rebinned" + ".root"
   print ">>>   file %s"%(filename)
   harvester.cp().channel([chn]).process(bkg_procs[chn]).ExtractShapes(filename, "$BIN/$PROCESS", "$BIN/$PROCESS_$SYSTEMATIC")
   harvester.cp().channel([chn]).process(sig_procs).ExtractShapes(filename, "$BIN/$PROCESS$MASS_norm", "$BIN/$PROCESS$MASS_$SYSTEMATIC")

def NegativeBins(p):
  hist = p.shape()
  has_negative = False
  for i in range(1,hist.GetNbinsX()+1):
    if hist.GetBinContent(i) < 0:
       has_negative = True
  if (has_negative):
    for i in range(1,hist.GetNbinsX()+1):
       if hist.GetBinContent(i) < 0:
          hist.SetBinContent(i,0)
  p.set_shape(hist,False) 

harvester.ForEachProc(NegativeBins)

workspace = RooWorkspace(analysis,analysis)
print analysis
Mphi = RooRealVar("MH","MH", 100., 300.)
Mphi.setConstant(True)

# MORPHING
print green(">>> morphing...")
BuildCMSHistFuncFactory(workspace, harvester, Mphi, "A60phi,A70phi,A80phi,A90phi,A100phi,A125phi,A140phi,A160phi")

#workspace.Print()
workspace.writeToFile("workspace_py.root")

# EXTRACT PDFs
print green(">>> add workspace and extract pdf...")
harvester.AddWorkspace(workspace, False)
harvester.ExtractPdfs(harvester, analysis, "$BIN_$PROCESS_morph", "")  # Extract all processes (signal and bkg are named the same way)
harvester.ExtractData(analysis, "$BIN_data_obs")  # Extract the RooDataHist

if (use_automc):
   harvester.SetAutoMCStats(harvester, 0.3, 0, 1) # Set the autoMCStats line (with -1 = no bbb uncertainties)

print green(">>> writing datacards...")
datacardtxt  = "%s/%s/$BIN/$BIN.txt"%(output_folder,era_tag)
datacardroot = "%s/%s/$BIN/common/$BIN_input_%s.root"%(output_folder,era_tag,era_tag)
writer = CardWriter(datacardtxt,datacardroot)
writer.SetVerbosity(1)
writer.SetWildcardMasses([ ])
writer.WriteCards("cmb", harvester)

workspace.Delete()

os.system("mkdir {}/{}/cmb".format(output_folder,era_tag))
os.system("mkdir {}/{}/cmb/common".format(output_folder,era_tag))
os.system("cp -r {}/{}/*/*/*.root {}/{}/cmb/common/".format(output_folder,era_tag,output_folder,era_tag))
os.system("cp -r {}/{}/*/*.txt {}/{}/cmb/".format(output_folder,era_tag,output_folder,era_tag))


