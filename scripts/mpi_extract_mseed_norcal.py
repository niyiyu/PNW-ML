import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
from mpi4py import MPI
import h5py
import os
import pandas as pd
import obspy
import numpy as np
from obspy import UTCDateTime as utc

from obspy.clients.fdsn.client import Client
from obspy.clients.fdsn.header import URL_MAPPINGS
URL_MAPPINGS['NCEDC'] = "https://service.ncedc.org"

# parallelize with ompi
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

iris = Client("IRIS")
ncedc = Client("NCEDC")

quakeml_path = '/home/niyiyu/Research/PNW-ML/data/norcal_qml'                        # directory contains quakeml file
trace_sampling_rate_hz = 100                                             # resample to 100 hz                                   
window_length = 250                                                      # window length in seconds
nbucket = 1

os.makedirs(f"../data/norcal/", exist_ok=True)

for ievent, quakeml  in (enumerate(os.listdir(quakeml_path))):
    if ievent % size == rank:
        print(quakeml)
        # logging
        # os.system("echo '%d / %d'>> ./log/%d.log" % (ievent, len(os.listdir(quakeml_path)), rank)) 
        
        # read quakeml and get event meta
        event = obspy.read_events(quakeml_path + '/%s' % quakeml)
        # source_id = str(event[0].preferred_origin_id).split('/')[3]
        source_id = quakeml[:-4]
        source_origin_time = event[0].preferred_origin().time
        os.makedirs(f"../data/norcal/{source_id}", exist_ok=True)

        # check picks
        for pick in event[0].picks:
            ptime = pick.time
            ptime_uncertainty = pick.time_errors['uncertainty']
            network = pick.waveform_id.network_code
            location = pick.waveform_id.location_code
            station = pick.waveform_id.station_code
            channel = pick.waveform_id.channel_code
            polarity = pick.polarity
            onset = pick.onset
            if channel[:2] in ['BH', "HH", "EH"]: # limit the instrument type
            # if channel[:2] in ['EN']:
                phase = pick.phase_hint
                trace_start_time = source_origin_time - 50 - 10
                trace_end_time = trace_start_time + window_length + 20

                if not os.path.exists(f"../data/norcal/{source_id}/{network}.{station}.{channel[:2]}.mseed"):
                    if network not in ["BK", "NC"]:
                        s = iris.get_waveforms(network, station, location, channel[:2] + "?", 
                                    starttime = trace_start_time, endtime = trace_end_time)
                    else:
                        s = ncedc.get_waveforms(network, station, location, channel[:2] + "?", 
                                    starttime = trace_start_time, endtime = trace_end_time)
                    try:
                        assert len(s) > 0
                        s.write(f"../data/norcal/{source_id}/{network}.{station}.{channel[:2]}.mseed")
                    except:
                        print(network, station, location, channel[:2] + "?", trace_start_time, trace_end_time)