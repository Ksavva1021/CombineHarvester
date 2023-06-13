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

loc = "/vols/cms/gu18/4tau_v3/CMSSW_10_2_13/src/CombineHarvester/Combine4tau/0806_unblinding/all/"
ws = loc+"cmb/ws.root"
freezepar = "r_A60,r_A70,r_A80,r_A90,r_A125,r_A140,r_A160"
poi = "r_A100"
sig_scale = 0
setpar = "r_A60=0,r_A70=0,r_A80=0,r_A90=0,r_A100={},r_A125=0,r_A140=0,r_A160=0".format(sig_scale)
shift = 1.0
parranges = "r_A100={},{}:r_A60=0,0:r_A70=0,0:r_A80=0,0:r_A90=0,0:r_A125=0,0:r_A140=0,0:r_A160=0,0".format(sig_scale-shift,sig_scale+shift)
mass = "100"
name = args.name

cats = ["cmb","eett_z_control_nobtag","mmtt_z_control_nobtag","emtt_z_control_nobtag","eett_2l2t_sig_nobtag","mmtt_2l2t_sig_nobtag","emtt_2l2t_sig_nobtag","ettt_nobtag","mttt_nobtag","tttt_inclusive","ttt_inclusive"]

#cat_to_latex = {
#                "eett_z_control_nobtag":"e_{}e_{}#tau_{h}#tau_{h} Opposite Sign Leptons",
#                "mmtt_z_control_nobtag":"#mu_{}#mu_{}#tau_{h}#tau_{h} Opposite Sign Leptons",
#                "emtt_z_control_nobtag":"e_{}#mu_{}#tau_{h}#tau_{h} Opposite Sign Leptons",
#                "eett_2l2t_sig_nobtag":"e_{}e_{}#tau_{h}#tau_{h} Same Sign Leptons",
#                "mmtt_2l2t_sig_nobtag":"#mu_{}#mu_{}#tau_{h}#tau_{h} Same Sign Leptons",
#                "emtt_2l2t_sig_nobtag":"e_{}#mu_{}#tau_{h}#tau_{h} Same Sign Leptons",
#                "ettt_nobtag":"e_{}#tau_{h}#tau_{h}#tau_{h}",
#                "mttt_nobtag":"#mu_{}#tau_{h}#tau_{h}#tau_{h}",
#                "tttt_inclusive":"#tau_{h}#tau_{h}#tau_{h}#tau_{h}",
#                "ttt_inclusive":"#tau_{h}#tau_{h}#tau_{h}",
#               }

cat_to_latex = {
                "eett_z_control_nobtag":"e_{}e_{}#tau_{h}#tau_{h} OS Leptons",
                "mmtt_z_control_nobtag":"#mu_{}#mu_{}#tau_{h}#tau_{h} OS Leptons",
                "emtt_z_control_nobtag":"e_{}#mu_{}#tau_{h}#tau_{h} OS Leptons",
                "eett_2l2t_sig_nobtag":"e_{}e_{}#tau_{h}#tau_{h} SS Leptons",
                "mmtt_2l2t_sig_nobtag":"#mu_{}#mu_{}#tau_{h}#tau_{h} SS Leptons",
                "emtt_2l2t_sig_nobtag":"e_{}#mu_{}#tau_{h}#tau_{h} SS Leptons",
                "ettt_nobtag":"e_{}#tau_{h}#tau_{h}#tau_{h}",
                "mttt_nobtag":"#mu_{}#tau_{h}#tau_{h}#tau_{h}",
                "tttt_inclusive":"#tau_{h}#tau_{h}#tau_{h}#tau_{h}",
                "ttt_inclusive":"#tau_{h}#tau_{h}#tau_{h}",
               }


total_bkg = "TotalBkg"
data_obs = "data_obs"

backgrounds = OrderedDict()
backgrounds["#geq 1 jet #rightarrow #tau_{h}"] = ["jetFakes"]
backgrounds["Genuine #tau_{h}"] = ["VVR","VVV","ZR","WR","TTR","Higgs"]
backgrounds["Other"] = ["VVLF","ZLF","WLF","TTLF"]

bkg_colours = [ROOT.TColor.GetColor(192,232,100),ROOT.TColor.GetColor(136,65,157),ROOT.TColor.GetColor(217,71,1)]

signals = OrderedDict()
signals["H(200)A(160); @ 0.01 pb"] = ["A160"]


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
    os.system("PostFitShapesFromWorkspace -w \"%(loc)s/%(cat)s/ws.root\" -o \"%(name)s_%(cat)s.root\" -d \"%(loc)s/%(cat)s/%(cat)s.txt\" -f \"%(loc)s/cmb/fitDiagnostics.%(name)s.root:fit_%(ft)s\" --postfit --freeze \"MH=200,r_A160=0.01\"" % vars())

if step in ["plot","all"]:

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
      for k,v in signals.iteritems():
        for ind,n in enumerate(v):
          if ind == 0:
            sig_hists.append(ShrinkFinalBin(f.Get(directory+"/"+n)))
            sig_hists[-1].SetName(k)
          else:
            sig_hists[-1].Add(ShrinkFinalBin(f.Get(directory+"/"+n)))

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

if step in ["combine","all"]:
  
  cats_to_combine = cats[1:]

  cats_to_combines = {
                      "low_stat":["ettt_nobtag","mttt_nobtag","tttt_inclusive","eett_2l2t_sig_nobtag","mmtt_2l2t_sig_nobtag","emtt_2l2t_sig_nobtag","emtt_z_control_nobtag"],
                      "med_stat":["eett_z_control_nobtag","mmtt_z_control_nobtag"],
                      "high_stat":["ttt_inclusive"]
                      }

  for extra_name, cats_to_combine in cats_to_combines.items():
 
    # get number of bins
    # add a bin for every category division
    nbins = 0
    bin_labels = []
    divider_lines = []
    for cat in cats_to_combine:
      f = ROOT.TFile(name+"_"+cat+".root")
      t = "prefit"
      directory = cat+"_"+t
      hist = f.Get(directory+"/"+data_obs)
      nbins += hist.GetNbinsX()
      for i in range(1,hist.GetNbinsX()+1):
        bin_labels.append("["+str(int(hist.GetXaxis().GetBinLowEdge(i)))+","+str(int(hist.GetXaxis().GetBinLowEdge(i+1))).replace("6000","#infty")+"]")
      if cat in cats_to_combine[:-1]:
        #bin_labels.append("")
        #nbins += 1
        divider_lines.append(nbins)
      f.Close()

    # fill histogram
    bins = array('f', map(float,list(range(0,nbins+1))))
    hout = ROOT.TH1D('hout','',len(bins)-1, bins)

    for t in ["prefit","postfit"]:

      bkg_hists = []
      sig_hists = []

      data_hist = copy.deepcopy(hout)
      total_bkg_hist = copy.deepcopy(hout)
      total_bkg_hist_down = copy.deepcopy(total_bkg_hist)
      total_bkg_hist_up = copy.deepcopy(total_bkg_hist)

      # backgrounds
      for k,v in backgrounds.iteritems():
        bkg_hists.append(copy.deepcopy(hout.Clone()))
        bkg_hists[-1].SetName(k)
        for ind_v,n in enumerate(v):
          ind = 1
          for cat in cats_to_combine:
            f = ROOT.TFile(name+"_"+cat+".root")
            directory = cat+"_"+t
            hist_orig = copy.deepcopy(f.Get(directory+"/"+n))
            #ind += 1
            for i in range(1,hist_orig.GetNbinsX()+1):
              bkg_hists[-1].SetBinContent(ind,hist_orig.GetBinContent(i)+bkg_hists[-1].GetBinContent(ind))
              bkg_hists[-1].SetBinError(ind,(hist_orig.GetBinError(i)**2 + bkg_hists[-1].GetBinError(ind)**2)**0.5)
              ind += 1
            f.Close()

      # signals
      for k,v in signals.iteritems():
        sig_hists.append(copy.deepcopy(hout.Clone()))
        sig_hists[-1].SetName(k)
        for ind_v,n in enumerate(v):
          ind = 1
          for cat in cats_to_combine:
            f = ROOT.TFile(name+"_"+cat+".root")
            directory = cat+"_"+t
            hist_orig = copy.deepcopy(f.Get(directory+"/"+n))
            #ind += 1
            for i in range(1,hist_orig.GetNbinsX()+1):
              sig_hists[-1].SetBinContent(ind,hist_orig.GetBinContent(i)+sig_hists[-1].GetBinContent(ind))
              sig_hists[-1].SetBinError(ind,(hist_orig.GetBinError(i)**2 + sig_hists[-1].GetBinError(ind)**2)**0.5)
              ind +=1
            f.Close()

      # data
      ind = 1
      for cat in cats_to_combine:
        f = ROOT.TFile(name+"_"+cat+".root")
        directory = cat+"_"+t
        hist_orig = copy.deepcopy(f.Get(directory+"/"+data_obs))
        #ind += 1
        for i in range(1,hist_orig.GetNbinsX()+1):
          data_hist.SetBinContent(ind,hist_orig.GetBinContent(i))
          data_hist.SetBinError(ind,hist_orig.GetBinError(i))
          ind +=1
        f.Close()

      # total bkg
      ind = 1
      for cat in cats_to_combine:
        f = ROOT.TFile(name+"_"+cat+".root")
        directory = cat+"_"+t
        hist_orig = copy.deepcopy(f.Get(directory+"/"+total_bkg))
        #ind += 1
        for i in range(1,hist_orig.GetNbinsX()+1):
          total_bkg_hist.SetBinContent(ind,hist_orig.GetBinContent(i))
          total_bkg_hist.SetBinError(ind,hist_orig.GetBinError(i))
          ind +=1
        f.Close()

      for i in range(0,total_bkg_hist.GetNbinsX()+1):
        total_bkg_hist_down.SetBinContent(i,total_bkg_hist.GetBinContent(i)-total_bkg_hist.GetBinError(i))
        total_bkg_hist_up.SetBinContent(i,total_bkg_hist.GetBinContent(i)+total_bkg_hist.GetBinError(i))

      if "low_stat" in extra_name:
        divider_text_pos = [0.5]+[i+0.5 for i in divider_lines]
        ratio_range="0.01,2.99"
      else:
        divider_text_pos = [0.75]+[i+0.75 for i in divider_lines]
        ratio_range="0,2"
 
      plotting.HTTPlotClean(bkg_hists=bkg_hists,
                            sig_hists=sig_hists,
                            data_hist=data_hist,
                            custom_uncerts=[total_bkg_hist_down,total_bkg_hist_up],
                            draw_data=True,
                            plot_name="%(name)s_combined_%(t)s_%(extra_name)s" % vars(),
                            ratio_range=ratio_range,
                            y_title="Events",
                            x_title="m_{T}^{tot} (GeV)",
                            title_right="138 fb^{-1}",
                            title_left="",
                            bkg_colours=bkg_colours,
                            replace_axis=True,
                            replace_labels=[[i+0.5 for i in range(0,nbins)],bin_labels],
                            shift_pad_up=0.1,
                            x_title_offset=2.6,
                            divider_lines=divider_lines,
                            divider_text = [divider_text_pos,[cat_to_latex[i] for i in cats_to_combine]],
                            width = 600,
                            y_axis_above_max = 1.8
                            )

