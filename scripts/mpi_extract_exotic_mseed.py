from mpi4py import MPI
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from tqdm import tqdm

import obspy
import pickle
from obspy.geodetics import locations2degrees
from obspy.core.utcdatetime import UTCDateTime
import requests
import glob
import h5py
from collections import Counter
import sys
sys.path.append("/data/wsd01/pnwstore/")
from obspy.signal.cross_correlation import *

from pnwstore.mseed import WaveformClient

client = WaveformClient()


import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

# parallelize with ompi
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()


bucket_mapping = {'su': 11, 'th': 12, 'px': 13, 'ex': 14, 'sn': 15, 'pc': 16}
name_mapping = {'su': 'surface event', 'th': 'thunder', 'px': 'probable explosion',
                'ex': 'explosion', 'sn': 'sonic boom', 'pc': 'plane crash'}
impulsivity_mapping = {'e': 'emergent', 'i': 'impulsive'}

def update_data(data, streamdata, ibucket, length):
    if streamdata.shape[0] < 3:
        for _ in range(3 - len(streamdata)):
            streamdata = np.concatenate((np.zeros([1, length]), streamdata))
    streamdata = np.expand_dims(streamdata, axis = 0)

    if ibucket in data:
        data[ibucket] = np.concatenate((data[ibucket], streamdata), axis = 0)
    else:
        data[ibucket] = streamdata
    return data


with open("../notebooks/df2.bin", 'rb') as f:
    df2 = pickle.load(f)

drop_list = []
for idx, i in tqdm(df2.iterrows()):
    if pd.notnull(i['P arrival']):
        year = i['P arrival'][:4]
    elif pd.notnull(i['S arrival']):
        year = i['S arrival'][:4]
    else:
        print("something is wrong.")
    if int(year) > 2021 or int(year) < 2002:
        drop_list.append(idx)
df2.drop(index = drop_list, axis = 0, inplace = True)
df2.reset_index(inplace = True, drop = True)

meta = pd.DataFrame(columns = [
    "event_id", "event_type",
    "station_network_code", "trace_channel", "station_code",
    "station_location_code", "station_latitude_deg",  "station_longitude_deg",
    "station_elevation_m", "trace_name", "trace_sampling_rate_hz", "trace_start_time",
    "trace_S_arrival_sample", "trace_S_onset",
    "trace_P_arrival_sample", "trace_P_onset",
    "trace_snr_db", "splits"])
data = {}
for idx, i in df2[df2['event_type'] == 'px'].iterrows():
    if idx % size == rank:
        event_id = "pnsn" + i['event_id']
        net = i['network']
        sta = i['station']
        loc = i['location']
        cha = i['channel']
        etype = i['event_type']
        event_type = name_mapping[i['event_type']]
        ibucket = bucket_mapping[etype]

        if pd.notnull(i['S arrival']):
            stime = UTCDateTime(i['S arrival'])
            starttime = stime - 20
        else:
            stime = np.nan

        if pd.notnull(i['P arrival']):
            ptime = UTCDateTime(i['P arrival'])
            starttime = ptime - 10
        else:
            ptime = np.nan

        s = client.get_waveforms(network = net, station = sta, location = loc,
                             channel = cha + "?", year = starttime.year, doy = starttime.julday)
        s.trim(starttime-30, starttime + 120)
        length = 15001

        if len(s) > 0 and len(s.get_gaps()) == 0:
            s.detrend()
            s.resample(100)
            stream_data = np.array(s)
            if str(stream_data.dtype) != 'object':
                if stream_data.shape[1] == 150 * 100 + 1:
                    data = update_data(data, stream_data, ibucket, length)
                elif 0 < (stream_data.shape[1] - length) <= 2:   # tolerate 2 smaple
                    data = update_data(data, stream_data[:, :length], ibucket, length)
                else:
                    continue

                try:
                    p_arrival_sample = (ptime - starttime + 10) * 100
                except:
                    p_arrival_sample = -999999
                try:
                    s_arrival_sample = (stime - starttime + 10) * 100
                except:
                    s_arrival_sample = -999999

                try:
                    p_onset = impulsivity_mapping[i['P impulsivity']]
                except:
                    p_onset = i['P impulsivity']
                try:
                    s_onset = impulsivity_mapping[i['S impulsivity']]
                except:
                    s_onset = i['S impulsivity']

                trace_name = f'bucket%d$%d,:3,:{length}' % (ibucket, len(data[ibucket]) - 1)
                meta = meta.append({
                    "event_id": event_id, "trace_sampling_rate_hz": 100,
                    "trace_start_time": str(starttime-10),
                    "event_type": event_type, "trace_name": trace_name,
                    "station_network_code": net,"station_code": sta,
                    "station_location_code": loc, "trace_channel": cha,
                    "trace_P_arrival_sample":  int(p_arrival_sample), "trace_P_onset": p_onset,
                    "trace_S_arrival_sample":  int(s_arrival_sample), "trace_S_onset": s_onset,
                    }, ignore_index = True)
        print(f"{rank} | {idx}")



meta.to_csv(f"../extract/px_proc{str(rank).zfill(2)}_metadata.csv", sep = ',', index=False)

f = h5py.File(f"../extract/px_proc{str(rank).zfill(2)}_waveforms.hdf5", mode = "w")
f['/data_format/component_order'] ='ENZ'

f['/data/bucket%d' % ibucket] = data[ibucket]
f.close()
