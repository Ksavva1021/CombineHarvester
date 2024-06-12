#!/usr/bin/env python

#for m in 100 200; do python scripts/plotting/plot_model_dependent_limits.py outputs/2002/all/cmb/limits/phi${m}/limit_phi${m}.json --excluded-mass=${m} --logy --scenario-label="m_{#phi} = ${m} GeV" --output="md_mphi${m}_hb" --title-left="Type X 2HDM Alignment Scenario"; done
#for m in 100 200; do python scripts/plotting/plot_model_dependent_limits.py outputs/2002/all/cmb/limits/phi${m}/limit_phi${m}.json --logy --scenario-label="m_{#phi} = ${m} GeV" --output="md_mphi${m}" --title-left="Type X 2HDM Alignment Scenario"; done

import json
import os
import numpy as np
import ROOT
import copy
from scipy.interpolate import griddata
import argparse
from array import array
from scipy.interpolate import Rbf
from scipy.spatial import Delaunay
from scipy.interpolate import LinearNDInterpolator
import CombineHarvester.CombineTools.plotting as plot


parser = argparse.ArgumentParser()
parser.add_argument('--file', help= 'File with __m__ in that is replaced mphi', default='outputs/260424_morphing/all/phi___m__/cmb/limits/limit_limits.json')
parser.add_argument('--mphi', help= 'mphi values to try and get', default='60,70,80,90,100,110,125,140,160,180,200,250,300,400,600')
parser.add_argument('--mA', help= 'mA values to try and get', default='40,50,60,70,80,90,100,125,140,160,200,250,300,400,600')
parser.add_argument('--data-type', help= 'Data type to use', default='obs')
parser.add_argument('--points', help= 'Number of points in each dimension', default='100')
parser.add_argument('--logx', help='Do log x', action='store_true')
parser.add_argument('--logy', help='Do log y', action='store_true')
parser.add_argument('--logz', help='Do log z', action='store_true')
parser.add_argument('--output', help= 'output name', default='md_plots/md_2d')
parser.add_argument('--no-interp', help='Do no interpolation', action='store_true')
parser.add_argument('--x-range', help= 'X range', default='40,400')
parser.add_argument('--y-range', help= 'Y range', default='60,400')
parser.add_argument('--z-range', help= 'Y range', default='1,100')
parser.add_argument('--x-title', help= 'X title', default="m_{A} (GeV)")
parser.add_argument('--y-title', help= 'Y title', default="m_{#phi} (GeV)")
parser.add_argument('--z-title', help= 'Z title', default="95% CL observed lower limits on tan#beta")
parser.add_argument('--show-complete-exclusion', help='Show complete exclusion', action='store_true')
parser.add_argument('--show-allowed-region', help='Show allowed region', action='store_true')
parser.add_argument('--cms-sub', help= 'CMS sub text', default="")
parser.add_argument('--title-right', help= 'Title right', default="138 fb^{-1} (13 TeV)")
parser.add_argument('--title-left', help= 'Title left', default="")
parser.add_argument('--add-contours', help= 'Add contours', action='store_true')

args = parser.parse_args()

canv = ROOT.TCanvas(args.output, args.output, 600, 600)
plot.ModTDRStyle(width=600, height=600)
if args.show_allowed_region and not args.show_complete_exclusion:
  pads = plot.TwoPadSplit(0.785, 0, 0.0)
elif args.show_allowed_region and args.show_complete_exclusion:
  pads = plot.TwoPadSplit(0.66, 0, 0.0)
else:
  pads = plot.TwoPadSplit(0.8, 0, 0.0)


##############################################################

##############################################################

# Get inputs

mphis = [float(mphi) for mphi in args.mphi.split(",")]
mAs = [float(mA) for mA in args.mA.split(",")]

# Load in limits

total_mphis = []
total_mAs = []
total_tanbs = []

for mphi in mphis:

  file_name = args.file.replace("__m__",str(int(mphi)))
  if not os.path.isfile(file_name): continue

  with open(file_name, 'r') as file:
    limits = json.load(file)

  for mA in mAs:

    limit_available = False
    if str(mA) in limits.keys():
      if args.data_type in limits[str(mA)].keys():
        if limits[str(mA)][args.data_type] < 150.0:
          limit_available = True

    if limit_available:
      total_mphis.append(mphi)
      total_mAs.append(mA)
      total_tanbs.append(limits[str(mA)][args.data_type])

# Print what was loaded in

#for ind in range(len(total_mphis)):
#  print(total_mphis[ind], total_mAs[ind], total_tanbs[ind])

# Build ip a histogram

if not args.no_interp:
  hist_x_bins = list(np.linspace(min(mAs), max(mAs), num=args.points))
  hist_y_bins = list(np.linspace(min(mphis), max(mphis), num=args.points))
else:
  hist_x_bins = mAs
  hist_y_bins = mphis

hout = ROOT.TH2D('hout','',len(hist_x_bins)-1, array('f', map(float,hist_x_bins)),len(hist_y_bins)-1, array('f', map(float,hist_y_bins)))
hexcinterp = ROOT.TH2D('hout','',len(hist_x_bins)-1, array('f', map(float,hist_x_bins)),len(hist_y_bins)-1, array('f', map(float,hist_y_bins)))
hexc = ROOT.TH2D('hout','',len(mAs)-1, array('f', map(float,mAs)),len(mphis)-1, array('f', map(float,mphis)))

tri = Delaunay(np.column_stack((total_mAs, [total_mphis[ind]-total_mAs[ind] for ind in range(len(total_mphis))])))
del_interp = LinearNDInterpolator(tri, total_tanbs)

for i in range(hout.GetNbinsX()+1):
  for j in range(hout.GetNbinsY()+1):
    if not args.no_interp:
      #interp = del_interp(hout.GetXaxis().GetBinCenter(i),hout.GetYaxis().GetBinCenter(j))
      interp = del_interp(hout.GetXaxis().GetBinCenter(i),hout.GetYaxis().GetBinCenter(j)-hout.GetXaxis().GetBinCenter(i))
    else:
      interp = np.nan
      if hout.GetXaxis().GetBinLowEdge(i) in total_mAs:
        total_mAs_inds = (np.array(total_mAs)==hout.GetXaxis().GetBinLowEdge(i))
        if hout.GetYaxis().GetBinLowEdge(j) in np.array(total_mphis)[total_mAs_inds]:
          interp_ind = (np.array(total_mphis)[total_mAs_inds]==hout.GetYaxis().GetBinLowEdge(j))
          interp = np.array(total_tanbs)[total_mAs_inds][interp_ind][0]

    if interp > 150.0 or np.isnan(interp):
      interp = 0.0
    hout.SetBinContent(i,j,interp)

# Find experiment exclusions
total_mphis = []
total_mAs = []
total_tanbs = []
excluded_file = ROOT.TFile("input/typeX_BRs.root")
for mphi in mphis:
  hist_name = "exp_exc_mphi{}p0".format(int(mphi))
  hist = excluded_file.Get(hist_name)
  if not hist: continue
  for mA in mAs:
    # mA bin
    bin_number_x = hist.GetXaxis().FindBin(mA)

    # find that tanb bin in the exclusion file
    for j in range(hist.GetNbinsY()+1):
      if j == 0:
        prev_j = copy.deepcopy(j)
        continue
      if hist.GetBinContent(bin_number_x,j) > 0.5 and hist.GetBinContent(bin_number_x,prev_j) < 0.5:
        tanb_limit = hist.GetYaxis().GetBinCenter(j)
        break
      prev_j = copy.deepcopy(j)

    # Add to array for interpolation
    total_mphis.append(mphi)
    total_mAs.append(mA)
    total_tanbs.append(tanb_limit)

# Interpolate hexc
tri_exc = Delaunay(np.column_stack((total_mAs, [total_mphis[ind]-total_mAs[ind] for ind in range(len(total_mphis))])))
del_interp_exc = LinearNDInterpolator(tri_exc, total_tanbs)

for i in range(hexcinterp.GetNbinsX()+1):
  for j in range(hexcinterp.GetNbinsY()+1):
    if not args.no_interp:
      interp = del_interp_exc(hexcinterp.GetXaxis().GetBinCenter(i),hexcinterp.GetYaxis().GetBinCenter(j)-hexcinterp.GetXaxis().GetBinCenter(i))
    else:
      interp = np.nan
      if hexcinterp.GetXaxis().GetBinLowEdge(i) in total_mAs:
        total_mAs_inds = (np.array(total_mAs)==hexcinterp.GetXaxis().GetBinLowEdge(i))
        if hexcinterp.GetYaxis().GetBinLowEdge(j) in np.array(total_mphis)[total_mAs_inds]:
          interp_ind = (np.array(total_mphis)[total_mAs_inds]==hexcinterp.GetYaxis().GetBinLowEdge(j))
          interp = np.array(total_tanbs)[total_mAs_inds][interp_ind][0]

    if interp > 150.0 or np.isnan(interp):
      interp = 0.0
    hexcinterp.SetBinContent(i,j,interp)

# Find contour
hexccontour = hexcinterp.Clone()
hexccontour.Reset()
for i in range(hexccontour.GetNbinsX()+2):
  for j in range(hexccontour.GetNbinsY()+2):
    hexccontour.SetBinContent(i,j,1)

for i in range(hexccontour.GetNbinsX()+2):
  for j in range(hexccontour.GetNbinsY()+2):
    hexccontour.SetBinContent(i,j,1)
    obs_limit = hout.GetBinContent(i,j)
    exc_limit = hexcinterp.GetBinContent(i,j)
    if obs_limit > exc_limit or obs_limit == 0 or np.isnan(obs_limit) or np.isnan(exc_limit):
      hexccontour.SetBinContent(i,j, 1.0)
    else:
      hexccontour.SetBinContent(i,j, 0.0)

cont = plot.contourFromTH2(hexccontour,0.5)

#hexc.Smooth()

"""
for i in range(hexc.GetNbinsX()+2):
  for j in range(hexc.GetNbinsY()+2):
    hexc.SetBinContent(i,j,1)
#hexc.Smooth()

excluded_file = ROOT.TFile("input/typeX_BRs.root")
exc_mAs = []
exc_mphis = []
excs = []
for mphi in mphis:
  hist_name = "exp_exc_mphi{}p0".format(int(mphi))
  hist = excluded_file.Get(hist_name)
  if not hist: continue
  for mA in mAs:
    # find tanb limit
    tanb_limit = hout.GetBinContent(hout.GetXaxis().FindBin(mA),hout.GetYaxis().FindBin(mphi))
    if tanb_limit == 0: continue
    # find that tanb bin in the exclusion file
    bin_number_x = hist.GetXaxis().FindBin(mA)
    bin_number_y = hist.GetYaxis().FindBin(tanb_limit)
    all_zeros = True
    for bn in range(bin_number_y,0,-1):
      if hist.GetBinContent(bin_number_x,bn) != 0:
        all_zeros = False
        break
    if all_zeros:
      hexc.SetBinContent(hexc.GetXaxis().FindBin(mA),hexc.GetYaxis().FindBin(mphi),0.0)
      exc_mAs.append(mA)
      exc_mphis.append(mphi)
      excs.append(0.0)
    else:
      exc_mAs.append(mA)
      exc_mphis.append(mphi)
      excs.append(1.0)

#tri_exc = Delaunay(np.column_stack((exc_mAs, exc_mphis)))
tri_exc = Delaunay(np.column_stack((exc_mAs, [exc_mphis[ind]-exc_mAs[ind] for ind in range(len(exc_mphis))])))

del_exc_interp = LinearNDInterpolator(tri_exc, excs)

for i in range(hexcinterp.GetNbinsX()+1):
  for j in range(hexcinterp.GetNbinsY()+1):
    #interp = del_exc_interp(hexcinterp.GetXaxis().GetBinCenter(i),hexcinterp.GetYaxis().GetBinCenter(j))
    interp = del_exc_interp(hexcinterp.GetXaxis().GetBinCenter(i),hexcinterp.GetYaxis().GetBinCenter(j)-hexcinterp.GetXaxis().GetBinCenter(i))
    if np.isnan(interp) or interp == np.inf:
      interp = 1
    hexcinterp.SetBinContent(i,j,interp)

#hexcinterp.Smooth()
cont = plot.contourFromTH2(hexcinterp,0.5)

"""

pads[1].cd()
haxis = hout.Clone()
haxis.Reset()
haxis.Draw("COLZ")
haxis.SetContour(255)
haxis.SetStats(0)
haxis.GetXaxis().SetRangeUser(float(args.x_range.split(",")[0]),float(args.x_range.split(",")[1]))
haxis.GetYaxis().SetRangeUser(float(args.y_range.split(",")[0]),float(args.y_range.split(",")[1]))

ROOT.gStyle.SetPalette(ROOT.kViridis)
haxis.SetContour(255)
haxis.SetStats(0)

haxis.GetXaxis().SetTitle(args.x_title)
haxis.GetYaxis().SetTitle(args.y_title)
haxis.GetXaxis().SetTitleSize(0.04)
haxis.GetYaxis().SetTitleSize(0.04)
haxis.GetXaxis().SetTitleOffset(1.2)
haxis.GetYaxis().SetTitleOffset(1.6)

haxis.GetXaxis().SetRangeUser(float(args.x_range.split(",")[0]),float(args.x_range.split(",")[1]))
if args.y_range is not None:
    haxis.GetYaxis().SetRangeUser(float(args.y_range.split(',')[0]),float(args.y_range.split(',')[1]))
if args.z_range is not None:
    haxis.GetZaxis().SetRangeUser(float(args.z_range.split(',')[0]),float(args.z_range.split(',')[1]))
haxis.GetXaxis().SetNdivisions(5,5,0)
if args.logy: 
  haxis.GetYaxis().SetMoreLogLabels()
  haxis.GetYaxis().SetNoExponent()
if args.logx: 
  haxis.GetXaxis().SetMoreLogLabels()
  haxis.GetXaxis().SetNoExponent()

conts = {}
hist_to_cont = {}
for show_tanb in [2,6,15,40,200]:

  # make hist
  hist_to_cont = hout.Clone()
  hist_to_cont.Reset()
  for i in range(hout.GetNbinsX()+1):
    for j in range(hout.GetNbinsY()+1):
      if hout.GetBinContent(i,j) < show_tanb:
        hist_to_cont.SetBinContent(i,j,1)

  conts[show_tanb] = plot.contourFromTH2(hist_to_cont,0.5)
  for contour_index in range(conts[show_tanb].GetSize()):
    name = str(show_tanb)+"_"+str(contour_index)
    conts[name] = conts[show_tanb].At(contour_index)
    plot.Set(conts[name], LineColor=1, LineWidth=2)
    pads[1].cd()
    conts[name].Draw("LSAME")


pads[1].SetLogz(args.logz)
pads[1].SetLogy(args.logy)
pads[1].SetLogx(args.logx)
pads[1].SetTickx()
pads[1].SetTicky()


if args.show_complete_exclusion:
  for contour_index in range(cont.GetSize()):
    contour = cont.At(contour_index)
    plot.Set(contour, LineColor=2, LineWidth=2, LineStyle=5, FillColor=plot.CreateTransparentColor(2,0.0), FillStyle=3144)
    pads[1].cd()
    contour.Draw("LSAME")


if args.show_allowed_region:
  x_data_inverted = [70,105,105,70,70]
  y_data_inverted = [100,100,120,120,100]
  graph_inverted = ROOT.TGraph(len(x_data_inverted), array("d", x_data_inverted), array("d", y_data_inverted))
  plot.Set(graph_inverted, LineColor=ROOT.kGreen+3, LineWidth=2, LineStyle=9, FillColor=plot.CreateTransparentColor(ROOT.kGreen+3,0.0), FillStyle=3144)
  #graph_inverted.Draw('FSAME')
  pads[1].cd()
  graph_inverted.Draw("LSAME")

  x_data_normal = [62.5,145,145,62.5,62.5]
  y_data_normal = [130,130,245,245,130]
  graph_normal = ROOT.TGraph(len(x_data_normal), array("d", x_data_normal), array("d", y_data_normal))
  plot.Set(graph_normal, LineColor=ROOT.kGreen+3, LineWidth=2, LineStyle=9 ,FillColor=plot.CreateTransparentColor(ROOT.kGreen+3,0.0), FillStyle=3144)
  #graph_normal.Draw('FSAME')
  pads[1].cd()
  graph_normal.Draw("LSAME")


##############################################################

pads[0].cd()
h_top = hout.Clone()
h_top.Reset()
plot.Set(h_top.GetXaxis(), LabelSize=0, TitleSize=0, TickLength=0)
plot.Set(h_top.GetYaxis(), LabelSize=0, TitleSize=0, TickLength=0)
h_top.Draw()


if args.show_complete_exclusion and not args.show_allowed_region:
  legend0 = plot.PositionedLegend(0.6, 0.12, 3, 0.005)
  legend0.SetTextSize(0.027)
  legend0.SetColumnSeparation(-0.0)
  plot.Set(legend0, NColumns=1, Header='#bf{%.0f%% CL excluded:}' % (95.))
  legend0.AddEntry(conts[name], "Observed", "L")
  legend0.AddEntry(contour, "Observed #cup #font[82]{HiggsTools-1}, All tan#beta", "F")
  legend0.Draw()

elif args.show_allowed_region and not args.show_complete_exclusion:
  legend0 = plot.PositionedLegend(0.6, 0.1, 3, 0.005)
  plot.Set(legend0, NColumns=1, Header='#bf{%.0f%% CL allowed:}' % (95.))
  legend0.SetTextSize(0.027)
  legend0.AddEntry(graph_normal, "Muon g-2: Phys. Rev. D 104, 095008", "F")
  legend0.Draw("same")

elif args.show_allowed_region and args.show_complete_exclusion:
  legend0 = plot.PositionedLegend(0.6, 0.15, 3, 0.005)
  legend0.SetTextSize(0.027)
  legend0.SetColumnSeparation(-0.0)
  plot.Set(legend0, NColumns=1, Header='#bf{%.0f%% CL excluded:}' % (95.))
  legend0.AddEntry(conts[name], "Observed", "L")
  legend0.AddEntry(contour, "Observed #cup #font[82]{HiggsTools-1}, All tan#beta", "F")
  legend0.Draw()

  legend1 = plot.PositionedLegend(0.6, 0.1, 3, 0.15, horizontaloffset=0.01)
  plot.Set(legend1, NColumns=1, Header='#bf{%.0f%% CL allowed:}' % (95.))
  legend1.SetTextSize(0.027)
  legend1.AddEntry(graph_normal, "Muon g-2: Phys. Rev. D 104, 095008", "F")
  legend1.Draw("same")

else:
  legend0 = plot.PositionedLegend(0.45, 0.1, 3, 0.005)
  legend0.SetTextSize(0.027)
  legend0.SetColumnSeparation(-0.0)
  plot.Set(legend0, NColumns=1, Header='#bf{%.0f%% CL excluded:}' % (95.))
  legend0.AddEntry(conts[name], "Observed", "L")
  legend0.Draw()

# Draw logos and titles
plot.DrawCMSLogo(pads[0], 'CMS', args.cms_sub, 11, 0.025, 0.15, 1.0, '', 1.0)
plot.DrawTitle(pads[0], args.title_right, 3, textSize=0.5)
plot.DrawTitle(pads[0], args.title_left, 1, textSize=0.5)

# Redraw the frame because it usually gets covered by the filled areas
pads[1].cd()
pads[1].GetFrame().Draw()
pads[1].RedrawAxis()

canv.Print('.pdf')
canv.Print('.png')
canv.Close()
