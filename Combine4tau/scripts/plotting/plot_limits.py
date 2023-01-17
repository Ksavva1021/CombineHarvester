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
            'exp0' : { 'LineColor' : ROOT.kBlack, 'LineStyle' : 2},
            'exp1' : { 'FillColor' : ROOT.kGreen+1, 'FillColorAlpha' : [ROOT.kGreen+1,0.5]},
            'exp2' : { 'FillColor' : ROOT.kOrange, 'FillColorAlpha' : [ROOT.kOrange,0.5]},
            },
        'legend' : {
            'exp0' : { 'Label' : 'Expected', 'LegendStyle' : 'L', 'DrawStyle' : 'LSAME'},
            'exp1' : { 'Label' : '#pm 1 #sigma Expected', 'LegendStyle' : 'F', 'DrawStyle' : '3SAME'},
            'exp2' : { 'Label' : '#pm 2 #sigma Expected', 'LegendStyle' : 'F', 'DrawStyle' : '3SAME'},
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
            'exp1' : { 'Label' : '#pm 1 #sigma Expected HN', 'LegendStyle' : 'F', 'DrawStyle' : '3SAME'},
            'exp2' : { 'Label' : '#pm 2 #sigma Expected', 'LegendStyle' : 'F', 'DrawStyle' : '3SAME'},
            }
        }

# Style and pads
ModTDRStyle()
canv = ROOT.TCanvas('limit', 'limit')
pads = OnePad()

# Get limit TGraphs as a dictionary
print("Channel:",channel,"MA:", mA)
graphs = StandardLimitsFromJSONFile('outputs/out_mt_tot/all/tttt_inclusive/limits/A60/AL_A60.json',draw=['exp0', 'exp1'])
graphs1 = StandardLimitsFromJSONFile('outputs/out_mt_tot/all/tttt_inclusive/limits/A60/HN_comb.json',draw=['exp0', 'exp1'])

# Create an empty TH1 from the first TGraph to serve as the pad axis and frame
axis = CreateAxisHist(graphs.values()[0])
axis.GetXaxis().SetTitle('m_{#phi} (GeV)')
axis.GetYaxis().SetTitle('95% CL limit')
pads[0].cd()
axis.Draw('axis')

# Create a legend in the top left
legend = PositionedLegend(0.3, 0.2, 3, 0.015)

# Set the standard green and yellow colors and draw
StyleLimitBand(graphs,overwrite_style_dict=style_dict["style"])
StyleLimitBand(graphs1,overwrite_style_dict=style_dict1["style"])
#DrawLimitBand(pads[0], graphs,draw=['exp0','exp1','exp2'], legend=legend,legend_overwrite=style_dict["legend"])
DrawLimitBand(pads[0], graphs,draw=['exp0','exp1'], legend=legend,legend_overwrite=style_dict["legend"])
DrawLimitBand(pads[0], graphs1,draw=['exp0','exp1'], legend=legend,legend_overwrite=style_dict1["legend"])
legend.Draw()

# Re-draw the frame and tick marks
pads[0].RedrawAxis()
pads[0].GetFrame().Draw()

# Adjust the y-axis range such that the maximum graph value sits 25% below
# the top of the frame. Fix the minimum to zero.
FixBothRanges(pads[0], 0, 0, GetPadYMax(pads[0]), 0.25)

# Standard CMS logo
DrawCMSLogo(pads[0], 'CMS', 'Internal', 11, 0.045, 0.035, 1.2, '', 0.8)

latex = ROOT.TLatex()
latex.SetNDC()
latex.SetTextAngle(0)
latex.SetTextAlign(12)
latex.SetTextFont(42)
latex.SetTextSize(0.04)

latex.DrawLatex(0.6,0.6,'mA = {}'.format(mA))
latex.DrawLatex(0.6,0.5,'{}'.format(channel))


canv.Print('1s.pdf')
canv.Print('1.png')
