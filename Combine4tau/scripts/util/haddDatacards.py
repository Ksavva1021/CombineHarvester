import os

variable = ['st','mvis_min_sum_dR_1','mt_tot']
channels = ['eett','emtt','ettt','mmtt','mttt','ttt','tttt']

categories = {
              "ttt" : ["inclusive","nobtag","mvis2_0-100","mvis2_100-200","mvis2_200-500","mvis2_0-100_2l2t_sig","mvis2_100-200_2l2t_sig","mvis2_200-500_2l2t_sig"],
              "tttt": ["inclusive","nobtag","mvis2_0-100","mvis2_100-200","mvis2_200-500","mvis2_0-100_2l2t_sig","mvis2_100-200_2l2t_sig","mvis2_200-500_2l2t_sig"],
              "ettt": ["inclusive","nobtag","mvis2_0-100","mvis2_100-200","mvis2_200-500","mvis2_0-100_2l2t_sig","mvis2_100-200_2l2t_sig","mvis2_200-500_2l2t_sig"],
              "mttt": ["inclusive","nobtag","mvis2_0-100","mvis2_100-200","mvis2_200-500","mvis2_0-100_2l2t_sig","mvis2_100-200_2l2t_sig","mvis2_200-500_2l2t_sig"],
              "emtt": ["inclusive","nobtag","mvis2_0-100","mvis2_100-200","mvis2_200-500","mvis2_0-100_2l2t_sig","mvis2_100-200_2l2t_sig","mvis2_200-500_2l2t_sig"],
              "eett": ["inclusive","nobtag","mvis2_0-100","mvis2_100-200","mvis2_200-500","mvis2_0-100_2l2t_sig","mvis2_100-200_2l2t_sig","mvis2_200-500_2l2t_sig","z_control","2l2t_sig","z_control_nobtag","2l2t_sig_nobtag"],
              "mmtt": ["inclusive","nobtag","mvis2_0-100","mvis2_100-200","mvis2_200-500","mvis2_0-100_2l2t_sig","mvis2_100-200_2l2t_sig","mvis2_200-500_2l2t_sig","z_control","2l2t_sig","z_control_nobtag","2l2t_sig_nobtag"],
             }

source_directory = '/vols/cms/ks1021/4tau/CMSSW_10_2_19/src/UserCode/ICHiggsTauTau/Analysis/4tau/2201/'

target_directory = '/vols/cms/ks1021/offline/4tau/Combine/CMSSW_10_2_13/src/CombineHarvester/Combine4tau/shapes/2201/all'

for channel in channels: 
  if not os.path.isdir('%(target_directory)s/%(channel)s' % vars()):
    os.system("mkdir %(target_directory)s/%(channel)s" % vars())
  for var in variable:
    for cat in categories[channel]:
      os.system("cp %(source_directory)s/%(channel)s/%(var)s_signal_%(channel)s_%(cat)s_all.root %(target_directory)s/%(channel)s/"% vars())
    os.system("hadd -T %(target_directory)s/%(channel)s/%(var)s_%(channel)s_multicat_all.root %(target_directory)s/%(channel)s/%(var)s_signal_%(channel)s_*_all.root"% vars())
  os.system("rm -r %(target_directory)s/%(channel)s/*signal*all.root"% vars())

         
         

