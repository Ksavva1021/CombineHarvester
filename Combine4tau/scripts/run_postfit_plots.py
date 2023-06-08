import os
import json
import copy
from argparse import ArgumentParser
import CombineHarvester.CombineTools.plotting as plotting
import ROOT
from collections import OrderedDict
from array import array

parser = ArgumentParser()
parser.add_argument('--step', type=str, default='all', help="step to run")
parser.add_argument('--name', type=str, default='postfit_plots', help="Name")
parser.add_argument('--fit', type=str, default='b', help="sig+bkg(s) or bkg(b)")
args = parser.parse_args()

def ShrinkFinalBin(h,val=600.0):
  bins = [h.GetBinLowEdge(b) for b in range(1,h.GetNbinsX()+2)]
  if len(bins) < 3: return h
  if val == None:
    new_bins = array('f',bins[:-1] + [2*bins[-2]-bins[-3]])
  else:
    new_bins = array('f',bins[:-1] + [val])
  new_h = ROOT.TH1D(h.GetName(),'',len(new_bins)-1, new_bins)
  for b in range(1,h.GetNbinsX()+1):
    new_h.SetBinContent(b,h.GetBinContent(b))
    new_h.SetBinError(b,h.GetBinError(b))
  return new_h

loc = "/vols/cms/gu18/4tau_v3/CMSSW_10_2_13/src/CombineHarvester/Combine4tau/outputs/0706_lt_z_control/all/"
ws = loc+"cmb/ws.root"
freezepar = "r_A60,r_A70,r_A80,r_A90,r_A125,r_A140,r_A160"
poi = "r_A100"
sig_scale = 0
setpar = "r_A60=0,r_A70=0,r_A80=0,r_A90=0,r_A100={},r_A125=0,r_A140=0,r_A160=0".format(sig_scale)
shift = 1.0
parranges = "r_A100={},{}:r_A60=0,0:r_A70=0,0:r_A80=0,0:r_A90=0,0:r_A125=0,0:r_A140=0,0:r_A160=0,0".format(sig_scale-shift,sig_scale+shift)
mass = "100"
name = args.name

cats = ["cmb","eett_z_control_nobtag","mmtt_z_control_nobtag"]

cat_to_latex = {
                "eett_z_control_nobtag":"e_{}e_{}#tau_{h}#tau_{h} Opposite Sign Lepton",
                "mmtt_z_control_nobtag":"#mu_{}#mu_{}#tau_{h}#tau_{h} Opposite Sign Lepton",
               }

step = args.step

if step in ["ws","all"]:
  for cat in cats:
    os.system("combineTool.py -M T2W -o ws.root -P CombineHarvester.Combine4tau.X2HDM:X2HDM -i %(loc)s/%(cat)s/ --X-allow-no-signal" % vars())

if step in ["fit","all"]:
  os.system("combineTool.py -M FitDiagnostics --redefineSignalPOIs %(poi)s --setParameters %(setpar)s --freezeParameters %(freezepar)s --setParameterRanges %(parranges)s --X-rtd MINIMIZER_analytic --cminDefaultMinimizerStrategy 0 --cminDefaultMinimizerTolerance 1 -m %(mass)s -d %(ws)s --robustHesse 1 -n .%(name)s --there -v 1" % vars())

if step in ["collect","all"]:

  for cat in cats:
    if "cmb" in cat: continue
    ft = args.fit
    os.system("PostFitShapesFromWorkspace -w \"%(loc)s/%(cat)s/ws.root\" -o \"%(name)s_%(cat)s.root\" -d \"%(loc)s/%(cat)s/%(cat)s.txt\" -f \"%(loc)s/cmb/fitDiagnostics.%(name)s.root:fit_%(ft)s\" --postfit" % vars())

if step in ["plot","all"]:

  backgrounds = OrderedDict()
  backgrounds["#geq 1 jet #rightarrow #tau_{h}"] = ["jetFakes"]
  backgrounds["Genuine #tau_{h}"] = ["VVR","VVV","ZR","WR","TTR","Higgs"]
  backgrounds["Other"] = ["VVLF","ZLF","WLF","TTLF"]

  total_bkg = "TotalBkg"
  data_obs = "data_obs"

  bkg_colours = [ROOT.TColor.GetColor(192,232,100),ROOT.TColor.GetColor(136,65,157),ROOT.TColor.GetColor(217,71,1)]

  signals = []

  for cat in cats:

    if cat == "cmb": continue

    f = ROOT.TFile(name+"_"+cat+".root")

    for t in ["prefit","postfit"]:

      directory = cat+"_"+t

      bkg_hists = []
      for k,v in backgrounds.iteritems():
        for ind,n in enumerate(v):
          if ind == 0:
            bkg_hists.append(ShrinkFinalBin(f.Get(directory+"/"+n)))
            bkg_hists[-1].SetName(k)
          else:
            bkg_hists[-1].Add(ShrinkFinalBin(f.Get(directory+"/"+n)))

      sig_hists = []
      for n in signals:
        sig_hists.append(ShrinkFinalBin(f.Get(directory+"/"+n)))

      data_hist = ShrinkFinalBin(f.Get(directory+"/"+data_obs))

      total_bkg_hist = ShrinkFinalBin(f.Get(directory+"/"+total_bkg))
      total_bkg_hist_down = total_bkg_hist.Clone()
      total_bkg_hist_up = total_bkg_hist.Clone()      
      for i in range(0,total_bkg_hist.GetNbinsX()+1):
        total_bkg_hist_down.SetBinContent(i,total_bkg_hist.GetBinContent(i)-total_bkg_hist.GetBinError(i))
        total_bkg_hist_up.SetBinContent(i,total_bkg_hist.GetBinContent(i)+total_bkg_hist.GetBinError(i))

      plotting.HTTPlotClean(bkg_hists=bkg_hists,
                            sig_hists=sig_hists,
                            data_hist=data_hist,
                            custom_uncerts=[total_bkg_hist_down,total_bkg_hist_up],
                            draw_data=True,
                            plot_name="%(name)s_%(cat)s_%(t)s" % vars(),
                            ratio_range="0,2",
                            y_title="Events",
                            x_title="m_{T}^{tot} (GeV)",
                            title_right="138 fb^{-1}",
                            title_left=cat_to_latex[cat],
                            bkg_colours=bkg_colours)
