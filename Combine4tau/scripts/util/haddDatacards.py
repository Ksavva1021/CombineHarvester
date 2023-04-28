import os
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--input',help= 'Input directory', default='/vols/cms/gu18/4tau_v3/CMSSW_10_2_19/src/UserCode/ICHiggsTauTau/Analysis/4tau/1204/')
parser.add_argument('--output',help= 'Output directory', default='/vols/cms/gu18/4tau_v3/CMSSW_10_2_13/src/CombineHarvester/Combine4tau/shapes/1704/')
args = parser.parse_args()

variable = ['mt_tot']
#variable = ['st','mt_tot']
channels = ['eett','emtt','ettt','mmtt','mttt','ttt','tttt']
categories = {
              "ttt" : ["inclusive"],
              "tttt": ["inclusive"],
              "ettt": ["nobtag"],
              "mttt": ["nobtag"],
              "emtt": ["z_control_nobtag","2l2t_sig_nobtag"],
              "eett": ["z_control_nobtag","2l2t_sig_nobtag"],
              "mmtt": ["z_control_nobtag","2l2t_sig_nobtag"],
             }

source_directory = args.input
target_directory = args.output


if not os.path.isdir('%(target_directory)s' % vars()):
  os.system("mkdir %(target_directory)s" % vars())
for channel in channels: 
  if not os.path.isdir('%(target_directory)s/%(channel)s' % vars()):
    os.system("mkdir %(target_directory)s/%(channel)s" % vars())
  for var in variable:
    for cat in categories[channel]:
      os.system("cp %(source_directory)s/%(channel)s/%(var)s_signal_%(channel)s_%(cat)s_all.root %(target_directory)s/%(channel)s/"% vars())
    os.system("hadd -T %(target_directory)s/%(channel)s/%(var)s_%(channel)s_multicat_all.root %(target_directory)s/%(channel)s/%(var)s_signal_%(channel)s_*_all.root"% vars())
  os.system("rm -r %(target_directory)s/%(channel)s/*signal*all.root"% vars())

         
