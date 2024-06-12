import os
import ROOT
import json
import copy
import numpy as np
from array import array
from optparse import OptionParser
from CombineHarvester.CombineTools.plotting import *

parser = OptionParser()
parser.add_option('--folder', help= 'Folder for processing', default='output')
(options, args) = parser.parse_args()


def InterpolationFromBinEdges(x,y,x1,x2,y1,y2,f11,f12,f21,f22):

  t1 = ((float(y2)-float(y))/(float(y2)-float(y1)))
  t2 = ((float(x2)-float(x))/(float(x2)-float(x1)))*f11
  t3 = ((float(x)-float(x1))/(float(x2)-float(x1)))*f21
  t4 = ((float(y)-float(y1))/(float(y2)-float(y1)))
  t5 = ((float(x2)-float(x))/(float(x2)-float(x1)))*f12
  t6 = ((float(x)-float(x1))/(float(x2)-float(x1)))*f22

  return (t1*(t2+t3)) + (t4*(t5+t6))

def find_closest(numbers, target):
  numbers_sorted = sorted(numbers)
  closest_higher = numbers[-1]
  closest_lower = None
  for number in numbers_sorted:
    if number >= target:
      closest_higher = number
      break
    closest_lower = number
  return closest_lower, closest_higher


bins_phi = [60,70,80,90,100,110,125,140,160,180,200,250,300,400,600,800]
bins_A = [40,50,60,70,80,90,100,125,140,160,200,250,300,400,600]

cont = "obs"

bins = 100
new_bins_A = list(np.linspace(bins_A[0],bins_A[-1],num=bins))
new_bins_phi = list(np.linspace(bins_phi[0],bins_phi[-1],num=bins))

#hout = ROOT.TH2D('hout','',len(new_bins_phi)-1, array('f', map(float,new_bins_phi)),len(new_bins_A)-1, array('f', map(float,new_bins_A)))

hout = ROOT.TH2D('hout','',len(new_bins_A)-1, array('f', map(float,new_bins_A)),len(new_bins_phi)-1, array('f', map(float,new_bins_phi)))


for bA in range(1,hout.GetNbinsX()+1):
  y = hout.GetXaxis().GetBinCenter(bA)
  y1, y2 = find_closest(bins_A,y)

  params_file_down = options.folder+'/all/A_'+ str(y1) + '/cmb/limits/limit_limits.json'
  params_file_up = options.folder+'/all/A_'+ str(y2) + '/cmb/limits/limit_limits.json'
  #params_file_down = options.folder+'/all/cmb/limits/A'+ str(y1) + '/model_independent/limit_model_independent.json'
  #params_file_up = options.folder+'/all/cmb/limits/A'+ str(y2) + '/model_independent/limit_model_independent.json'
  with open(params_file_down) as jsonfile: params_down = json.load(jsonfile)
  with open(params_file_up) as jsonfile: params_up = json.load(jsonfile)

  for bphi in range(1,hout.GetNbinsY()+1):

    x = hout.GetYaxis().GetBinCenter(bphi)
    x1, x2 = find_closest(bins_phi,x) 

    if not (not any(str(float(x1)) not in d.keys() for d in [params_down, params_up]) and not any(str(float(x2)) not in d.keys() for d in [params_down, params_up])):
      hout.SetBinContent(bA,bphi,0)
    else:
      f11 = params_down[str(float(x1))][cont]
      f12 = params_up[str(float(x1))][cont]
      f21 = params_down[str(float(x2))][cont]
      f22 = params_up[str(float(x2))][cont]
      hout.SetBinContent(bA,bphi,10.0*InterpolationFromBinEdges(x,y,x1,x2,y1,y2,f11,f12,f21,f22))
  

ROOT.gStyle.SetPalette(ROOT.kRainBow)

c = ROOT.TCanvas('c','c',700,700)
c.SetLeftMargin(0.15)
c.SetRightMargin(0.25)
c.SetBottomMargin(0.15)
c.SetLogz()
#ROOT.gPad.SetTicks(0, 1)
hout.SetMaximum(20.0001) # so labels show up
hout.SetMinimum(0.9999)
hout.Draw("COLZ")
hout.SetContour(255)
hout.SetStats(0)

cont_vals = [2,3,4,6,8,12]

cont = copy.deepcopy(hout)
cont.SetContour(len(cont_vals), array('d', cont_vals))
cont.SetLineColor(ROOT.kBlack)
cont.Draw("cont3 same")

right_bin = cont.GetNbinsX() - 10

h_final_column_values = [cont.GetBinContent(right_bin, y) for y in range(1, cont.GetNbinsY() + 1)]
h_final_row_values = [cont.GetBinContent(x, 1) for x in range(1, cont.GetNbinsX() + 1)]

print(h_final_row_values)

for cont_val in cont_vals:

  print(cont_val, min(h_final_column_values), max(h_final_column_values), min(h_final_row_values), max(h_final_row_values))

  if cont_val > min(h_final_column_values) and cont_val < max(h_final_column_values):
    up_bins = 2
    left_bins = 3
    for ind in range(len(h_final_column_values)-1):
      if (cont_val > h_final_column_values[ind] and cont_val < h_final_column_values[ind+1]) or (cont_val < h_final_column_values[ind] and cont_val > h_final_column_values[ind+1]):
        print(cont_val, ind, cont.GetXaxis().GetBinLowEdge(right_bin), cont.GetYaxis().GetBinLowEdge(ind))
        latex = ROOT.TLatex()
        latex.SetTextSize(0.025)
        latex.SetTextAlign(22)  # Centered alignment
        latex.DrawLatex(cont.GetXaxis().GetBinLowEdge(cont.GetNbinsX()-left_bins), cont.GetYaxis().GetBinLowEdge(ind+up_bins), str(cont_val)+" fb")

  elif cont_val > min(h_final_row_values) and cont_val < max(h_final_row_values):
    up_bins = 2
    right_bins = 6
    for ind in range(len(h_final_row_values)-1):
      if (cont_val > h_final_row_values[ind] and cont_val < h_final_row_values[ind+1]) or (cont_val < h_final_row_values[ind] and cont_val > h_final_row_values[ind+1]):
        print(cont_val, ind, cont.GetXaxis().GetBinLowEdge(ind), cont.GetYaxis().GetBinLowEdge(1))
        latex = ROOT.TLatex()
        latex.SetTextSize(0.025)
        latex.SetTextAlign(22)  # Centered alignment
        latex.DrawLatex(cont.GetXaxis().GetBinLowEdge(ind+right_bins), cont.GetYaxis().GetBinLowEdge(1+up_bins), str(cont_val) + " fb")
# find latex value to draw title
# Need to figure out if it is on the x axis or the y axis


hout.GetZaxis().SetMoreLogLabels()
hout.GetZaxis().SetNoExponent()
hout.GetYaxis().SetTitle("m_{#phi} (GeV)")
hout.GetXaxis().SetTitle("m_{A} (GeV)")
hout.GetZaxis().SetTitle("95% CL Limit on #sigma #times BR(#phi#rightarrow#tau#tau) #times BR(A#rightarrow#tau#tau) (fb)")

DrawTitle(c, "138 fb^{-1} (13 TeV)", 3, textSize=0.35)
DrawCMSLogo(c, 'CMS','Preliminary', 1, 0.14, -0.055, 0, '', 0.4)


hout.GetXaxis().SetNdivisions(5)
hout.GetYaxis().SetNdivisions(5)
hout.GetZaxis().SetNdivisions(20)


hout.GetXaxis().SetTitleSize(0.04)
hout.GetXaxis().SetTitleOffset(1.4)

hout.GetYaxis().SetTitleSize(0.04)
hout.GetYaxis().SetTitleOffset(1.4)

hout.GetZaxis().SetTitleSize(0.04)
hout.GetZaxis().SetTitleOffset(1.6)

c.Print('mi_2d.pdf')
c.Print('mi_2d.png')
