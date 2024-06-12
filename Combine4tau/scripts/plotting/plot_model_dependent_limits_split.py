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
args = parser.parse_args()


with open(args.input, 'r') as fp:
  json_file = json.load(fp)

segments = [0.05,0.25,0.275,0.275,0.15]
y_lower_range = [1.0,99.9]
y_upper_range = [100.0,200.0]

contours = {}
for c in ["exp-2","exp-1","exp0","exp+1","exp+2","obs"]:
  sorted_keys = [str(j) for j in sorted([float(i) for i in json_file.keys()])]
  contours[c] = ROOT.TGraph()
  for k in sorted_keys: contours[c].SetPoint(contours[c].GetN(),float(k),json_file[k][c])
  for k in reversed(sorted_keys): contours[c].SetPoint(contours[c].GetN(),float(k),y_upper_range[1])
  contours[c].SetPoint(contours[c].GetN(),float(sorted_keys[0]),json_file[sorted_keys[0]][c])

canv = ROOT.TCanvas(args.output, args.output, 600, 600)
plot.ModTDRStyle(width=600, height=600)
pads = [None,None,None,None]

pads[0] = ROOT.TPad('legend', 'legend', 0., 0., 1., 1.)
pads[0].SetTopMargin(sum(segments[:1]))
pads[0].SetBottomMargin(sum(segments[2:]))
pads[0].SetFillStyle(4000)
pads[0].Draw()

pads[1] = ROOT.TPad('linear', 'linear', 0., 0., 1., 1.)
pads[1].SetTopMargin(sum(segments[:2]))
pads[1].SetBottomMargin(sum(segments[3:]))
pads[1].SetFillStyle(4000)
pads[1].SetTickx()
pads[1].SetTicky()
pads[1].Draw("SAME")

pads[2] = ROOT.TPad('log', 'log', 0., 0., 1., 1.)
pads[2].SetTopMargin(sum(segments[:3]))
pads[2].SetBottomMargin(sum(segments[4:]))
pads[2].SetFillStyle(4000)
pads[2].SetLogy(True)
pads[2].SetTickx()
pads[2].SetTicky()
pads[2].Draw("SAME")

pads[3] = ROOT.TPad('log', 'log', 0., 0., 1., 1.)
pads[3].SetTopMargin(sum(segments[:2]))
pads[3].SetBottomMargin(sum(segments[4:]))
pads[3].SetFillStyle(4000)
pads[3].SetTickx()
pads[3].SetTicky()
pads[3].Draw("SAME")

pads[3].cd()
binsx = array('f', map(float,sorted_keys)) 
h3_axis = ROOT.TH1D('h_axis','', len(binsx)-1, binsx)
h3_axis.SetStats(0)
h3_axis.GetXaxis().SetRangeUser(float(sorted_keys[0]),float(sorted_keys[-1]))
h3_axis.GetXaxis().SetNdivisions(5,5,0)
h3_axis.GetYaxis().SetTickSize(0)
h3_axis.GetXaxis().SetLabelSize(0)
h3_axis.GetYaxis().SetLabelSize(0)
h3_axis.GetXaxis().SetTickLength(0.03)
h3_axis.Draw("SAME")

pads[2].cd()
binsx = array('f', map(float,sorted_keys)) 
h2_axis = ROOT.TH1D('h_axis','', len(binsx)-1, binsx)
h2_axis.SetStats(0)
h2_axis.GetXaxis().SetTitle(args.x_title)
h2_axis.GetXaxis().SetRangeUser(float(sorted_keys[0]),float(sorted_keys[-1]))
h2_axis.GetYaxis().SetRangeUser(y_lower_range[0],y_lower_range[1])
h2_axis.GetXaxis().SetNdivisions(5,5,0)
#h2_axis.GetYaxis().SetMoreLogLabels()
h2_axis.GetXaxis().SetLabelOffset(0.01)
h2_axis.GetXaxis().SetTickSize(0)
h2_axis.GetYaxis().SetNoExponent()
h2_axis.GetYaxis().SetTickLength(0.1)
h2_axis.Draw("SAME")

pads[1].cd()
binsx = array('f', map(float,sorted_keys)) 
h1_axis = ROOT.TH1D('h_axis','', len(binsx)-1, binsx)
h1_axis.SetStats(0)
h1_axis.GetYaxis().SetTitle(args.y_title)
h1_axis.GetXaxis().SetRangeUser(float(sorted_keys[0]),float(sorted_keys[-1]))
h1_axis.GetYaxis().SetRangeUser(y_upper_range[0],y_upper_range[1])
h1_axis.GetXaxis().SetTitleSize(0)
h1_axis.GetXaxis().SetLabelSize(0)
h1_axis.GetXaxis().SetTickSize(0)
h1_axis.GetYaxis().SetTickLength(0.1)
h1_axis.Draw("SAME")


copy_expm1 = {}
copy_expp1 = {}
copy_expp2 = {}
graph = {}
for p in [1,2]:
  pads[p].cd()
  fillstyle = 'FSAME'

  import copy
  if 'exp2' in args.contours:
    plot.Set(contours['exp-2'], LineColor=0, FillColor=plot.CreateTransparentColor(ROOT.kGray + 0,0.9), FillStyle=1001)
    contours['exp-2'].Draw(fillstyle)
    copy_expm1[p] = copy.deepcopy(contours['exp-1'])
    copy_expm1[p].SetName("copy_expm1_"+str(p))
    plot.Set(copy_expm1[p], LineColor=0, FillColor=plot.CreateTransparentColor(ROOT.kWhite,1.0), FillStyle=1001)
    copy_expm1[p].Draw(fillstyle)
  if 'exp1' in args.contours:
    plot.Set(contours['exp-1'], LineColor=0, FillColor=plot.CreateTransparentColor(ROOT.kGray + 1,0.9), FillStyle=1001)
    contours['exp-1'].Draw(fillstyle)
    copy_expp1[p] = copy.deepcopy(contours['exp+1'])
    copy_expp1[p].SetName("copy_expp1_"+str(p))
    plot.Set(copy_expp1[p], LineColor=0, FillColor=plot.CreateTransparentColor(ROOT.kWhite,1.0), FillStyle=1001)
    copy_expp1[p].Draw(fillstyle)
  if 'exp2' in args.contours:
    plot.Set(contours['exp+1'], LineColor=0, FillColor=plot.CreateTransparentColor(ROOT.kGray + 0,0.9), FillStyle=1001)
    contours['exp+1'].Draw(fillstyle)
    copy_expp2[p] = copy.deepcopy(contours['exp+2'])
    copy_expp2[p].SetName("copy_expp2_"+str(p))
    plot.Set(copy_expp2[p], LineColor=0, FillColor=plot.CreateTransparentColor(ROOT.kWhite,1.0), FillStyle=1001)
    copy_expp2[p].Draw(fillstyle)

  if 'exp0' in args.contours:
    if 'obs' in args.contours:
      plot.Set(contours["exp0"], LineColor=ROOT.kBlack, LineStyle=2)
      contours["exp0"].Draw('LSAME')
    else:
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

  ## Draw excluded regions
  #if args.excluded_mass != "" and p == 2:
  #  #excluded_file = ROOT.TFile("input/excluded_contours.root")
  #  excluded_file = ROOT.TFile("input/excluded_contours_v2.root")
  #  excl_cont = excluded_file.Get("mphi"+args.excluded_mass)
  #  plot.Set(excl_cont, LineColor=2, FillColor=plot.CreateTransparentColor(2,0.2), FillStyle=1001)
  #  #plot.Set(excl_cont, LineColor=2, FillColor=plot.CreateTransparentColor(2,1.0), FillStyle=3004)
  #  excl_cont.Draw('FSAME')
  #  excl_cont.Draw("LSAME")

  # Draw excluded regions
  if args.excluded_mass != "" and p == 2:
    excluded_file = ROOT.TFile("input/typeX_BRs.root")

    for i in range(1,5):

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

  if args.box_allowed != None:
    n_points = args.box_allowed.count("(")
    graph[p] = ROOT.TGraph(n_points+1)
    for i in range(n_points):
      point = args.box_allowed.split("(")[i+1].split(")")[0].split(",")
      graph[p].SetPoint(i, float(point[0]), float(point[1]))
    point_end = args.box_allowed.split("(")[1].split(")")[0].split(",")
    graph[p].SetPoint(n_points, float(point_end[0]), float(point_end[1]))
    #plot.Set(graph[p], LineColor=8, FillColor=plot.CreateTransparentColor(8,0.2), FillStyle=1001)
    plot.Set(graph[p], LineColor=ROOT.kGreen+3, FillColor=plot.CreateTransparentColor(ROOT.kGreen+3,0.2), FillStyle=1001)
    #plot.Set(graph[p], LineColor=8, FillColor=plot.CreateTransparentColor(8,1.0), FillStyle=3004)
    graph[p].Draw('FSAME')
    graph[p].Draw("LSAME")


pads[0].cd()
h_top = h1_axis.Clone()
plot.Set(h_top.GetXaxis(), LabelSize=0, TitleSize=0, TickLength=0)
plot.Set(h_top.GetYaxis(), LabelSize=0, TitleSize=0, TickLength=0)
h_top.Draw()

# Draw the legend in the top TPad
#legend = plot.PositionedLegend(0.5, 0.15, 3, 0.015)
legend = plot.PositionedLegend(0.5, 0.145, 3, 0.005)

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

legend.Draw()

if args.box_allowed != None:
  legend1 = plot.PositionedLegend(0.5, 0.08, 6, 0.004, horizontaloffset=0.0)
  plot.Set(legend1, NColumns=2, Header='#bf{%.0f%% CL allowed:}' % (95.))
  legend1.SetTextSize(0.027)
  #legend1.SetColumnSeparation(-0.0)  
  legend1.AddEntry(graph[1], "Muon g-2: Phys. Rev. D 104, 095008", "F")
  legend1.Draw()

# Draw logos and titles
plot.DrawCMSLogo(pads[0], 'CMS', args.cms_sub, 11, 0.045, 0.15, 1.0, '', 1.0)
plot.DrawTitle(pads[0], args.title_right, 3)
plot.DrawTitle(pads[0], args.title_left, 1)


# Redraw the frame because it usually gets covered by the filled areas
pads[1].cd()
pads[1].GetFrame().Draw()
pads[1].RedrawAxis()

pads[2].cd()
pads[2].GetFrame().Draw()
pads[2].RedrawAxis()


# Draw the scenario label
pads[1].cd()
latex = ROOT.TLatex()
latex.SetNDC()
latex.SetTextAngle(90)
latex.SetTextSize(0.03)
latex.DrawLatex(0.93, sum(segments[2:]) - 0.10, "Linear")

pads[2].cd()
latex = ROOT.TLatex()
latex.SetNDC()
latex.SetTextAngle(90)
latex.SetTextSize(0.03)
latex.DrawLatex(0.93, sum(segments[3:]) - 0.07, "Log")

# Draw the log and linear scales
pads[1].cd()
latex = ROOT.TLatex()
latex.SetNDC()
latex.SetTextSize(0.04)
latex.DrawLatex(0.18, sum(segments[2:]) + 0.018, args.scenario_label)

#plot.DrawTitle(pads[1], args.scenario_label, 1, textSize=0.12,textOffset=0.05)

canv.Print('.pdf')
canv.Print('.png')
canv.Close()

