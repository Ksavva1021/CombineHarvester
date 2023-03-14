import os

variable = ['mt_tot']
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

source_directory = '/vols/cms/ks1021/offline/4tau_/CMSSW_10_2_19/src/UserCode/ICHiggsTauTau/Analysis/4tau/4tau_plots'

target_directory = '/vols/cms/ks1021/offline/4tau_/Combine/CMSSW_10_2_13/src/CombineHarvester/Combine4tau/shapes/14_03_2023/all'

for channel in channels: 
  if not os.path.isdir('%(target_directory)s/%(channel)s' % vars()):
    os.system("mkdir %(target_directory)s/%(channel)s" % vars())
  for var in variable:
    for cat in categories[channel]:
      os.system("cp %(source_directory)s/%(channel)s/%(var)s_signal_%(channel)s_%(cat)s_all.root %(target_directory)s/%(channel)s/"% vars())
    os.system("hadd -T %(target_directory)s/%(channel)s/%(var)s_%(channel)s_multicat_all.root %(target_directory)s/%(channel)s/%(var)s_signal_%(channel)s_*_all.root"% vars())
  os.system("rm -r %(target_directory)s/%(channel)s/*signal*all.root"% vars())

         
