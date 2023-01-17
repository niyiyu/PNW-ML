import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
from mpi4py import MPI
import h5py
import os
import pandas as pd
import obspy
import numpy as np
from obspy import UTCDateTime
import sys
sys.path.append("/home/niyiyu/Research/pnwstore/")

# parallelize with ompi
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

quakeml_path = '/home/niyiyu/Research/PNW-ML/data/norcal_qml'                  # directory contains quakeml file
trace_sampling_rate_hz = 100                                             # resample to 100 hz                                   
window_length = 250                                                      # window length in seconds
nbucket = 1

def update_data(data, streamdata, ibucket):
    if streamdata.shape[0] < 3:
        for _ in range(3 - len(streamdata)):
            streamdata = np.concatenate((np.zeros([1, 25001]), streamdata))
    streamdata = np.expand_dims(streamdata, axis = 0)
    
    if ibucket in data:
        data[ibucket] = np.concatenate((data[ibucket], streamdata), axis = 0)
    else:
        data[ibucket] = streamdata
    return data

data = {}
meta = pd.DataFrame(columns = [
    "event_id", "source_origin_time", "source_latitude_deg", "source_longitude_deg", "source_type",
    "source_depth_km", "source_magnitude", "source_magnitude_type", 
    "source_depth_uncertainty_km", "source_horizontal_uncertainty_km",
    "station_network_code", "trace_channel", "station_code", 
    "station_location_code", "station_latitude_deg",  "station_longitude_deg",  # new features calcuated after extraction
    "station_elevation_m", "trace_name", "trace_sampling_rate_hz", "trace_start_time", 
    "trace_P_arrival_sample", 
    "trace_P_arrival_uncertainty_s", 
    "trace_P_polarity", "trace_P_onset",   # new features to be added
    ])    # for dev only

for ievent, quakeml  in (enumerate(os.listdir(quakeml_path))):
    # logging
    # os.system("echo '%d / %d'>> ./log/%d.log" % (ievent, len(os.listdir(quakeml_path)), rank))
    
    # read quakeml and get event meta
    event = obspy.read_events(quakeml_path + '/%s' % (quakeml))
    # source_id = str(event[0].preferred_origin_id).split('/')[3]
    event_id = quakeml[:-4]
    print(f"----{ievent + 1}-----{event_id}---------")
    source_origin_time = event[0].preferred_origin().time
    source_latitude_deg = event[0].preferred_origin().latitude
    source_longitude_deg = event[0].preferred_origin().longitude
    source_depth_km = event[0].preferred_origin().depth / 1000
    source_magnitude = event[0].preferred_magnitude().mag
    source_magnitude_type = event[0].preferred_magnitude().magnitude_type

    # use Mh magnitude
    # if event[0].preferred_magnitude().mag_errors['uncertainty']:
        # source_magnitude_uncertainty = event[0].preferred_magnitude().mag_errors['uncertainty']
    # else:
        # source_magnitude_uncertainty = np.nan

    if event[0].preferred_origin().origin_uncertainty:
        source_horizontal_uncertainty = float(event[0].preferred_origin().origin_uncertainty.horizontal_uncertainty)/1000.
    else:
        source_horizontal_uncertainty = np.nan
    if event[0].preferred_origin().depth_errors:
        source_depth_uncertainty = float(event[0].preferred_origin().depth_errors['uncertainty'])/1000.
    else:
        source_depth_uncertainty = np.nan
    source_type = event[0].event_type

    # check picks
    for pick in event[0].picks:
        ptime = pick.time
        ptime_uncertainty = pick.time_errors['uncertainty']
        station_network_code = pick.waveform_id.network_code
        station_location_code = pick.waveform_id.location_code
        station_code = pick.waveform_id.station_code
        trace_channel = pick.waveform_id.channel_code
        polarity = pick.polarity
        onset = pick.onset
        
        if trace_channel[:2] in ['BH', "HH", "EH"]: # limit the instrument type
            station_latitude_deg = "TBA"
            station_longitude_deg = "TBA"
            station_elevation_m = "TBA"
            phase = pick.phase_hint
            trace_start_time = source_origin_time - 50
            arrival_sample = (ptime - trace_start_time) * trace_sampling_rate_hz
            pdoy = ptime.julday
            pyear = ptime.year
            
            # try:
            # CODE = source_id + station_network_code + station_code + station_location_code
            # if CODE in meta['CODE'].unique():
            stream = obspy.read(f"../data/norcal/{event_id}/{station_network_code}.{station_code}.{trace_channel[:2]}.mseed")
            stream = stream.trim(trace_start_time, trace_start_time + window_length)
            stream.detrend()
            stream.resample(trace_sampling_rate_hz)

            # need to test gap first then merge
            # stream.merge(fill_value = 0)
            if len(stream) > 0 and len(stream.get_gaps()) == 0:
                stream.merge(fill_value = 0)
                ibucket = np.random.choice(list(np.arange(nbucket) + 1))
                stream_data = np.array(stream)
                try:
                    if stream_data.shape[1] == window_length * trace_sampling_rate_hz + 1:
                        data = update_data(data, stream_data, ibucket)
                    elif 0 < (stream_data.shape[1] - window_length * trace_sampling_rate_hz - 1) <= 2:   # tolerate +2 smaple
                        data = update_data(data, stream_data[:, :window_length * trace_sampling_rate_hz+1], ibucket)
                    elif (window_length * trace_sampling_rate_hz + 1 - stream_data.shape[1]) <= 1: # tolerate -2 sample
                        stream_data = np.c_[stream_data, np.zeros([3,1])]
                        data = update_data(data, stream_data, ibucket)
                    else:
                        pass
                except:
                    print(f"../data/norcal/{event_id}/{station_network_code}.{station_code}.{trace_channel[:2]}.mseed")

                trace_name = 'bucket%d$%d,:3,:25001' % (ibucket, len(data[ibucket]) - 1)

            # else:
                meta = meta.append({
                    "event_id": "uw" + event_id, "source_origin_time": source_origin_time, "source_magnitude_type": source_magnitude_type,
                    # "source_magnitude_uncertainty": "%.3f" % source_magnitude_uncertainty, 
                    "source_horizontal_uncertainty_km": "%.3f" % source_horizontal_uncertainty,
                    "source_depth_uncertainty_km": "%.3f" % source_depth_uncertainty, 
                    "source_latitude_deg": "%.3f" % source_latitude_deg, "source_longitude_deg": "%.3f" % source_longitude_deg, 
                    "source_type": source_type,
                    "source_depth_km": "%.3f" % source_depth_km, "source_magnitude": source_magnitude,
                    "station_network_code": station_network_code, "trace_channel": trace_channel[:2], 
                    "station_code": station_code, "station_location_code": station_location_code,
                    "station_latitude_deg": station_latitude_deg,  "station_longitude_deg": station_longitude_deg,
                    "station_elevation_m": station_elevation_m,
                    "trace_name": trace_name, "trace_sampling_rate_hz": trace_sampling_rate_hz,
                    "trace_start_time": str(trace_start_time),
                    "trace_P_arrival_sample": int(arrival_sample), 
                    "trace_P_arrival_uncertainty_s": ptime_uncertainty,
                    "trace_P_onset": onset,
                    "trace_P_polarity": polarity,}, ignore_index = True)
            # except:
                # pass

# save meta and waveform only for this mpi rank
# merging is required after all mpi rank returns
# select those channels only both P and S pick exists
# meta = meta.drop(columns = "CODE")
# meta = meta.drop(columns = "trace_S_polarity") # dont rely on S polarity
meta.to_csv("../data/extract/norcal_metadata.csv", sep = ',', index=False)

f = h5py.File("../data/extract/norcal_waveforms.hdf5", mode = "w")
f['/data_format/component_order'] ='ENZ'
for b in range(nbucket):
    f['/data/bucket%d' % (b + 1)] = data[b + 1]
f.close()