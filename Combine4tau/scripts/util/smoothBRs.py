import ROOT
import CombineHarvester.CombineTools.plotting as plot
import copy

phi_masses = ["60","70","80","90","100","110","125","140","160","180","200","250","300","400","600","800"]
#phi_masses = ["60","70","80","90","100","110","140","160","180","200","250","300","400","600","800"]
#phi_masses = ["140","200"]


def InterpolateHist(hist, x_points=400, y_points=400):

  from scipy.spatial import Delaunay
  from scipy.interpolate import LinearNDInterpolator
  from array import array
  import numpy as np
  import warnings

  warnings.filterwarnings("ignore", category=RuntimeWarning)

  hist_x_bins = list(np.linspace(hist.GetXaxis().GetBinLowEdge(1), hist.GetXaxis().GetBinLowEdge(hist.GetNbinsX()), num=x_points))
  hist_y_bins = list(np.linspace(hist.GetYaxis().GetBinLowEdge(1), hist.GetYaxis().GetBinLowEdge(hist.GetNbinsY()), num=y_points))

  X = []
  Y = []
  Z = []
  for i in range(hist.GetNbinsX()+1):
    for j in range(hist.GetNbinsY()+1):
      X.append(hist.GetXaxis().GetBinCenter(i))
      Y.append(hist.GetYaxis().GetBinCenter(j))
      Z.append(hist.GetBinContent(i,j))
      #print(hist.GetXaxis().GetBinCenter(i), hist.GetYaxis().GetBinCenter(j), hist.GetBinContent(i,j))
  tri = Delaunay(np.column_stack((X, Y)))
  del_interp = LinearNDInterpolator(tri, Z)
  hout = ROOT.TH2D(hist.GetName(),'',len(hist_x_bins)-1, array('f', map(float,hist_x_bins)),len(hist_y_bins)-1, array('f', map(float,hist_y_bins)))

  for i in range(hout.GetNbinsX()+1):
    for j in range(hout.GetNbinsY()+1):
      interp = del_interp(hout.GetXaxis().GetBinCenter(i),hout.GetYaxis().GetBinCenter(j))
      if np.isnan(interp):
        interp = 0.0
      else:
        interp = float(max(min(interp,1.0),0.0))
      hout.SetBinContent(i,j,interp)
  return hout


hists = []
for phi_mass in phi_masses:

  if phi_mass in ["60","70","80","90","100","110","125","140","160","180","200","250","300","400"]:
    rootfile = ROOT.TFile.Open("input/typeX_mphi"+phi_mass+"_more_tanb.root")
  else:
    rootfile = ROOT.TFile.Open("input/typeX_mphi"+phi_mass+".root")

  # Get histograms
  if int(phi_mass) < 125:
    phi = "h"
  else:
    phi = "H"

  phi_decay = rootfile.Get("br_mphi%(phi_mass)sp0_csbma0p0_%(phi)s_to_tautau" % vars())
  A_decay = rootfile.Get("br_mphi%(phi_mass)sp0_csbma0p0_A_to_tautau" % vars())    

  # Multiply histograms
  A_and_phi_decay = A_decay.Clone()
  A_and_phi_decay.SetName("brs_mphi%(phi_mass)sp0" % vars())
  A_and_phi_decay.Multiply(phi_decay)

  # Interpolate A_and_phi_decay
  #hists.append(copy.deepcopy(A_and_phi_decay))
  A_and_phi_decay.Smooth()
  A_and_phi_decay_interp = InterpolateHist(A_and_phi_decay)
  hists.append(copy.deepcopy(A_and_phi_decay_interp))

  # Make higgs tools exclusion also
  hs = rootfile.Get("exp_exc_hs_mphi%(phi_mass)sp0_csbma0p0" % vars())
  hs.SetName("exp_exc_hs_mphi%(phi_mass)sp0" % vars())
  hb = rootfile.Get("exp_exc_hb_mphi%(phi_mass)sp0_csbma0p0" % vars())
  hb.SetName("exp_exc_hb_mphi%(phi_mass)sp0" % vars())
  ht = hs.Clone()
  ht.SetName("exp_exc_mphi%(phi_mass)sp0" % vars())
  for i in range(0, ht.GetNbinsX()+1):
    for j in range(0,ht.GetNbinsY()+1):
      if hs.GetBinContent(i,j) > 0.5 or hb.GetBinContent(i,j) > 0.5:
        ht.SetBinContent(i,j,0)
      else:
        ht.SetBinContent(i,j,1)

  for i in range(0, ht.GetNbinsX()+1):
    exc = False
    for j in range(ht.GetNbinsY(),-1,-1):
      if ht.GetBinContent(i,j) == 0 and not exc:
        exc = True
      if exc:
        ht.SetBinContent(i,j,0)

  # Interpolate ht
  #hists.append(copy.deepcopy(ht))

  ht.Smooth()
  ht_interp = InterpolateHist(ht)
  hists.append(copy.deepcopy(ht_interp))

  hists.append(copy.deepcopy(hs))
  hists.append(copy.deepcopy(hb))

  cont = plot.contourFromTH2(ht_interp,0.5)
  for contour_index in range(cont.GetSize()):
    contour = cont.At(contour_index)
    contour.SetName("contour_"+ht.GetName()+"_"+str(contour_index+1))
    hists.append(copy.deepcopy(contour))

  rootfile.Close()

output_file = ROOT.TFile("input/typeX_BRs.root", "RECREATE")
output_file.cd()
for hist in hists:
  hist.Write()
output_file.Close()