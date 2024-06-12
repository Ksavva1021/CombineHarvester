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
parser.add_argument('-c', '--config', dest='config', type=str, default='config/run_combine_new_v2.yml', help="Output folder")
parser.add_argument('--model_dep', help= 'Run model dependent limits',  action='store_true')
parser.add_argument('--br', help= 'Run br fit',  action='store_true')
parser.add_argument('--cosbma', help= 'Run tanb-cosbma limits',  action='store_true')
parser.add_argument('--only_harvest', help= 'Only harvest txt datacards',  action='store_true')
parser.add_argument('--only_ws', help= 'Only run ws',  action='store_true')
parser.add_argument('--only_limit', help= 'Only run limit',  action='store_true')
parser.add_argument('--run', help= 'Run the harvesting, ws and limits',  action='store_true')
parser.add_argument('--collect', help= 'Collect the limits',  action='store_true')
parser.add_argument('--plot', help= 'Plot the limits',  action='store_true')
parser.add_argument('--rerun', help= 'Rerun broken limits',  action='store_true')


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
auto_rebin = setup["auto_rebin"]
use_automc = setup["auto_mc"]
verbose = setup["verbose"]
do_systematics = setup["do_systematics"]
systematics = setup["systematics"]
input_dir_path = setup["path"]

if args.model_dep:
  workspace_loop_masses = setup["phi_masses"]
else:
  workspace_loop_masses = setup["A_masses"]

cmssw_base = os.getcwd()


pTable = PrettyTable()
column_names = ["Option", "Setting"]
pTable.add_column(column_names[0], ["Output Folder","Analysis","Year","Channels","Variable","Auto Rebin","AutoMC","Verbose"])
pTable.add_column(column_names[0], [output_folder,analysis,era_tag,channels,variable,auto_rebin,use_automc,verbose])
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

def SetNegativeRates(p):
  print "Setting Rate For Negative Histograms"
  p.set_rate(p.rate()*-1.0)


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
  if len(frozen_POIs_SetToZero) > 1:
    if frozen_POIs_SetToZero[-1] == ",": frozen_POIs_SetToZero = frozen_POIs_SetToZero[:-1]
  if len(frozen_POIs) > 1:
    if frozen_POIs[-1] == ",": frozen_POIs = frozen_POIs[:-1]
  return frozen_POIs,frozen_POIs_SetToZero


po_ws = ""
split_higgs = "A"
other_higgs = "phi"
if args.model_dep:
  #po_ws = "--PO model_dependent --PO mphi[" + ','.join(setup['phi_masses']) + "] --PO mA[" + ','.join(setup['A_masses']) + "]"
  po_ws = "--PO model_dependent"
  #po_ws = "--PO phi_only_branching_ratio"
  if args.br:
    po_ws = "--PO branching_ratio"
  split_higgs = "phi"
  other_higgs = "A"


if args.run:

  ### Harvest datacards ###

  if args.only_harvest or not (args.only_ws or args.only_limit):
  
    for mass in workspace_loop_masses:  
      print("Processing {} mass:".format(split_higgs),mass)
      sig_procs = [split_higgs+mass]
      mass_shifts = setup[split_higgs+"_"+mass]
      if (os.path.exists("{}/{}/{}_{}".format(output_folder,era_tag,split_higgs,mass))):
        os.system("rm -r {}/{}/{}_{}".format(output_folder,era_tag,split_higgs,mass))
      
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
  #               harvester.cp().process(sig_procs).mass(mass_shifts).AddSyst(harvester,sysDef["name"] if "name" in sysDef else syst, sysDef["effect"], SystMap()(scaleFactor))
                  harvester.cp().process(sig_procs).AddSyst(harvester,sysDef["name"] if "name" in sysDef else syst, sysDef["effect"], SystMap()(scaleFactor))

            elif ("YEAR" not in syst):
              harvester.cp().process(sysDef["processes"]).channel(sysDef["channel"]).AddSyst(harvester,sysDef["name"] if "name" in sysDef else syst, sysDef["effect"], SystMap()(scaleFactor))
              if do_sig_procs:
  #               harvester.cp().process(sig_procs).mass(mass_shifts).channel(sysDef["channel"]).AddSyst(harvester,sysDef["name"] if "name" in sysDef else syst, sysDef["effect"], SystMap()(scaleFactor))
                harvester.cp().process(sig_procs).channel(sysDef["channel"]).AddSyst(harvester,sysDef["name"] if "name" in sysDef else syst, sysDef["effect"], SystMap()(scaleFactor))
      
            if "YEAR" in syst:
              for year in ["2016_preVFP","2016_postVFP","2017","2018"]:
      
                  name = sysDef["name"].replace("YEAR",year)
                  if ("all" in sysDef["channel"]):
                    harvester.cp().process(sysDef["processes"]).AddSyst(harvester,name, sysDef["effect"], SystMap()(scaleFactor))
                    if do_sig_procs:
  #                    harvester.cp().process(sig_procs).mass(mass_shifts).AddSyst(harvester,name, sysDef["effect"], SystMap()(scaleFactor))
                      harvester.cp().process(sig_procs).AddSyst(harvester,name, sysDef["effect"], SystMap()(scaleFactor))
      

                  else:
                    harvester.cp().process(sysDef["processes"]).channel(sysDef["channel"]).AddSyst(harvester,name, sysDef["effect"], SystMap()(scaleFactor))
                    if do_sig_procs:
  #                    harvester.cp().process(sig_procs).mass(mass_shifts).channel(sysDef["channel"]).AddSyst(harvester,name, sysDef["effect"], SystMap()(scaleFactor))
                      harvester.cp().process(sig_procs).channel(sysDef["channel"]).AddSyst(harvester,name, sysDef["effect"], SystMap()(scaleFactor))

        
        # I guess here you need to just load in the uncertainties for only a single A at a time
        if args.model_dep or args.cosbma:
            with open("input/4tau_xs_uncerts.json") as jsonfile: sig_xs = json.load(jsonfile)
            for k,v in sig_xs.items():
              phi_mass = k.split("phi")[1].split("A")[0]
              A_mass = k.split("A")[1].split("To")[0]
              if phi_mass == mass:
                for A in setup["phi_"+mass]:
                  if A_mass == A:
                    for syst, lnN in v.items():
                      harvester.cp().process(["phi{}".format(phi_mass)]).mass([str(A_mass)]).AddSyst(harvester,str(syst)+"_yield","lnN",SystMap()([lnN["Down"],lnN["Up"]]))
      
      # Populating Observation, Process and Systematic entries in the harvester instance
      for chn in channels:
        #filename = input_dir_path + '/' + era_tag + "/" + chn + "/" + variable + "_" + chn + "_multicat_" + era_tag + ".root"
        filename = input_dir_path + "/" + chn + "/" + variable + "_" + chn + "_multicat_" + era_tag + ".root"
        print ">>>   file %s"%(filename)
        print(chn)
        harvester.cp().channel([chn]).process([i for j in bkg_procs[chn] for i in j]).ExtractShapes(filename, "$BIN/$PROCESS", "$BIN/$PROCESS_$SYSTEMATIC")
        if not (args.model_dep or args.cosbma):
          #harvester.cp().channel([chn]).process(sig_procs).ExtractShapes(filename, "$BIN/$PROCESSphi$MASS_norm", "$BIN/$PROCESSphi$MASS_norm_$SYSTEMATIC")
          harvester.cp().channel([chn]).process(sig_procs).ExtractShapes(filename, "$BIN/$PROCESSphi$MASS", "$BIN/$PROCESSphi$MASS_$SYSTEMATIC")
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
      harvester.ForEachProc(NegativeBins)
      
      if not (args.model_dep or args.cosbma):
        harvester.cp().process(sig_procs).AddSyst(harvester, "rate_model_ind","rateParam",SystMap()(0.01))
        harvester.GetParameter("rate_model_ind").set_frozen(1)
  
      harvester.PrintAll()
      
      workspace = RooWorkspace(analysis,analysis)
    
      # RooVar
      Mphi = RooRealVar("MH","Mass of H/h in GeV", float(mass_shifts[0]), float(mass_shifts[-1]))
      Mphi.setConstant(True)
      
      # MORPHING
      print green(">>> morphing...")
      print(workspace, harvester, Mphi, split_higgs+mass)
      BuildCMSHistFuncFactory(workspace, harvester, Mphi, split_higgs+mass)

      workspace.writeToFile("workspace_py.root")
      
      # EXTRACT PDFs
      print green(">>> add workspace and extract pdf...")
      harvester.AddWorkspace(workspace, False)
      harvester.ExtractPdfs(harvester, analysis, "$BIN_$PROCESS_morph", "")  # Extract all processes (signal and bkg are named the same way)
      harvester.ExtractData(analysis, "$BIN_data_obs")  # Extract the RooDataHist
      
      # Group systematics
      ff_sideband = [
        "mmtt_iso_0f_3","mmtt_iso_0f_4","mmtt_iso_1f_3","mmtt_iso_1f_4",
        "eett_iso_0f_3","eett_iso_0f_4","eett_iso_1f_3","eett_iso_1f_4",
        "emtt_iso_0f_3","emtt_iso_0f_4","emtt_iso_1f_3","emtt_iso_1f_4",
        "mttt_iso_0f_2","mttt_iso_0f_3","mttt_iso_0f_4",
        "mttt_iso_1f1p_2","mttt_iso_1f1p_3","mttt_iso_1f1p_4",
        "mttt_iso_1p1f_2","mttt_iso_1p1f_3","mttt_iso_1p1f_4",
        "mttt_iso_2f_2","mttt_iso_2f_3","mttt_iso_2f_4",
        "ettt_iso_0f_2","ettt_iso_0f_3","ettt_iso_0f_4",
        "ettt_iso_1f1p_2","ettt_iso_1f1p_3","ettt_iso_1f1p_4",
        "ettt_iso_1p1f_2","ettt_iso_1p1f_3","ettt_iso_1p1f_4",
        "ettt_iso_2f_2","ettt_iso_2f_3","ettt_iso_2f_4",
        "ttt_iso_0f_1","ttt_iso_0f_2","ttt_iso_0f_3",
        "ttt_iso_1f1p_1","ttt_iso_1f1p_2","ttt_iso_1f1p_3","ttt_iso_1f1p_4",
        "ttt_iso_1p1f_1","ttt_iso_1p1f_2","ttt_iso_1p1f_3","ttt_iso_1p1f_4",
        "ttt_iso_2f_1","ttt_iso_2f_2","ttt_iso_2f_3","ttt_iso_2f_4",
        ]
      harvester.AddDatacardLineAtEnd("ff_sideband group = {}".format(" ".join(ff_sideband)))

      ff_non_closure = ["mmtt_non_closure","eett_non_closure","emtt_non_closure","mttt_non_closure","ettt_non_closure","ttt_non_closure"]
      harvester.AddDatacardLineAtEnd("ff_non_closure group = {}".format(" ".join(ff_non_closure)))

      ff_subtraction_non_closure = [
        "mmtt_subtract_pass_non_closure","eett_subtract_pass_non_closure","emtt_subtract_pass_non_closure","mttt_subtract_pass_non_closure","ettt_subtract_pass_non_closure","ttt_subtract_pass_non_closure",
        "mmtt_subtract_fail_non_closure","eett_subtract_fail_non_closure","emtt_subtract_fail_non_closure","mttt_subtract_fail_non_closure","ettt_subtract_fail_non_closure","ttt_subtract_fail_non_closure"
        ]
      harvester.AddDatacardLineAtEnd("ff_subtraction_non_closure group = {}".format(" ".join(ff_subtraction_non_closure)))

      ff_subtraction_yield = ["mmtt_subtraction","eett_subtraction","emtt_subtraction","mttt_subtraction","ettt_subtraction","ttt_subtraction"]
      harvester.AddDatacardLineAtEnd("ff_subtraction_yield group = {}".format(" ".join(ff_subtraction_yield)))

      tau_ID = [
        "syst_tau_id_highpt",
        "syst_tau_id_syst_2016_preVFP","syst_tau_id_syst_2016_postVFP","syst_tau_id_syst_2017","syst_tau_id_syst_2018",
        "syst_tau_id_syst_all_eras",
        "syst_tau_id_syst_dm02016_preVFP_DM","syst_tau_id_syst_dm02016_postVFP_DM","syst_tau_id_syst_dm02017_DM","syst_tau_id_syst_dm02018_DM",
        "syst_tau_id_syst_dm12016_preVFP_DM","syst_tau_id_syst_dm12016_postVFP_DM","syst_tau_id_syst_dm12017_DM","syst_tau_id_syst_dm12018_DM",
        "syst_tau_id_syst_dm102016_preVFP_DM","syst_tau_id_syst_dm102016_postVFP_DM","syst_tau_id_syst_dm102017_DM","syst_tau_id_syst_dm102018_DM",
        "syst_tau_id_syst_dm112016_preVFP_DM","syst_tau_id_syst_dm112016_postVFP_DM","syst_tau_id_syst_dm112017_DM","syst_tau_id_syst_dm112018_DM",
        "syst_tau_id_uncert0_DM02016_preVFP","syst_tau_id_uncert0_DM02016_postVFP","syst_tau_id_uncert0_DM02017","syst_tau_id_uncert0_DM02018",
        "syst_tau_id_uncert0_DM12016_preVFP","syst_tau_id_uncert0_DM12016_postVFP","syst_tau_id_uncert0_DM12017","syst_tau_id_uncert0_DM12018",
        "syst_tau_id_uncert0_DM102016_preVFP","syst_tau_id_uncert0_DM102016_postVFP","syst_tau_id_uncert0_DM102017","syst_tau_id_uncert0_DM102018",
        "syst_tau_id_uncert0_DM112016_preVFP","syst_tau_id_uncert0_DM112016_postVFP","syst_tau_id_uncert0_DM112017","syst_tau_id_uncert0_DM112018",
        "syst_tau_id_uncert1_DM02016_preVFP","syst_tau_id_uncert1_DM02016_postVFP","syst_tau_id_uncert1_DM02017","syst_tau_id_uncert1_DM02018",
        "syst_tau_id_uncert1_DM12016_preVFP","syst_tau_id_uncert1_DM12016_postVFP","syst_tau_id_uncert1_DM12017","syst_tau_id_uncert1_DM12018",
        "syst_tau_id_uncert1_DM102016_preVFP","syst_tau_id_uncert1_DM102016_postVFP","syst_tau_id_uncert1_DM102017","syst_tau_id_uncert1_DM102018",
        "syst_tau_id_uncert1_DM112016_preVFP","syst_tau_id_uncert1_DM112016_postVFP","syst_tau_id_uncert1_DM112017","syst_tau_id_uncert1_DM112018",
        ]
      harvester.AddDatacardLineAtEnd("tau_ID group = {}".format(" ".join(tau_ID)))

      k_factor = [
        "syst_qqZZ_k_factor",
        "syst_ggZZ_k_factor",
      ]
      harvester.AddDatacardLineAtEnd("k_factor group = {}".format(" ".join(k_factor)))

      electron_ID = [
        "syst_electron_id",
      ]
      harvester.AddDatacardLineAtEnd("electron_ID group = {}".format(" ".join(electron_ID)))

      muon_ID = [
        "syst_muon_id",
      ]
      #harvester.AddDatacardLineAtEnd("muon_ID group = {}".format(" ".join(muon_ID)))

      tau_trigger = [
        "syst_doubletau_trg",
      ]
      harvester.AddDatacardLineAtEnd("tau_trigger group = {}".format(" ".join(tau_trigger)))

      electron_trigger = [
        "syst_singlee_trg",
      ]
      harvester.AddDatacardLineAtEnd("electron_trigger group = {}".format(" ".join(electron_trigger)))

      muon_trigger = [
        "syst_singlem_trg",
      ]
      harvester.AddDatacardLineAtEnd("muon_trigger group = {}".format(" ".join(muon_trigger)))

      tau_es = [
        "syst_1prong",
        "syst_1prong1pizero",
        "syst_3prong",
        "syst_3prong1pizero",
      ]
      harvester.AddDatacardLineAtEnd("tau_es group = {}".format(" ".join(tau_es)))

      electron_es = [
        "syst_electron_scale",
      ]
      harvester.AddDatacardLineAtEnd("electron_es group = {}".format(" ".join(electron_es)))

      jetmet = [
        "syst_jet_res",
        "syst_Absolute",
        "syst_Absolute_2016_preVFP","syst_Absolute_2016_postVFP","syst_Absolute_2017","syst_Absolute_2018",
        "syst_BBEC1",
        "syst_BBEC1_2016_preVFP","syst_BBEC1_2016_postVFP","syst_BBEC1_2017","syst_BBEC1_2018",
        "syst_EC2",
        "syst_EC2_2016_preVFP","syst_EC2_2016_postVFP","syst_EC2_2017","syst_EC2_2018",
        "syst_FlavorQCD",
        "syst_HF",
        "syst_HF_2016_preVFP","syst_HF_2016_postVFP","syst_HF_2017","syst_HF_2018",
        "syst_RelativeBal",
        "syst_RelativeSample_2016_preVFP","syst_RelativeSample_2016_postVFP","syst_RelativeSample_2017","syst_RelativeSample_2018",
        "syst_met_unclustered",
      ]
      harvester.AddDatacardLineAtEnd("jetmet group = {}".format(" ".join(jetmet)))

      lumi = [
        "Lumi",
      ]
      harvester.AddDatacardLineAtEnd("lumi group = {}".format(" ".join(lumi)))

      btag = [
        "syst_eff_b",
        "syst_mistag_b",
      ]
      harvester.AddDatacardLineAtEnd("btag group = {}".format(" ".join(btag)))

      prefiring = [
        "syst_prefiring",
      ]
      harvester.AddDatacardLineAtEnd("prefiring group = {}".format(" ".join(prefiring)))


      if (use_automc):
        # Set the autoMCStats line (with -1 = no bbb uncertainties)
        # Set threshold to 0.3 to use Poisson PDF instead
        harvester.SetAutoMCStats(harvester, 10.0, 0, 1)
        #harvester.SetAutoMCStats(harvester, 0.)

      
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
      datacardtxt  = "%s/%s/%s_%s/$BIN/$BIN.txt"%(output_folder,era_tag,split_higgs,mass)
      datacardroot = "%s/%s/%s_%s/$BIN/common/$BIN_input_%s.root"%(output_folder,era_tag,split_higgs,mass,era_tag)
      writer = CardWriter(datacardtxt,datacardroot)
      writer.SetVerbosity(1)
      writer.SetWildcardMasses([ ])
      writer.WriteCards("cmb", harvester)
      
      # You have to delete the workspace as otherwise you will get a memory management seg val (You can avoid this if you use a newer version of PyROOT or if you run the file within a function)
      workspace.Delete()
      
      # Relocating outputs to ease further processing
      if (os.path.exists("{}/{}/{}_{}/cmb".format(output_folder,era_tag,split_higgs,mass))):
        os.system("rm -r {}/{}/{}_{}/cmb".format(output_folder,era_tag,split_higgs,mass))
      os.system("mkdir {}/{}/{}_{}/cmb".format(output_folder,era_tag,split_higgs,mass))
      
      if (os.path.exists("{}/{}/{}_{}/cmb/common".format(output_folder,era_tag,split_higgs,mass))):
        os.system("rm -r {}/{}/{}_{}/cmb/common".format(output_folder,era_tag,split_higgs,mass))
      os.system("mkdir {}/{}/{}_{}/cmb/common".format(output_folder,era_tag,split_higgs,mass))
      
      os.system("cp -r {}/{}/{}_{}/*/*/*.root {}/{}/{}_{}/cmb/common/".format(output_folder,era_tag,split_higgs,mass,output_folder,era_tag,split_higgs,mass))
      os.system("cp -r {}/{}/{}_{}/*/*.txt {}/{}/{}_{}/cmb/".format(output_folder,era_tag,split_higgs,mass,output_folder,era_tag,split_higgs,mass))
      os.system("mv workspace_py.root {}/{}/{}_{}/".format(output_folder,era_tag,split_higgs,mass))
  
  ### Run Workspace ###
  if args.only_ws or not (args.only_harvest or args.only_limit):
    # Build the workspaces
    log_workspace = "workspace" + datetime.today().strftime('%d%m')
    for mass in workspace_loop_masses:
      print("Building workspace for {} mass:".format(split_higgs),mass)
      if (os.path.exists("%(cmssw_base)s/%(output_folder)s/%(era_tag)s/%(split_higgs)s_%(mass)s/logs" %vars()) == False):
        os.mkdir("%(cmssw_base)s/%(output_folder)s/%(era_tag)s/%(split_higgs)s_%(mass)s/logs"%vars())
    
      po_mass = "--PO m{}[{}]".format(split_higgs, mass)
      os.system("python %(cmssw_base)s/../CombineTools/scripts/combineTool.py -M T2W -o ws.root %(po_mass)s %(po_ws)s -P CombineHarvester.Combine4tau.X2HDM_v2:X2HDM -i %(cmssw_base)s/%(output_folder)s/%(era_tag)s/%(split_higgs)s_%(mass)s/cmb/ --parallel 4 --cores 2 | tee -a %(cmssw_base)s/%(output_folder)s/%(era_tag)s/%(split_higgs)s_%(mass)s/logs/%(log_workspace)s_cmb.txt" % vars())
      # Make Directories for Limits
      if (os.path.exists("%(cmssw_base)s/%(output_folder)s/%(era_tag)s/%(split_higgs)s_%(mass)s/cmb/limits" %vars()) == False):
        os.mkdir("%(cmssw_base)s/%(output_folder)s/%(era_tag)s/%(split_higgs)s_%(mass)s/cmb/limits"%vars())

  ### Run Limits ###
  ## Change for model DEP
  if (args.only_limit) or not (args.only_harvest or args.only_ws):

    for m in workspace_loop_masses:
      if not args.model_dep:
        POI = "r_"+split_higgs+m
      else:
        POI = "tanb"
        if args.br:
          POI = "br"
      method = "-M AsymptoticLimits"
      #blinding = "--run expected"
      blinding = ""
      log_limits = "AL" + datetime.today().strftime('%d%m')
      add_cond = ""
      #if not (args.model_dep or args.cosbma): add_cond += " --rMin 0 --rMax 0.02"
      name_ext = ""
      
      #grid_str = ','.join(setup[split_higgs+"_"+m])
      grid_str = ','.join(setup["morphed_"+split_higgs+"_"+m])
      print(grid_str)
      #--setParameterRanges tanb=1,90

      #print("pushd %(cmssw_base)s/%(output_folder)s/%(era_tag)s/%(split_higgs)s_%(m)s/cmb/limits; python %(cmssw_base)s/../CombineTools/scripts/combineTool.py %(method)s -m %(grid_str)s --redefineSignalPOIs %(POI)s -d %(cmssw_base)s/%(output_folder)s/%(era_tag)s/%(split_higgs)s_%(m)s/cmb/ws.root --X-rtd MINIMIZER_analytic --cminDefaultMinimizerStrategy 0 %(blinding)s  --job-mode SGE  --prefix-file ic --sub-opts \"-q hep.q -l h_rt=3:0:0\" --task-name %(split_higgs)s%(m)s%(name_ext)s%(add_cond)s | tee -a %(cmssw_base)s/%(output_folder)s/%(era_tag)s/%(split_higgs)s_%(m)s/logs/%(log_limits)s_cmb_m%(split_higgs)s%(m)s%(other_higgs)s.txt; popd" %vars())
      os.system("pushd %(cmssw_base)s/%(output_folder)s/%(era_tag)s/%(split_higgs)s_%(m)s/cmb/limits; python %(cmssw_base)s/../CombineTools/scripts/combineTool.py %(method)s -m %(grid_str)s --redefineSignalPOIs %(POI)s -d %(cmssw_base)s/%(output_folder)s/%(era_tag)s/%(split_higgs)s_%(m)s/cmb/ws.root --X-rtd MINIMIZER_analytic --cminDefaultMinimizerStrategy 0 %(blinding)s  --job-mode SGE  --prefix-file ic --sub-opts \"-q hep.q -l h_rt=3:0:0\" --task-name %(split_higgs)s%(m)s%(name_ext)s%(add_cond)s --setParameterRanges tanb=1,90 | tee -a %(cmssw_base)s/%(output_folder)s/%(era_tag)s/%(split_higgs)s_%(m)s/logs/%(log_limits)s_cmb_m%(split_higgs)s%(m)s%(other_higgs)s.txt; popd" %vars())


if args.collect:
  for m in workspace_loop_masses:
    os.system("python %(cmssw_base)s/../CombineTools/scripts/combineTool.py -M CollectLimits %(cmssw_base)s/%(output_folder)s/%(era_tag)s/%(split_higgs)s_%(m)s/cmb/limits/higgsCombine.Test.AsymptoticLimits.mH*.root --use-dirs -o %(cmssw_base)s/%(output_folder)s/%(era_tag)s/%(split_higgs)s_%(m)s/cmb/limits/limit.json" %vars())

    if args.model_dep and not args.br:
      # Open jsons
      limit_file = "%(cmssw_base)s/%(output_folder)s/%(era_tag)s/%(split_higgs)s_%(m)s/cmb/limits/limit_limits.json" % vars()
      if not os.path.isfile(limit_file): continue

      with open(limit_file, 'r') as file:
        data_dict = json.load(file)

      for k, v in data_dict.items():

        # check all keys are there and they are less than tanb=90
        keys_all_there = True
        for key in ["obs","exp-2","exp-1","exp0","exp+1","exp+2"]:
          if not key in v.keys():
            keys_all_there = False
          elif v[key] > 90.0:
            v[key] = 200.0

        # This means no limit found so set to maxixum
        if not keys_all_there:
          data_dict[k] = {u"obs":200.0, u"exp-2":200.0, u"exp-1":200.0, u"exp0":200.0, u"exp+1":200.0, u"exp+2":200.0}

        # Rerun ones that gave broken limits with smaller range  
        allowed_sigma = 3.0
        lower_bound = data_dict[k]["exp0"] - (allowed_sigma/2.0)*(data_dict[k]["exp0"]-data_dict[k]["exp-2"])
        upper_bound = data_dict[k]["exp0"] + (allowed_sigma/2.0)*(-data_dict[k]["exp0"]+data_dict[k]["exp+2"])
        if args.rerun:
          if (data_dict[k]["obs"] < lower_bound) or (data_dict[k]["obs"] > upper_bound):
            min_tanb = str(lower_bound)
            max_tanb = str(upper_bound)
            POI = "tanb"
            method = "-M AsymptoticLimits"
            blinding = ""
            name_ext = ""
            add_cond = ""
            log_limits = "AL" + datetime.today().strftime('%d%m')
            str_k = str(int(float(k)))
            os.system("pushd %(cmssw_base)s/%(output_folder)s/%(era_tag)s/%(split_higgs)s_%(m)s/cmb/limits; python %(cmssw_base)s/../CombineTools/scripts/combineTool.py %(method)s -m %(str_k)s --redefineSignalPOIs %(POI)s -d %(cmssw_base)s/%(output_folder)s/%(era_tag)s/%(split_higgs)s_%(m)s/cmb/ws.root --X-rtd MINIMIZER_analytic --cminDefaultMinimizerStrategy 0 %(blinding)s  --job-mode SGE  --prefix-file ic --sub-opts \"-q hep.q -l h_rt=3:0:0\" --task-name %(split_higgs)s%(m)s%(name_ext)s%(add_cond)s_A%(str_k)s_correction --setParameterRanges tanb=1,10 | tee -a %(cmssw_base)s/%(output_folder)s/%(era_tag)s/%(split_higgs)s_%(m)s/logs/%(log_limits)s_cmb_m%(split_higgs)s%(m)s%(other_higgs)s.txt; popd" %vars())

        else:
          # Write to new dictionary to file
          with open(limit_file, 'w') as file:
            json.dump(data_dict, file, indent=4)

    if args.br:
      # Open jsons
      limit_file = "%(cmssw_base)s/%(output_folder)s/%(era_tag)s/%(split_higgs)s_%(m)s/cmb/limits/limit_limits.json" % vars()
      if not os.path.isfile(limit_file): continue
      with open(limit_file, 'r') as file:
        data_dict = json.load(file)
      with open(limit_file.replace(".json","_br.json"), 'w') as file:
        json.dump(data_dict, file, indent=4)

      # Open tanb br root file
      br_file = ROOT.TFile("input/typeX_BRs.root")
      hist_name = "brs_mphi{}p0".format(str(m))
      br_hist = br_file.Get(hist_name)
      if not br_hist: continue

      tanb_limits = {}
      for k, v in data_dict.items():

        tanb_limits[k] = {}

        # 2D interpolation
        from scipy.interpolate import interp2d
        mA_bin = br_hist.GetXaxis().FindBin(float(k))
        if float(k) > br_hist.GetXaxis().GetBinCenter(mA_bin):
          x1_bin = mA_bin*1
          x2_bin = mA_bin + 1
        else:
          x1_bin = mA_bin - 1
          x2_bin = mA_bin*1

        x1 = br_hist.GetXaxis().GetBinCenter(x1_bin)
        x2 = br_hist.GetXaxis().GetBinCenter(x2_bin)

        for v1, v2 in v.items():
          done_x1 = False
          done_x2 = False
          for i in range(0,br_hist.GetNbinsY()):
            bin_below_x1 = br_hist.GetBinContent(x1_bin,i)
            bin_above_x1 = br_hist.GetBinContent(x1_bin,i+1)
            if bin_below_x1 <= v2 and bin_above_x1 > v2 and not done_x1:
              y1_x1 = br_hist.GetYaxis().GetBinCenter(i)
              y2_x1 = br_hist.GetYaxis().GetBinCenter(i+1)
              f11 = br_hist.GetBinContent(x1_bin, i)
              f12 = br_hist.GetBinContent(x1_bin, i+1)
              done_x1 = True
            bin_below_x2 = br_hist.GetBinContent(x2_bin,i)
            bin_above_x2 = br_hist.GetBinContent(x2_bin,i+1)
            if bin_below_x2 <= v2 and bin_above_x2 > v2 and not done_x2:
              y1_x2 = br_hist.GetYaxis().GetBinCenter(i)
              y2_x2 = br_hist.GetYaxis().GetBinCenter(i+1)
              f21 = br_hist.GetBinContent(x2_bin, i)
              f22 = br_hist.GetBinContent(x2_bin, i+1)
              done_x2 = True
          #print(k, v1)
          #print([x1,x1,x2,x2], [y1_x1,y2_x1,y1_x2,y2_x2], [f11,f12,f21,f22])
          if done_x1 and done_x2:
            f = interp2d([x1,x1,x2,x2], [f11,f12,f21,f22], [y1_x1,y2_x1,y1_x2,y2_x2], kind='linear')
            tanb_limits[k][v1] = f(float(k),float(v2))[0]
          else:
            tanb_limits[k][v1] = 200.0

      br_file.Close()

      with open(limit_file, 'w') as file:
        json.dump(tanb_limits, file, indent=4)

if args.plot:
  if not args.model_dep:
    os.system("mkdir mi_plots")
    os.system("python scripts/plotting/plot_all_model_independent_limits.py --folder=%(output_folder)s" % vars()) 
    os.system("python scripts/plotting/plot_model_independent_2d_new.py --folder=%(output_folder)s --logx --logy --logz" % vars())
  else:

    plot_dir = "model_dependent_2d"
    if not os.path.isdir(plot_dir): os.system("mkdir %(plot_dir)s"  % vars())


    ##os.system('python scripts/plotting/plot_model_dependent_limits_2d_new.py --output="%(plot_dir)s/md_2d_no_interp" --no-interp --z-range=1,200 --title-left="Type X 2HDM Alignment Scenario" --logz --mA="40,45,50,55,60,65,70,75,80,85,90,95,100,105,110,115,120,125,130,135,140,145,150,155,160,170,180,190,200,210,220,230,240,250,275,300,325,350,375,400,500,600" --mphi="60,70,80,90,100,110,125,140,160,180,200,250,300,400" --logx --logy --points=100 --file="%(output_folder)s/%(era_tag)s/phi___m__/cmb/limits/limit_limits.json"' % vars())
    os.system('python scripts/plotting/plot_model_dependent_limits_2d_contour_new.py --output="%(plot_dir)s/md_2d_contour" --title-left="Type X 2HDM Alignment Scenario"  --points=1000 --file="%(output_folder)s/%(era_tag)s/phi___m__/cmb/limits/limit_limits.json"' % vars())
    os.system('python scripts/plotting/plot_model_dependent_limits_2d_contour_new.py --output="%(plot_dir)s/md_2d_hb_contour" --show-complete-exclusion --title-left="Type X 2HDM Alignment Scenario" --points=1000 --file="%(output_folder)s/%(era_tag)s/phi___m__/cmb/limits/limit_limits.json"' % vars())
    os.system('python scripts/plotting/plot_model_dependent_limits_2d_contour_new.py --output="%(plot_dir)s/md_2d_gm2_contour" --show-allowed-region --title-left="Type X 2HDM Alignment Scenario" --points=1000 --file="%(output_folder)s/%(era_tag)s/phi___m__/cmb/limits/limit_limits.json"' % vars())
    os.system('python scripts/plotting/plot_model_dependent_limits_2d_contour_new.py --output="%(plot_dir)s/md_2d_hb_gm2_contour" --show-complete-exclusion --show-allowed-region --title-left="Type X 2HDM Alignment Scenario" --points=1000 --file="%(output_folder)s/%(era_tag)s/phi___m__/cmb/limits/limit_limits.json"' % vars())


    '''
    os.system('python scripts/plotting/plot_model_dependent_limits_2d_new.py --output="%(plot_dir)s/md_2d" --z-range=1,200 --title-left="Type X 2HDM Alignment Scenario" --logz --mA="40,45,50,55,60,65,70,75,80,85,90,95,100,105,110,115,120,125,130,135,140,145,150,155,160,170,180,190,200,210,220,230,240,250,275,300,325,350,375,400,500,600" --mphi="60,70,80,90,100,110,125,140,160,180,200,250,300,400" --logx --logy --points=100 --file="%(output_folder)s/%(era_tag)s/phi___m__/cmb/limits/limit_limits.json"' % vars())
    os.system('python scripts/plotting/plot_model_dependent_limits_2d_new.py --output="%(plot_dir)s/md_2d_hb" --show-complete-exclusion --z-range=1,200 --title-left="Type X 2HDM Alignment Scenario" --logz --mA="40,45,50,55,60,65,70,75,80,85,90,95,100,105,110,115,120,125,130,135,140,145,150,155,160,170,180,190,200,210,220,230,240,250,275,300,325,350,375,400,500,600" --mphi="60,70,80,90,100,110,125,140,160,180,200,250,300,400" --logx --logy --points=100 --file="%(output_folder)s/%(era_tag)s/phi___m__/cmb/limits/limit_limits.json"' % vars())
    os.system('python scripts/plotting/plot_model_dependent_limits_2d_new.py --output="%(plot_dir)s/md_2d_gm2" --show-allowed-region --z-range=1,200 --title-left="Type X 2HDM Alignment Scenario" --logz --mA="40,45,50,55,60,65,70,75,80,85,90,95,100,105,110,115,120,125,130,135,140,145,150,155,160,170,180,190,200,210,220,230,240,250,275,300,325,350,375,400,500,600" --mphi="60,70,80,90,100,110,125,140,160,180,200,250,300,400" --logx --logy --points=100 --file="%(output_folder)s/%(era_tag)s/phi___m__/cmb/limits/limit_limits.json"' % vars())
    os.system('python scripts/plotting/plot_model_dependent_limits_2d_new.py --output="%(plot_dir)s/md_2d_hb_gm2" --show-complete-exclusion --z-range=1,200 --show-allowed-region --title-left="Type X 2HDM Alignment Scenario" --logz --mA="40,45,50,55,60,65,70,75,80,85,90,95,100,105,110,115,120,125,130,135,140,145,150,155,160,170,180,190,200,210,220,230,240,250,275,300,325,350,375,400,500,600" --mphi="60,70,80,90,100,110,125,140,160,180,200,250,300,400" --logx --logy --points=100 --file="%(output_folder)s/%(era_tag)s/phi___m__/cmb/limits/limit_limits.json"' % vars())

    os.system('python scripts/plotting/plot_model_dependent_limits_2d_new.py --output="%(plot_dir)s/md_2d_gm2_cont" --add-contour --show-allowed-region --z-range=1,200 --title-left="Type X 2HDM Alignment Scenario" --logz --mA="40,45,50,55,60,65,70,75,80,85,90,95,100,105,110,115,120,125,130,135,140,145,150,155,160,170,180,190,200,210,220,230,240,250,275,300,325,350,375,400,500,600" --mphi="60,70,80,90,100,110,125,140,160,180,200,250,300,400" --logx --logy --points=100 --file="%(output_folder)s/%(era_tag)s/phi___m__/cmb/limits/limit_limits.json"' % vars())
    os.system('python scripts/plotting/plot_model_dependent_limits_2d_new.py --output="%(plot_dir)s/md_2d_hb_gm2_cont" --add-contour --show-complete-exclusion --z-range=1,200 --show-allowed-region --title-left="Type X 2HDM Alignment Scenario" --logz --mA="40,45,50,55,60,65,70,75,80,85,90,95,100,105,110,115,120,125,130,135,140,145,150,155,160,170,180,190,200,210,220,230,240,250,275,300,325,350,375,400,500,600" --mphi="60,70,80,90,100,110,125,140,160,180,200,250,300,400" --logx --logy --points=100 --file="%(output_folder)s/%(era_tag)s/phi___m__/cmb/limits/limit_limits.json"' % vars())
    '''

    for m in setup["phi_masses"]:

      if m == "800": continue

      # Make standard plots
      plot_dir = "model_dependent_with_higgs_tools"
      if not os.path.isdir(plot_dir): os.system("mkdir %(plot_dir)s" % vars())
      os.system("python scripts/plotting/plot_model_dependent_limits.py %(output_folder)s/%(era_tag)s/phi_%(m)s/cmb/limits/limit_limits.json --excluded-mass=%(m)s --logy --scenario-label=\"m_{#phi} = %(m)s GeV\" --output=\"%(plot_dir)s/md_mphi%(m)s_hb\" --title-left=\"Type X 2HDM Alignment Scenario\" --cms-sub=\"Supplementary\" --y-range=1,200" % vars())
      plot_dir = "model_dependent"
      if not os.path.isdir(plot_dir): os.system("mkdir %(plot_dir)s" % vars())
      os.system("python scripts/plotting/plot_model_dependent_limits.py %(output_folder)s/%(era_tag)s/phi_%(m)s/cmb/limits/limit_limits.json --logy --scenario-label=\"m_{#phi} = %(m)s GeV\" --output=\"%(plot_dir)s/md_mphi%(m)s\" --title-left=\"Type X 2HDM Alignment Scenario\" --cms-sub=\"Supplementary\" --y-range=1,200" % vars())

      # Make split plots
      box_allowed = None
      if float(m) >= 130 and float(m) <= 245:
        box_allowed = "(62.95,90.53),(153.14,200.0),(87.14,200.0),(62.95,146.34)"
      elif float(m) >= 100 and float(m) <= 120:
        box_allowed = "(72.04,118.03),(110.66,200.0),(72.04,200.0)"
      if box_allowed is not None:
        plot_dir = "model_dependent_with_higgs_tools_and_gm2"
        if not os.path.isdir(plot_dir): os.system("mkdir %(plot_dir)s" % vars())
        os.system("python scripts/plotting/plot_model_dependent_limits_split.py %(output_folder)s/%(era_tag)s/phi_%(m)s/cmb/limits/limit_limits.json --excluded-mass=%(m)s --logy --scenario-label=\"m_{#phi} = %(m)s GeV\" --output=\"%(plot_dir)s/md_mphi%(m)s_hb_gm2\" --title-left=\"Type X 2HDM Alignment Scenario\" --cms-sub=\"\" --box-allowed=\"%(box_allowed)s\"" % vars())
        plot_dir = "model_dependent_with_gm2"
        if not os.path.isdir(plot_dir): os.system("mkdir %(plot_dir)s" % vars())
        os.system("python scripts/plotting/plot_model_dependent_limits_split.py %(output_folder)s/%(era_tag)s/phi_%(m)s/cmb/limits/limit_limits.json --logy --scenario-label=\"m_{#phi} = %(m)s GeV\" --output=\"%(plot_dir)s/md_mphi%(m)s_gm2\" --title-left=\"Type X 2HDM Alignment Scenario\" --cms-sub=\"\" --box-allowed=\"%(box_allowed)s\"" % vars())
