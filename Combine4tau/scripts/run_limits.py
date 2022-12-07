import os
grid_A = [60,70,80,90,100,125,140,160] 
channels = ['cmb','emtt','ettt','mmtt','mttt','tttt','eett']
directory = "output_X2HDM_0712"
for chan in channels:
   if chan != "cmb":
      chan += "_inclusive"
   for mA in grid_A:
      os.system("python python/plot_limits.py --folder=%(directory)s --channel=%(chan)s --year=all --MA=%(mA)s"%vars())


