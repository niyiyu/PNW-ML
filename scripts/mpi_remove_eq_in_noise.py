from mpi4py import MPI

import sys
sys.path.append("/home/niyiyu/Research/MachineLearning/seisbench/")
import copy
# from geopy.distance import geodesic
from obspy.core.utcdatetime import UTCDateTime as utc
from datetime import datetime
import time
import pickle
import h5py
import obspy
import os
import numpy as np
from tqdm import tqdm
import pandas as pd
# from tqdm import tqdm
import matplotlib.pyplot as plt

# import seaborn as sns
# sns.set(font_scale=1.2)
# sns.set_style("ticks")

import seisbench
import seisbench.models as sbm
import torch

# parallelize with ompi
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

model = sbm.EQTransformer.from_pretrained("pnw")
model.to(torch.device("cuda"));
model.eval()

for year in range(2022, 2023):
    # if year % size == rank:
    if True:
        fcom = h5py.File(f"../data/mpiextract2022/proc{year}_waveforms.hdf5", 'r')
        dfcom = pd.read_csv(f"../data/mpiextract2022/proc{year}_metadata.csv")

        drop = []
        for k in tqdm(range(len(dfcom))):
            tn = dfcom.iloc[k]['trace_name']
            bucket, narray = tn.split('$')
            x, y, z = iter([int(i) for i in narray.split(',:')])
            data = fcom['/data/%s' % bucket][x, :y, :z]

            for istart,iend in [[0, 6000], [3000, 9000], [6000, 12000], [9000, 15000]]:
                predict = model(torch.Tensor(np.expand_dims(data[:, istart:iend], axis = 0)).to(torch.device("cuda")))
                p = sum(predict[1].detach().cpu().data.T > 0.1)[0]
                s = sum(predict[2].detach().cpu().data.T > 0.1)[0]
                if (p != 0) or (s != 0):
        #             print(f"{p}, {s}, ??")
        #             ds.append(data)
                    drop.append(k)
                    break


        dfcom.drop(index = drop, inplace = True)
        dfcom.reset_index(drop = True, inplace = True)
        dfcom.to_csv(f"../data/mpiextract2022/proc{year}_metadata.csv",  sep = ',', index=False)

        fcom.close()