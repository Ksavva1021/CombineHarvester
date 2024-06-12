#!/usr/bin/env python

#for m in 100 200; do python scripts/plotting/plot_model_dependent_limits.py outputs/2002/all/cmb/limits/phi${m}/limit_phi${m}.json --excluded-mass=${m} --logy --scenario-label="m_{#phi} = ${m} GeV" --output="md_mphi${m}_hb" --title-left="Type X 2HDM Alignment Scenario"; done
#for m in 100 200; do python scripts/plotting/plot_model_dependent_limits.py outputs/2002/all/cmb/limits/phi${m}/limit_phi${m}.json --logy --scenario-label="m_{#phi} = ${m} GeV" --output="md_mphi${m}" --title-left="Type X 2HDM Alignment Scenario"; done

import CombineHarvester.CombineTools.plotting as plot
import ROOT
import argparse
import json
from collections import OrderedDict
from array import array

ROOT.PyConfig.IgnoreCommandLineOptions = True
ROOT.gROOT.SetBatch(ROOT.kTRUE)

parser = argparse.ArgumentParser(
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument(
    'input', help="""Json file from AsymptoticLimit""")
parser.add_argument(
    '--output', default='limit_output', help="""Name of the output
    plot without file extension""")
parser.add_argument(
    '--contours', default='obs,exp0,exp1,exp2', help="""List of
    contours to plot.""")
parser.add_argument(
    '--x-title', default='m_{A} (GeV)', help="""Title for the x-axis""")
parser.add_argument(
    '--y-title', default='tan#beta', help="""Title for the y-axis""")
parser.add_argument(
    '--y-range', default="1,200", type=str, help="""y-axis range""")
parser.add_argument(
    '--cms-sub', default='Internal', help="""Text below the CMS logo""")
parser.add_argument(
    '--scenario-label', default='', help="""Scenario name to be drawn in top
    left of plot""")
parser.add_argument(
    '--title-right', default='138 fb^{-1} (13 TeV)', help="""Right header text above the frame""")
parser.add_argument(
    '--title-left', default='', help="""Left header text above the frame""")
parser.add_argument(
    '--excluded-mass', default='', help="""Excluded mass for region""")
parser.add_argument(
    '--logy', action='store_true', help="""Draw y-axis in log scale""")
parser.add_argument(
    '--logx', action='store_true', help="""Draw x-axis in log scale""")
parser.add_argument(
    '--box-allowed', default=None, type=str, help="""draw a box with allowed values, format is (x1,y1),(x2,y2),(x3,y3)""")
parser.add_argument(
    '--draw-contour', action='store_true', help="""Draw line contours across the plot""")
args = parser.parse_args()


with open(args.input, 'r') as fp:
  json_file = json.load(fp)

contours = {}
for c in ["exp-2","exp-1","exp0","exp+1","exp+2","obs"]:
  sorted_keys = [str(j) for j in sorted([float(i) for i in json_file.keys()])]
  contours[c] = ROOT.TGraph()
  for k in sorted_keys: contours[c].SetPoint(contours[c].GetN(),float(k),json_file[k][c])
  for k in reversed(sorted_keys): contours[c].SetPoint(contours[c].GetN(),float(k),float(args.y_range.split(",")[1]))
  contours[c].SetPoint(contours[c].GetN(),float(sorted_keys[0]),json_file[sorted_keys[0]][c])


canv = ROOT.TCanvas(args.output, args.output, 600, 600)
#plot.SetTDRStyle()
plot.ModTDRStyle(width=600, height=600)
if not ("obs" in args.contours and args.excluded_mass != ""):
  pads = plot.TwoPadSplit(0.8, 0, 0)
else:
  pads = plot.TwoPadSplit(0.75, 0, 0)

pads[1].cd()
binsx = array('f', map(float,sorted_keys)) 
#binsy = array('f', map(float,[float(args.y_range.split(",")[0]),float(args.y_range.split(",")[1])]))
#h_axis = ROOT.TH2D('h_axis','', len(binsx)-1, binsx, len(binsy)-1, binsy)
h_axis = ROOT.TH1D('h_axis','', len(binsx)-1, binsx)
h_axis.SetStats(0)

h_axis.GetXaxis().SetTitle(args.x_title)
h_axis.GetYaxis().SetTitle(args.y_title)
h_axis.GetXaxis().SetRangeUser(float(sorted_keys[0]),float(sorted_keys[-1]))
if args.y_range is not None:
    h_axis.GetYaxis().SetRangeUser(float(args.y_range.split(',')[0]),float(args.y_range.split(',')[1]))
h_axis.GetXaxis().SetNdivisions(5,5,0)
h_axis.Draw()
if args.logy: 
  h_axis.GetYaxis().SetMoreLogLabels()
  h_axis.GetYaxis().SetNoExponent()
if args.logx: 
  h_axis.GetXaxis().SetMoreLogLabels()
  h_axis.GetXaxis().SetNoExponent()

pads[1].SetLogy(args.logy)
pads[1].SetLogx(args.logx)
pads[1].SetTickx()
pads[1].SetTicky()

fillstyle = 'FSAME'

import copy
if 'exp2' in args.contours:
  plot.Set(contours['exp-2'], LineColor=0, FillColor=plot.CreateTransparentColor(ROOT.kGray + 0,0.9), FillStyle=1001)
  contours['exp-2'].Draw(fillstyle)
  copy_expm1 = copy.deepcopy(contours['exp-1'])
  plot.Set(copy_expm1, LineColor=0, FillColor=plot.CreateTransparentColor(ROOT.kWhite,1.0), FillStyle=1001)
  copy_expm1.Draw(fillstyle)
if 'exp1' in args.contours:
  plot.Set(contours['exp-1'], LineColor=0, FillColor=plot.CreateTransparentColor(ROOT.kGray + 1,0.9), FillStyle=1001)
  contours['exp-1'].Draw(fillstyle)
  copy_expp1 = copy.deepcopy(contours['exp+1'])
  plot.Set(copy_expp1, LineColor=0, FillColor=plot.CreateTransparentColor(ROOT.kWhite,1.0), FillStyle=1001)
  copy_expp1.Draw(fillstyle)
if 'exp2' in args.contours:
  plot.Set(contours['exp+1'], LineColor=0, FillColor=plot.CreateTransparentColor(ROOT.kGray + 0,0.9), FillStyle=1001)
  contours['exp+1'].Draw(fillstyle)
  copy_expp2 = copy.deepcopy(contours['exp+2'])
  plot.Set(copy_expp2, LineColor=0, FillColor=plot.CreateTransparentColor(ROOT.kWhite,1.0), FillStyle=1001)
  copy_expp2.Draw(fillstyle)

if 'exp0' in args.contours:
  if 'obs' in args.contours:
    plot.Set(contours["exp0"], LineColor=ROOT.kBlack, LineStyle=2)
    contours["exp0"].Draw('LSAME')
  else:
    pads[1].cd()
    plot.Set(contours["exp0"], LineStyle=2, FillStyle=1001,
             FillColor=plot.CreateTransparentColor(
                ROOT.kSpring + 6, 0.2))
    contours["exp0"].Draw(fillstyle)
    contours["exp0"].Draw('LSAME')
if 'obs' in args.contours:
  plot.Set(contours["obs"], FillStyle=1001, FillColor=plot.CreateTransparentColor(
      ROOT.kAzure + 6, 0.5))
  contours["obs"].Draw(fillstyle)
  contours["obs"].Draw('LSAME')

# Draw excluded regions
if args.excluded_mass != "":
  #excluded_file = ROOT.TFile("input/excluded_contours.root")
  #excluded_file = ROOT.TFile("input/excluded_contours_v2.root")
  #excl_cont = excluded_file.Get("mphi"+args.excluded_mass)
  #excluded_file = ROOT.TFile("input/typeX_info_v5.root")
  excluded_file = ROOT.TFile("input/typeX_BRs.root")

  for i in range(1,5):

    #for bs in ["b","s"]:

    #contour_name = "contour_exp_exc_h{}_mphi{}p0_csbma0p0_{}".format(bs,args.excluded_mass,i)
    contour_name = "contour_exp_exc_mphi{}p0_{}".format(args.excluded_mass,i)

    contour_exists = False
    if excluded_file and not excluded_file.IsZombie() and not excluded_file.TestBit(ROOT.TFile.kRecovered):
      contour = excluded_file.Get(contour_name)
      if contour:
        contour_exists = True

    if contour_exists:
      excl_cont = excluded_file.Get(contour_name)
      plot.Set(excl_cont, LineColor=2, FillColor=plot.CreateTransparentColor(2,0.2), FillStyle=1001)
      excl_cont.Draw('FSAME')
      excl_cont.Draw("LSAME")

if args.box_allowed != None and p == 1:
  n_points = args.box_allowed.count("(")
  graph = ROOT.TGraph(n_points+1)
  for i in range(n_points):
    point = args.box_allowed.split("(")[i+1].split(")")[0].split(",")
    graph.SetPoint(i, float(point[0]), float(point[1]))
  point_end = args.box_allowed.split("(")[1].split(")")[0].split(",")
  graph.SetPoint(n_points, float(point_end[0]), float(point_end[1]))
  graph.Print("all")
  plot.Set(graph, LineColor=8, FillColor=plot.CreateTransparentColor(8,0.2), FillStyle=1001)
  graph.Draw('FSAME')
  graph.Draw("LSAME")


pads[0].cd()
h_top = h_axis.Clone()
plot.Set(h_top.GetXaxis(), LabelSize=0, TitleSize=0, TickLength=0)
plot.Set(h_top.GetYaxis(), LabelSize=0, TitleSize=0, TickLength=0)
h_top.Draw()

# Draw the legend in the top TPad
if not ("obs" in args.contours and args.excluded_mass != ""):
  legend = plot.PositionedLegend(0.4, 0.11, 3, 0.015)
else:
  #legend = plot.PositionedLegend(0.4, 0.15, 3, 0.015)
  legend = plot.PositionedLegend(0.45, 0.15, 3, 0.015, horizontaloffset=0.0)

  legend.SetTextSize(0.027)
  #legend.SetColumnSeparation(-0.15)
  legend.SetColumnSeparation(-0.0)

plot.Set(legend, NColumns=2, Header='#bf{%.0f%% CL excluded:}' % (95.))
if 'obs' in args.contours:
    legend.AddEntry(contours['obs'], "Observed", "F")
if 'exp1' in args.contours:
    legend.AddEntry(contours['exp-1'], "68% expected", "F")
if 'exp0' in args.contours:
    if 'obs' in contours:
        legend.AddEntry(contours['exp0'], "Expected", "L")
    else:
        legend.AddEntry(contours['exp0'], "Expected", "F")
if 'exp2' in args.contours:
    legend.AddEntry(contours['exp-2'], "95% expected", "F")
if args.excluded_mass != "":
    entry = legend.AddEntry(excl_cont, "HiggsTools-1", "F")
    entry.SetTextFont(82)
    # 82
if args.box_allowed != None:
  legend.AddEntry(graph, "Allowed for g-2", "F")

legend.Draw()

# Draw logos and titles
plot.DrawCMSLogo(pads[0], 'CMS', args.cms_sub, 11, 0.045, 0.15, 1.0, '', 1.0)
plot.DrawTitle(pads[0], args.title_right, 3)
plot.DrawTitle(pads[0], args.title_left, 1)


# Redraw the frame because it usually gets covered by the filled areas
pads[1].cd()
pads[1].GetFrame().Draw()
pads[1].RedrawAxis()

# Draw the scenario label
latex = ROOT.TLatex()
latex.SetNDC()
latex.SetTextSize(0.04)
#latex.DrawLatex(0.155, 0.75, args.scenario_label)
if not ("obs" in args.contours and args.excluded_mass != ""):
  latex.DrawLatex(0.18, 0.75, args.scenario_label)
else:
  latex.DrawLatex(0.18, 0.7, args.scenario_label)

canv.Print('.pdf')
canv.Print('.png')
canv.Close()
