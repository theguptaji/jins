import numpy as np
import pandas as pd

import csv, os
import glob
from importlib import reload
from pytz import timezone
from datetime import datetime as dt

import meme
reload(meme)




all_avg = pd.DataFrame(columns=['fname','blink_freq','diff','pvt'])




dir = "/Users/aman/Downloads/1"
t = 0

for root, dirs, files in os.walk(dir):
    for name in files:
        if name.endswith(".csv"):
            df = meme.read(os.path.join(root, name))
            all_avg.at[t,'fname']= os.path.join(root, name)            
            if len(df['EOG'].index) > 1:
                total_time = df['EOG'].index[-1]-df['EOG'].index[0]
                res = meme.detect_blink(df, nf=200, cutoff=100, plot=False)
                proposed = res[res["blink"] == 1.0].index
                all_avg.at[t,'blink_freq'] = (len(proposed)*60)/total_time
                diff = []
                for x in range (len(proposed)-1):                    
                    if x==len(proposed)-1:
                        continue
                    else:
                        diff.append(proposed[x+1]-proposed[x])
                all_avg.at[t,'diff']= sum(diff)/len(diff)
                all_avg.at[t,'pvt'] = df["pvt"]                
            else:
                all_avg.at[t,'blink_freq'] = 0
                all_avg.at[t,'diff'] = 0
                all_avg.at[t,'pvt'] = 0
            t+=1              
        else:
            continue

all_avg.to_csv('/Users/aman/Downloads/1/output.csv', sep=',')