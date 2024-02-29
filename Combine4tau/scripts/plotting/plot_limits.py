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
parser.add_option('--channel',help= 'Name of input channels', default='tttt')
parser.add_option('--folder', help= 'Folder for processing', default='output')
parser.add_option('--year', help= 'Year for processing', default='all')
parser.add_option('--MA', help='Mass of A to run limits for', default='100')
(options, args) = parser.parse_args()

# initialising variables
folder = options.folder
channel = options.channel
year = options.year
mA = options.MA

style_dict = {
        'style' : {
            'obs' : { 'LineWidth' : 2},
            'exp0' : { 'LineColor' : ROOT.kBlack, 'LineStyle' : 2},
            'exp1' : { 'FillColor' : ROOT.kGreen+1},
            'exp2' : { 'FillColor' : ROOT.kOrange},
            },
        'legend' : {
            'obs' : { 'Label' : 'Observed', 'LegendStyle' : 'LP', 'DrawStyle' : 'PLSAME'},
            'exp0' : { 'Label' : 'Expected', 'LegendStyle' : 'L', 'DrawStyle' : 'LSAME'},
            'exp1' : { 'Label' : '68% Expected', 'LegendStyle' : 'F', 'DrawStyle' : '3SAME'},
            'exp2' : { 'Label' : '95% Expected', 'LegendStyle' : 'F', 'DrawStyle' : '3SAME'},
            }
        }

# Style and pads
ModTDRStyle()
canv = ROOT.TCanvas('limit', 'limit')
pads = OnePad()

# Get limit TGraphs as a dictionary
graphs = StandardLimitsFromJSONFile_wScaling(options.folder+'/'+options.year+'/'+options.channel+'/limits/A'+ options.MA + '/limit_A' + options.MA + '.json',0.1,draw=['obs','exp0', 'exp1','exp2'])

# Create an empty TH1 from the first TGraph to serve as the pad axis and frame
axis = CreateAxisHist(graphs.values()[0])
axis.GetXaxis().SetTitle('m_{#phi} (GeV)')

axis.GetYaxis().SetTitle('95% CL Limit on #sigma #times BR(#phi#rightarrow#tau#tau) #times BR(A#rightarrow#tau#tau) (fb)')
axis.GetYaxis().SetTitleOffset(1.1)
axis.GetXaxis().SetTitleOffset(1.25)
axis.GetYaxis().SetTitleSize(0.045)
axis.GetXaxis().SetTitleSize(0.045)
axis.GetYaxis().SetLabelSize(0.035)
axis.GetXaxis().SetLabelSize(0.035)
axis.GetYaxis().SetLabelOffset(0.01)
axis.GetXaxis().SetLabelOffset(0.02)


pads[0].cd()
axis.Draw('axis')

# Create a legend in the top left
legend = PositionedLegend(0.3, 0.2, 3, 0.015)

# Set the standard green and yellow colors and draw
StyleLimitBand(graphs,overwrite_style_dict=style_dict["style"])
DrawLimitBand(pads[0], graphs,draw=['exp2','exp1','exp0','obs'], legend=legend,legend_overwrite=style_dict["legend"])
legend.Draw()

# Re-draw the frame and tick marks
pads[0].RedrawAxis()
pads[0].GetFrame().Draw()
pads[0].SetTicks()

# Adjust the y-axis range such that the maximum graph value sits 25% below
# the top of the frame. Fix the minimum to zero.
FixBothRanges(pads[0], 0, 0, GetPadYMax(pads[0]), 0.25)

# Standard CMS logo
DrawCMSLogo(pads[0], 'CMS', 'Supplementary', 11, 0.045, 0.035, 1.2, '', 0.8)
MA = options.MA

DrawTitle(pads[0], "m_{A} = %(MA)s GeV"%vars(), 1)
DrawTitle(pads[0], "138 fb^{-1} (13 TeV)", 3)

latex = ROOT.TLatex()
latex.SetNDC()
latex.SetTextAngle(0)
latex.SetTextAlign(12)
latex.SetTextFont(42)
latex.SetTextSize(0.04)

canv.Print('plots/{}_A{}_limit.pdf'.format(options.channel,options.MA))
#canv.Print('test1.pdf')
#canv.Print('1.png')

