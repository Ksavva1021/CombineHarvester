import os
import pandas as pd
import json
import seaborn as sns
import matplotlib.pyplot as plt

# Define the directory where the JSON files are stored
json_directory = '/vols/cms/ks1021/offline/4tau/Combine/CMSSW_10_2_13/src/CombineHarvester/Combine4tau/outputs/AN/all/cmb/limits/Collect/'

# Define the dataframe where the JSON data will be added
df = pd.DataFrame(columns=['A','phi','exp+1', 'exp+2', 'exp-1', 'exp-2', 'exp0'])

# Loop through each JSON file in the directory
for filename in os.listdir(json_directory):
    if filename.endswith('.json'):
        # Open the JSON file and load the data
        with open(os.path.join(json_directory, filename)) as json_file:
            data = json.load(json_file)
        # Loop through each item in the JSON data and add it to the dataframe
        for item in data.items():
            if "A60" in filename:
               df = df.append(pd.Series([60,item[0],item[1]['exp+1'], item[1]['exp+2'], item[1]['exp-1'], item[1]['exp-2'], item[1]['exp0']], index=df.columns), ignore_index=True)
            elif "A70" in filename:
               df = df.append(pd.Series([70,item[0],item[1]['exp+1'], item[1]['exp+2'], item[1]['exp-1'], item[1]['exp-2'], item[1]['exp0']], index=df.columns), ignore_index=True)
            elif "A80" in filename:
               df = df.append(pd.Series([80,item[0],item[1]['exp+1'], item[1]['exp+2'], item[1]['exp-1'], item[1]['exp-2'], item[1]['exp0']], index=df.columns), ignore_index=True)
            elif "A90" in filename:
               df = df.append(pd.Series([90,item[0],item[1]['exp+1'], item[1]['exp+2'], item[1]['exp-1'], item[1]['exp-2'], item[1]['exp0']], index=df.columns), ignore_index=True)
            elif "A100" in filename:
               df = df.append(pd.Series([100,item[0],item[1]['exp+1'], item[1]['exp+2'], item[1]['exp-1'], item[1]['exp-2'], item[1]['exp0']], index=df.columns), ignore_index=True)
            elif "A125" in filename:
               df = df.append(pd.Series([125,item[0],item[1]['exp+1'], item[1]['exp+2'], item[1]['exp-1'], item[1]['exp-2'], item[1]['exp0']], index=df.columns), ignore_index=True)
            elif "A140" in filename:
               df = df.append(pd.Series([140,item[0],item[1]['exp+1'], item[1]['exp+2'], item[1]['exp-1'], item[1]['exp-2'], item[1]['exp0']], index=df.columns), ignore_index=True)
            elif "A160" in filename:
               df = df.append(pd.Series([160,item[0],item[1]['exp+1'], item[1]['exp+2'], item[1]['exp-1'], item[1]['exp-2'], item[1]['exp0']], index=df.columns), ignore_index=True)
 
df.loc[68,'exp0'] = 0.01

df_sub = df[['A','phi', 'exp0']]
# Print the resulting dataframe
print(df_sub)


# reshape dataframe to matrix form
df_pivot = df.pivot('A', 'phi', 'exp0')
# create heatmap with Seaborn
sns.heatmap(df_pivot, cmap='YlGnBu')
plt.savefig('output.pdf')

