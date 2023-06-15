# importing packages
import sys
from optparse import OptionParser
import os
import numpy as np
from datetime import datetime
import ROOT
from CombineHarvester.CombineTools.plotting import *
import re
ROOT.PyConfig.IgnoreCommandLineOptions = True
ROOT.gROOT.SetBatch(ROOT.kTRUE)

parser = OptionParser()
parser.add_option('--folder', help= 'Folder for processing', default='output')
(options, args) = parser.parse_args()


style_dict = {
        'style' : {
            'obs' : { 'LineWidth' : 2},
            'exp0' : { 'LineColor' : ROOT.kBlack, 'LineStyle' : 2},
            'exp1' : { 'FillColor' : ROOT.kGreen+1, 'FillColorAlpha' : [ROOT.kGreen+1,0.5]},
            'exp2' : { 'FillColor' : ROOT.kOrange, 'FillColorAlpha' : [ROOT.kOrange,0.5]},
            },
        'legend' : {
            'obs' : { 'Label' : 'Observed', 'LegendStyle' : 'LP', 'DrawStyle' : 'PLSAME'},
            'exp0' : { 'Label' : 'Expected', 'LegendStyle' : 'L', 'DrawStyle' : 'LSAME'},
            'exp1' : { 'Label' : '68% Expected', 'LegendStyle' : 'F', 'DrawStyle' : '3SAME'},
            'exp2' : { 'Label' : '95% Expected', 'LegendStyle' : 'F', 'DrawStyle' : '3SAME'},
            }
        }

style_dict1 = {
        'style' : {
            'exp0' : { 'LineColor' : ROOT.kBlue, 'LineStyle' : 2},
            'exp1' : { 'FillColor' : ROOT.kRed, 'FillColorAlpha' : [ROOT.kRed,0.5]},
            'exp2' : { 'FillColor' : ROOT.kOrange, 'FillColorAlpha' : [ROOT.kOrange,0.5]},
            },
        'legend' : {
            'exp0' : { 'Label' : 'Expected HN', 'LegendStyle' : 'L', 'DrawStyle' : 'LSAME'},
            'exp1' : { 'Label' : '68% Expected', 'LegendStyle' : 'F', 'DrawStyle' : '3SAME'},
            'exp2' : { 'Label' : '95% Expected', 'LegendStyle' : 'F', 'DrawStyle' : '3SAME'},
            }
        }

# Style and pads
ModTDRStyle()
canv = ROOT.TCanvas("limit","limit",700,900)
pads = OnePad()

# Get limit TGraphs as a dictionary

masses = sorted([int(f.split("A")[1]) for f in os.listdir(options.folder+"/all/cmb/limits/")])


first_loop = True
graphs = []
for ind, mass in enumerate(masses):

  print "Getting mass:", mass
  
  graphs.append(StandardLimitsFromJSONFile_wScaling(options.folder+'/all/cmb/limits/A'+ str(mass) + '/model_independent/limit_model_independent.json',100,draw=['obs','exp0', 'exp1','exp2']))
  #graphs.append(StandardLimitsFromJSONFile(options.folder+'/all/cmb/limits/A'+ str(mass) + '/limit_A' + str(mass) + '.json',draw=['obs','exp0', 'exp1','exp2']))
  #graphs.append(StandardLimitsFromJSONFile(options.folder+'/all/cmb/limits/A'+ str(mass) + '/limit_A' + str(mass) + '.json',draw=['exp0']))

  if first_loop:

    # Create an empty TH1 from the first TGraph to serve as the pad axis and frame
    axis_g = graphs[0].values()[0].Clone()
    axis_g.SetPoint(axis_g.GetN(),440,0.0)

    axis = CreateAxisHist(axis_g)
    axis.GetXaxis().SetTitle('m_{#phi} (GeV)')
    
    axis.GetYaxis().SetTitle('95% CL Limit on #sigma(pp#rightarrow Z* #rightarrow #phi A) #times BR(#phi#rightarrow#tau#tau) #times BR(A#rightarrow#tau#tau) (pb)')
    axis.GetYaxis().SetTitleOffset(1.75)
    axis.GetYaxis().SetTitleSize(0.04)
    axis.GetXaxis().SetTitleSize(0.04)
    axis.GetYaxis().SetLabelSize(0.03)
    axis.GetXaxis().SetLabelSize(0.03)

    axis.GetYaxis().SetRangeUser(10**(-10),12)

    pads[0].cd()
    pads[0].SetLogy()
    axis.Draw('axis')

    # Create a legend in the top left
    legend = PositionedLegend(0.3, 0.2, 3, 0.015)

    # Standard CMS logo
    #DrawCMSLogo(pads[0], 'CMS', 'Work in progress', 11, 0.045, 0.035, 1.2, '', 0.8)
    #DrawTitle(pads[0], "m_{A}=%(MA)s GeV"%vars(), 1)
    DrawTitle(pads[0], "138 fb^{-1} (13 TeV)", 3)


  scaling = (1/10.0)**ind

  for k, v in graphs[ind].items():
    for i in range(0,v.GetN()):
      graphs[ind][k].GetY()[i] *= scaling
      if k not in ["exp0","obs"]:
        graphs[ind][k].SetPointEYhigh(i,graphs[ind][k].GetErrorYhigh(i)*scaling)
        graphs[ind][k].SetPointEYlow(i,graphs[ind][k].GetErrorYlow(i)*scaling)


  latex = ROOT.TLatex()
  latex.SetNDC(False)
  #latex.SetTextAngle(0)
  latex.SetTextAlign(12)
  latex.SetTextFont(42)
  latex.SetTextSize(0.03)
  num = -1*ind
  latex.DrawLatex(310,graphs[ind]["exp0"].GetY()[graphs[ind]["exp0"].GetN()-1],"m_{A} = %(mass)i GeV (#times 10^{%(num)i})" % vars())


  # Set the standard green and yellow colors and draw
  StyleLimitBand(graphs[ind],overwrite_style_dict=style_dict["style"])
  DrawLimitBand(pads[0], graphs[ind],draw=['exp0','exp1','exp2','obs'], legend=legend if first_loop else None,legend_overwrite=style_dict["legend"] if first_loop else None)
  legend.Draw()

  if first_loop: first_loop = False

# Re-draw the frame and tick marks
pads[0].RedrawAxis()
pads[0].GetFrame().Draw()

# Adjust the y-axis range such that the maximum graph value sits 25% below
# the top of the frame. Fix the minimum to zero.
FixBothRanges(pads[0], 0, 0, GetPadYMax(pads[0]), 0.25)

#latex = ROOT.TLatex()
#latex.SetNDC()
#latex.SetTextAngle(0)
#latex.SetTextAlign(12)
#latex.SetTextFont(42)
#latex.SetTextSize(0.04)

canv.Print('plots/model_independent_limit_all.pdf')

