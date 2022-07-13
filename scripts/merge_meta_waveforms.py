import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
import h5py
import numpy as np
import pandas as pd
from tqdm import tqdm

s = 0
data = {}
lenth = {}
nbucket = 10
for ibucket in range(nbucket):
    lenth[ibucket + 1] = 0

df_all = pd.DataFrame()
for i in tqdm(range(2016, 2022)):
    f = h5py.File("../data/mpiextract/proc%s_waveforms.hdf5" % str(i), mode = "r")
    df = pd.read_csv("../data/mpiextract/proc%s_metadata.csv" % str(i))
        
    for idx in range(len(df)):
        ib = int(df.iloc[idx]['trace_name'].split('bucket')[1].split('$')[0])  
        ntr = int(df.iloc[idx]['trace_name'].split('$')[1].split(',')[0])
        df.iloc[idx, df.columns.get_loc("trace_name")] = 'bucket%s$%d,:3,:15001' % (ib, ntr + lenth[ib])
        
    for ibucket in range(nbucket):    
        if (ibucket+1) in data.keys():
            data[ibucket + 1] = np.concatenate([data[ibucket + 1], f['/data/bucket%d' % (ibucket + 1)][:]], axis = 0)
        else:
            data[ibucket + 1] = f['/data/bucket%d' % (ibucket + 1)][:]
        lenth[ibucket + 1] = data[ibucket + 1].shape[0]

    df_all = df_all.append(df, ignore_index = True)
    
    
    f.close()

# save merged meta file
select = (pd.notnull(df_all['trace_S_arrival_sample'])) & (pd.notnull(df_all['trace_P_arrival_sample']))
meta_PS = df_all[select]
meta_PS.to_csv("../data/metadata.csv", index = False)

# save merged waveform file
f = h5py.File("../data/waveforms.hdf5", mode = "w")
for i in range(nbucket):
    f[f'/data/bucket{i + 1}'] = data[i + 1]
f['/data_format/component_order'] = 'ZNE' 
f.close()