import json

A = '160'
inputs = ['/vols/cms/ks1021/offline/4tau/Combine/CMSSW_10_2_13/src/CombineHarvester/Combine4tau/outputs/out_mt_tot/all/tttt_inclusive/limits/A%(A)s/HN16_A%(A)s.json'%vars(),'/vols/cms/ks1021/offline/4tau/Combine/CMSSW_10_2_13/src/CombineHarvester/Combine4tau/outputs/out_mt_tot/all/tttt_inclusive/limits/A%(A)s/HN_A%(A)s.json'%vars(),'/vols/cms/ks1021/offline/4tau/Combine/CMSSW_10_2_13/src/CombineHarvester/Combine4tau/outputs/out_mt_tot/all/tttt_inclusive/limits/A%(A)s/HN84_A%(A)s.json'%vars()]


with open(inputs[0]) as f1:               # open the file
   data1 = json.load(f1)



with open(inputs[1]) as f2:               # open the file
   data2 = json.load(f2)



with open(inputs[2]) as f3:               # open the file
   data3 = json.load(f3)



items1 = sorted(data1.items())
items2 = sorted(data2.items())
items3 = sorted(data3.items())

mp = ["100.0","110.0","125.0","140.0","160.0","180.0","200.0","250.0","300.0"]

dicts = []
for i,j in enumerate(mp):
   temp_dict = {}
   if (items1[i][0] == j and items2[i][0] == j and items2[i][0] == j):
      temp_dict['exp-1'] = items1[i][1]['exp-1']
      temp_dict['exp0'] = items2[i][1]['exp0']
      temp_dict['exp+1'] = items3[i][1]['exp+1']
      dicts.append(temp_dict)

D = dict(zip(mp, dicts))

# Serializing json  
json_object = json.dumps(D, indent = 4) 
#print(json_object)
jsonFile = open("/vols/cms/ks1021/offline/4tau/Combine/CMSSW_10_2_13/src/CombineHarvester/Combine4tau/outputs/out_mt_tot/all/tttt_inclusive/limits/A%(A)s/HN_comb.json"%vars(), "w")
jsonFile.write(json_object)
jsonFile.close()
