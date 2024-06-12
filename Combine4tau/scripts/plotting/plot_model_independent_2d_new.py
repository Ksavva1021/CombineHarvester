import os
import ROOT
import json
import copy
import numpy as np
from array import array
from optparse import OptionParser
from CombineHarvester.CombineTools.plotting import *
from scipy.interpolate import griddata

parser = OptionParser()
parser.add_option('--folder', help= 'Folder for processing', default='output')
parser.add_option('--mphi-minus-mA', help='Do mphi - mA x axis', action='store_true')
parser.add_option('--logx', help='Do log x', action='store_true')
parser.add_option('--logy', help='Do log y', action='store_true')
parser.add_option('--logz', help='Do log z', action='store_true')
(options, args) = parser.parse_args()
  
def find_max_coordinates(hist2d, target_z, fractional_error):
  # Initialize variables to store the result
  max_x = None
  max_y = None

  # Iterate over each bin in the histogram
  for xbin in range(1, hist2d.GetNbinsX() + 1):
    for ybin in range(1, hist2d.GetNbinsY() + 1):
      # Get the bin content and coordinates
      z = hist2d.GetBinContent(xbin, ybin)
      x = hist2d.GetXaxis().GetBinCenter(xbin)
      y = hist2d.GetYaxis().GetBinCenter(ybin)
      
      # Check if the z value is close to the target z value
      if abs(z - target_z) / target_z <= fractional_error:
        # Update the maximum x and y values
        if max_x is None or x > max_x:
          max_x = x
          max_y = y

  return max_x, max_y

def find_median_xy_and_angle(hist2d, z_value, fractional_error, bins_for_angle=5, bins_shift=-1.4):

  x_values = []
  y_values = []

  for ix in range(1, hist2d.GetNbinsX() + 1):
    for iy in range(1, hist2d.GetNbinsY() + 1):
      bin_content = hist2d.GetBinContent(ix, iy)
      if np.abs(bin_content - z_value) <= z_value*fractional_error:
        x_values.append(hist2d.GetXaxis().GetBinCenter(ix))
        y_values.append(hist2d.GetYaxis().GetBinCenter(iy))

  median_x = np.median(x_values)
  ind_median = int(len(x_values)/2)
  median_y = y_values[ind_median]

  ind_median_before = ind_median - bins_for_angle
  ind_median_after = ind_median + bins_for_angle

  y_before = y_values[max(ind_median_before,0):ind_median]
  y_after = y_values[max(ind_median,0):ind_median_after]
  x_before = x_values[max(ind_median_before,0):ind_median]
  x_after = x_values[max(ind_median,0):ind_median_after]

  sum_y_before = np.sum(y_before)/len(y_before)
  sum_y_after = np.sum(y_after)/len(y_after)
  sum_x_before = np.sum(x_before)/len(x_before)
  sum_x_after = np.sum(x_after)/len(x_after)

  grad = (sum_y_after-sum_y_before)/(sum_x_after-sum_x_before)
  angle_rad = np.arctan(grad)
  angle_deg = np.degrees(angle_rad)

  x_bin = hist2d.GetXaxis().FindBin(median_x) + bins_shift*np.cos(-1/grad)
  y_bin = hist2d.GetYaxis().FindBin(median_y) + bins_shift*np.sin(-1/grad)

  x = hist2d.GetXaxis().GetBinCenter(int(x_bin))
  y = hist2d.GetYaxis().GetBinCenter(int(y_bin))

  return x, y, angle_deg


bins_phi = [60,70,80,90,100,110,125,140,160,180,200,250,300,400,600,800]
bins_A = [40,50,60,70,80,90,100,125,140,160,200,250,300,400,600]

cont = "obs"

bins = 100
start_A = bins_A[0]
end_A = bins_A[-1]
start_phi = bins_phi[0]
end_phi = bins_phi[-1]
num_bins = bins

if options.logx:
  new_bins_A = list(np.logspace(np.log10(start_A), np.log10(end_A), num=num_bins))
else:
  new_bins_A = list(np.linspace(bins_A[0],bins_A[-1],num=bins))

if options.logy:
  new_bins_phi = list(np.logspace(np.log10(start_phi), np.log10(end_phi), num=num_bins))
else:
  new_bins_phi = list(np.linspace(bins_phi[0],bins_phi[-1],num=bins))

new_bin_centers_A = [(new_bins_A[i]+new_bins_A[i+1])/2 for i in range(len(new_bins_A)-1)]
new_bin_centers_phi = [(new_bins_phi[i]+new_bins_phi[i+1])/2 for i in range(len(new_bins_phi)-1)]

hout = ROOT.TH2D('hout','',len(new_bins_A)-1, array('f', map(float,new_bins_A)),len(new_bins_phi)-1, array('f', map(float,new_bins_phi)))
hnans = ROOT.TH2F('hnans','',len(new_bins_A)-1, array('f', map(float,new_bins_A)),len(new_bins_phi)-1, array('f', map(float,new_bins_phi)))


x = []
y = []
z = []
for bA in bins_A:
  params_file = options.folder+'/all/A_'+ str(bA) + '/cmb/limits/limit_limits.json'
  with open(params_file) as jsonfile: params = json.load(jsonfile)
  for bphi in bins_phi:
    if str(float(bphi)) in params.keys():
      if not options.mphi_minus_mA: 
        x.append(bA)
      else:
        x.append(bphi - bA)
      y.append(bphi)
      z.append(params[str(float(bphi))][cont])

for xi in new_bin_centers_A:
  for yi in new_bin_centers_phi:
    zi = float(griddata((x, y), z, (xi, yi), method='cubic'))
    bin_index_x = hout.GetXaxis().FindBin(xi)
    bin_index_y = hout.GetYaxis().FindBin(yi)
    if not np.isnan(zi):
      hout.SetBinContent(bin_index_x, bin_index_y, zi)
      hnans.SetBinContent(bin_index_x, bin_index_y, 1)
    else:
      hnans.SetBinContent(bin_index_x, bin_index_y, 0)

c = ROOT.TCanvas('c','c',700,700)
c.SetLeftMargin(0.15)
c.SetRightMargin(0.25)
c.SetBottomMargin(0.15)
if options.logz: c.SetLogz()
if options.logx: c.SetLogx()
if options.logy: c.SetLogy()
ROOT.gPad.SetTicks(1, 1)
#hout.SetMaximum(20.0001) # so labels show up
#hout.SetMinimum(0.9999)
ROOT.gStyle.SetPalette(ROOT.kViridis)
hout.Draw("COLZ")
hout.SetContour(255)
hout.SetStats(0)

cont_vals = [0.1, 0.2, 0.3, 1, 3, 10]

cont = copy.deepcopy(hout)
cont.SetContour(len(cont_vals), array('d', cont_vals))
cont.SetLineColor(ROOT.kBlack)
cont.Draw("cont3 LIST same")

legend = PositionedLegend(0.3, 0.08, 1, 0.015)

# Hashed contour
first_loop = True
conts = contourFromTH2(hnans, 0.5)
x_min = hout.GetXaxis().GetXmin()
x_max = hout.GetXaxis().GetXmax()
y_min = hout.GetYaxis().GetXmin()
y_max = hout.GetYaxis().GetXmax()
for obj in conts:
  for i in range(obj.GetN()):
    x, y = ROOT.Double(0), ROOT.Double(0)
    obj.GetPoint(i, x, y)
    factor = 0.01
    if x <= x_min:
      x -= factor
    elif x >= x_max:
      x += factor
    if y <= y_min:
      y -= factor
    elif y >= y_max:
      y += factor
    obj.SetPoint(i, x, y)
  obj.Draw("FL same")
  obj.SetFillStyle(3004)
  obj.SetFillColor(ROOT.kRed)
  obj.SetLineColor(ROOT.kRed)
  obj.SetLineWidth(4)
  if first_loop:
    legend.AddEntry(obj, "Out of mass range", "F")
    first_loop = False

# Legend
legend.Draw()


for cont_val in cont_vals:
  x, y, angle_deg = find_median_xy_and_angle(hout, cont_val, 0.05, bins_for_angle=20)
  bin_index_x = hout.GetXaxis().FindBin(x)
  bin_index_y = hout.GetYaxis().FindBin(y)
  latex = ROOT.TLatex()
  latex.SetTextSize(0.025)
  latex.SetTextAlign(22)
  latex.SetTextAngle(angle_deg)
  latex.DrawLatex(hout.GetXaxis().GetBinLowEdge(bin_index_x), hout.GetYaxis().GetBinLowEdge(bin_index_y), str(cont_val)+" fb")  


if options.logx:
  hout.GetXaxis().SetMoreLogLabels()
  hout.GetXaxis().SetNoExponent()
if options.logy:
  hout.GetYaxis().SetMoreLogLabels()
  hout.GetYaxis().SetNoExponent()
if options.logz:
  hout.GetZaxis().SetMoreLogLabels()
  hout.GetZaxis().SetNoExponent()
hout.GetYaxis().SetTitle("m_{#phi} (GeV)")
if not options.mphi_minus_mA:
  hout.GetXaxis().SetTitle("m_{A} (GeV)")
else:
  hout.GetXaxis().SetTitle("m_{#phi} - m_{A} (GeV)")
hout.GetZaxis().SetTitle("95% CL upper limits on #sigma #times BR(#phi#rightarrow#tau#tau) #times BR(A#rightarrow#tau#tau) (fb)")

DrawTitle(c, "138 fb^{-1} (13 TeV)", 3, textSize=0.35)
DrawCMSLogo(c, 'CMS','', 1, 0.14, -0.055, 0, '', 0.4)

hout.GetXaxis().SetNdivisions(5)
hout.GetYaxis().SetNdivisions(5)
hout.GetZaxis().SetNdivisions(20)

hout.GetXaxis().SetTitleSize(0.04)
hout.GetXaxis().SetTitleOffset(1.4)

hout.GetYaxis().SetTitleSize(0.04)
hout.GetYaxis().SetTitleOffset(1.4)

hout.GetZaxis().SetTitleSize(0.035)
hout.GetZaxis().SetTitleOffset(1.8)

c.Print('mi_plots/mi_2d.pdf')
c.Print('mi_plots/mi_2d.png')
