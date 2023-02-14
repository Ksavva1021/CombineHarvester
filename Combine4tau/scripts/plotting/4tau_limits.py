#!/usr/bin/env python
import ROOT
import CombineHarvester.CombineTools.plotting as plot
import argparse
import sys

parser = argparse.ArgumentParser()

parser.add_argument(
    '--input', default='config/input_limits.txt', help="""Input txt file containing json files""")
parser.add_argument(
    '--output', '-o', default='limit', help="""Name of the output
    plot without file extension""")
parser.add_argument(
    '--show', default='exp,obs')
parser.add_argument(
    '--x-title', default='m_{#phi} (GeV)', help="""Title for the x-axis""")
parser.add_argument(
    '--y-title', default=None, help="""Title for the y-axis""")
parser.add_argument(
    '--cms-sub', default='Internal', help="""Text below the CMS logo""")
parser.add_argument(
    '--title-right', default='', help="""Right header text above the frame""")
parser.add_argument(
    '--title-left', default='', help="""Left header text above the frame""")
parser.add_argument(
    '--title-center', default='', help="""Center header text above the frame""")
parser.add_argument(
    '--logy', action='store_true', help="""Draw y-axis in log scale""")
parser.add_argument(
    '--logx', action='store_true', help="""Draw x-axis in log scale""")
args = parser.parse_args()

with open(args.input) as file:
    files = [line.rstrip() for line in file]
    
def DrawAxisHists(pads, axis_hists, def_pad=None):
    for i, pad in enumerate(pads):
        pad.cd()
        axis_hists[i].Draw('AXIS')
        axis_hists[i].Draw('AXIGSAME')
    if def_pad is not None:
        def_pad.cd()


## Boilerplate
ROOT.PyConfig.IgnoreCommandLineOptions = True
ROOT.gROOT.SetBatch(ROOT.kTRUE)
plot.ModTDRStyle()
ROOT.gStyle.SetNdivisions(510, 'XYZ') # probably looks better

canv = ROOT.TCanvas(args.output, args.output)
pads = plot.OnePad()

# Set the style options of the pads
for padx in pads:
    # Use tick marks on oppsite axis edges
    plot.Set(padx, Tickx=1, Ticky=1, Logx=args.logx)

graphs = []
graph_sets = []

legend = plot.PositionedLegend(0.45, 0.10, 3, 0.015)
plot.Set(legend, NColumns=2)

defcols = [
    ROOT.kGreen+3, ROOT.kRed, ROOT.kBlue, ROOT.kBlack, ROOT.kYellow+2,
    ROOT.kOrange+10, ROOT.kCyan+3, ROOT.kMagenta+2, ROOT.kViolet-5, ROOT.kGray
    ]
    
print(defcols)
axis = None


for src in files:
   splitsrc = src.split(':')
   file = splitsrc[0]
   if (len(splitsrc) == 1):
        graph_sets.append(plot.StandardLimitsFromJSONFile(file, args.show.split(',')))
        if axis is None:
            axis = plot.CreateAxisHists(len(pads), graph_sets[-1].values()[0], True)
            DrawAxisHists(pads, axis, pads[0])
        plot.StyleLimitBand(graph_sets[-1])
        plot.DrawLimitBand(pads[0], graph_sets[-1], legend=legend)
        pads[0].RedrawAxis()
        pads[0].RedrawAxis('g')
        pads[0].GetFrame().Draw()

    # limit.json:X => Draw a single graph for entry X in the json file 
    # 'limit.json:X:Title="Blah",LineColor=4,...' =>
    # as before but also apply style options to TGraph
   elif len(splitsrc) >= 2:
       settings = {}
       graphs.append(plot.LimitTGraphFromJSONFile(file, splitsrc[1]))
       for x in splitsrc[2:]:
         setting = x.split("=",1)
         if setting[0]!= "Title":
           settings["{}".format(setting[0])] = int(setting[1])
         else:
           settings["{}".format(setting[0])] = setting[1]
              
       plot.Set(graphs[-1], **settings)
       if axis is None:
           axis = plot.CreateAxisHists(len(pads), graphs[-1], True)
           DrawAxisHists(pads, axis, pads[0])
       graphs[-1].Draw('PLSAME')
       legend.AddEntry(graphs[-1], '', 'PL')

axis[0].GetYaxis().SetTitle('95% CL Limit on #sigma #times BR(#phi#rightarrow#tau#tau) #times BR(A#rightarrow#tau#tau)')
axis[0].GetYaxis().SetTitleOffset(1.75)
axis[0].GetYaxis().SetTitleSize(0.04)
axis[0].GetXaxis().SetTitleSize(0.04)
axis[0].GetYaxis().SetLabelSize(0.03)
axis[0].GetXaxis().SetLabelSize(0.03)

#if args.y_title is not None:
#    axis[0].GetYaxis().SetTitle(args.y_title)
axis[0].GetXaxis().SetTitle(args.x_title)
axis[0].GetXaxis().SetLabelOffset(axis[0].GetXaxis().GetLabelOffset()*2)    

if args.logy:
    axis[0].SetMinimum(0.1)  # we'll fix this later
    pads[0].SetLogy(True)
    # axis[0].GetYaxis().SetMoreLogLabels()
    # axis[0].SetNdivisions(50005, "X")

y_min, y_max = (plot.GetPadYMin(pads[0]), plot.GetPadYMax(pads[0]))
plot.FixBothRanges(pads[0], y_min if args.logy else 0, 0.05 if args.logy else 0, y_max, 0.25)

pads[0].cd()
if legend.GetNRows() == 1:
    legend.SetY1(legend.GetY2() - 0.5*(legend.GetY2()-legend.GetY1()))
legend.Draw()

# line = ROOT.TLine()
# line.SetLineColor(ROOT.kBlue)
# line.SetLineWidth(2)
# plot.DrawHorizontalLine(pads[0], line, 1)

box = ROOT.TPave(pads[0].GetLeftMargin(), 0.81, 1-pads[0].GetRightMargin(), 1-pads[0].GetTopMargin(), 1, 'NDC')
box.Draw()

legend.SetTextSize(0.025);
legend.Draw()

plot.DrawCMSLogo(pads[0], 'CMS', args.cms_sub, 11, 0.045, 0.035, 1.2, '', 0.8)
plot.DrawTitle(pads[0], args.title_right, 3)
plot.DrawTitle(pads[0], args.title_left, 1)
plot.DrawTitle(pads[0], args.title_center,2)

#latex = ROOT.TLatex()
#latex.SetNDC()
#latex.SetTextAngle(0)
#latex.SetTextAlign(12)
#latex.SetTextFont(42)
#latex.SetTextSize(0.04)
#
#latex.DrawLatex(.75,.75,'{}'.format(args.channel))

canv.Update()

canv.Print('.pdf')
canv.Print('.png')
