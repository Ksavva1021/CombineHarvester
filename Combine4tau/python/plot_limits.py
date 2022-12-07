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
parser.add_option('--grid_A', help= 'Grid of A Masses', default='60,70,80,90,100,125,140,160')
parser.add_option('--xs_file', help='Cross-sections', default="/vols/cms/ks1021/4tau/CMSSW_10_2_19/src/UserCode/ICHiggsTauTau/Analysis/4tau/scripts/xs_inputs_2018_UL.txt")
(options, args) = parser.parse_args()

# initialising variables
folder = options.folder
channel = options.channel
year = options.year
grid_A = options.grid_A.split(',')
input_xs = open(options.xs_file, "r")
mA = options.MA
xs_list=[word for line in input_xs for word in line.split()]

xs = {}
for A in grid_A:
   temp_xs = []
   temp_phi = []
   for i in range(len(xs_list)):
      if "Zstar" in xs_list[i]:
         split = re.split('(\d+)', xs_list[i])
         mPhi = split[1]
         mA_ = split[3]
         if A == mA_:
            temp_xs.append(xs_list[i+1])
            temp_phi.append(mPhi)
   xs["mA{}".format(A)] = [temp_xs,temp_phi] 


def PlotXS(xs,A): 
   xvals = xs['mA{}'.format(A)][1]
   yvals = xs['mA{}'.format(A)][0]

   xvals = np.asarray(xvals,dtype=float)
   yvals = np.asarray(yvals,dtype=float)
   graph = R.TGraph(len(xvals), array('d', xvals), array('d', yvals))
   graph.Sort()
   return graph


style_dict = {
        'style' : {
            'exp0' : { 'LineColor' : ROOT.kBlack, 'LineStyle' : 2},
            'exp1' : { 'FillColor' : ROOT.kGreen+1, 'FillColorAlpha' : [ROOT.kGreen+1,0.5]},
            'exp2' : { 'FillColor' : ROOT.kOrange, 'FillColorAlpha' : [ROOT.kOrange,0.5]},
            'xs'   : { 'LineColor' : ROOT.kBlue, 'LineStyle' : 2}
            },
        'legend' : {
            'exp0' : { 'Label' : 'Expected', 'LegendStyle' : 'L', 'DrawStyle' : 'LSAME'},
            'exp1' : { 'Label' : '#pm 1 #sigma Expected', 'LegendStyle' : 'F', 'DrawStyle' : '3SAME'},
            'exp2' : { 'Label' : '#pm 2 #sigma Expected', 'LegendStyle' : 'F', 'DrawStyle' : '3SAME'},
            'xs'   : { 'Label' : 'xs','LegendStyle' : 'L', 'DrawStyle' : 'LSAME'}
            }
        }

# Style and pads
ModTDRStyle()
canv = ROOT.TCanvas('limit', 'limit')
pads = OnePad()

# Get limit TGraphs as a dictionary
print("Channel:",channel,"MA:", mA)
graphs = StandardLimitsFromJSONFile('%(folder)s/%(year)s/%(channel)s/limit_m%(mA)s.json'%vars(),draw=['exp0', 'exp1', 'exp2'])
graphs["xs"] = PlotXS(xs,mA)

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
DrawLimitBand(pads[0], graphs,draw=['exp0','exp1','exp2','xs'], legend=legend,legend_overwrite=style_dict["legend"])
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


canv.Print('%(folder)s/%(year)s/%(channel)s/limit_plot_m%(mA)s.pdf'%vars())
canv.Print('%(folder)s/%(year)s/%(channel)s/limit_plot_m%(mA)s.png'%vars())
