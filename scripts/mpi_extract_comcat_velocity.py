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

from pnwstore.mseed import WaveformClient
waveformclient = WaveformClient()

quakeml_path = '/auto/pnwstore1-wd11/PNWQuakeML/UW/'                  # directory contains quakeml file
stationxml_path = '/auto/pnwstore1-wd11/PNWStationXML/%s/%s.%s.xml'   # directory of station xml file
splits = ['train', 'test', 'dev']    
trace_sampling_rate_hz = 100                                             # resample to 100 hz                                   
window_length = 150                                                      # window length in seconds
nbucket = 10

def update_data(data, streamdata, ibucket):
    if streamdata.shape[0] < 3:
        for _ in range(3 - len(streamdata)):
            streamdata = np.concatenate((streamdata, np.zeros([1, 15001])))
    streamdata = np.expand_dims(streamdata, axis = 0)
    
    if ibucket in data:
        data[ibucket] = np.concatenate((data[ibucket], streamdata), axis = 0)
    else:
        data[ibucket] = streamdata
    return data

eventlimit = None                                                        # for debug only

for quake_year in np.arange(2002, 2022):
    if quake_year % size == rank:
        ide = 0

        data = {}
        meta = pd.DataFrame(columns = [
            "source_id", "source_origin_time", "source_latitude_deg", "source_longitude_deg", "source_type",
            "source_depth_km", "source_magnitude", "source_magnitude_type", "source_magnitude_uncertainty", 
            "source_depth_uncertainty_km", "source_horizontal_uncertainty_km",
            "station_network_code", "trace_channel", "station_code", 
            "station_location_code", "station_latitude_deg",  "station_longitude_deg",  # new features calcuated after extraction
            "station_elevation_m", "trace_name", "trace_sampling_rate_hz", "trace_start_time", 
            "trace_S_arrival_sample", "trace_P_arrival_sample", 
            "trace_S_arrival_uncertainty_s", "trace_P_arrival_uncertainty_s", 
            "trace_S_polarity", "trace_P_polarity", "trace_S_onset", "trace_P_onset",   # new features to be added
            "trace_snr_db", "split",                                                          # new features calcuated after extraction
            "CODE"])    # for dev only

        for ievent, quakeml  in (enumerate(os.listdir(quakeml_path + str(quake_year)))):
            # logging
            os.system("echo '%d\t| %d / %d'>> ./log/%d.log" % (quake_year, ievent, len(os.listdir(quakeml_path + str(quake_year))), rank)) 
            ide += 1
            
            # read quakeml and get event meta
            event = obspy.read_events(quakeml_path + '%s/%s' % (quake_year, quakeml))
            source_id = str(event[0].preferred_origin_id).split('/')[3]
            source_origin_time = event[0].origins[0].time
            source_latitude_deg = event[0].origins[0].latitude
            source_longitude_deg = event[0].origins[0].longitude
            source_depth_km = event[0].origins[0].depth / 1000
            source_magnitude = event[0].magnitudes[0].mag
            source_magnitude_type = event[0].magnitudes[0].magnitude_type
            if event[0].magnitudes[0].mag_errors['uncertainty']:
                source_magnitude_uncertainty = event[0].magnitudes[0].mag_errors['uncertainty']
            else:
                source_magnitude_uncertainty = np.nan
            source_horizontal_uncertainty = float(event[0].origins[0].origin_uncertainty.horizontal_uncertainty)/1000.
            source_depth_uncertainty = float(event[0].origins[0].depth_errors['uncertainty'])/1000.
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

                    try:
                        CODE = source_id + station_network_code + station_code + station_location_code
                        if CODE in meta['CODE'].unique():
                            stream = waveformclient.get_waveforms(network = station_network_code,
                                                                station = station_code,
                                                                location= station_location_code,
                                                                channel = trace_channel[:2] + '?',
                                                                year    = pyear, doy = pdoy,
                                                                starttime = trace_start_time, endtime = trace_start_time + window_length)
                            #stream = stream.trim(trace_start_time, trace_start_time + window_length)
                            stream.detrend()
                            stream.resample(trace_sampling_rate_hz)

                            # need to test gap first then merge
                            # stream.merge(fill_value = 0) 
                            if len(stream) > 0 and len(stream.get_gaps()) == 0:
                                stream.merge(fill_value = 0)
                                ibucket = np.random.choice(list(np.arange(nbucket) + 1))
                                stream_data = np.array(stream)
                                split = splits[np.random.choice([0, 1, 2], p = [0.6, 0.2, 0.2])]
                                if stream_data.shape[1] == window_length * trace_sampling_rate_hz + 1:
                                    data = update_data(data, stream_data, ibucket)
                                elif 0 < (stream_data.shape[1] - window_length * trace_sampling_rate_hz - 1) <= 2:   # tolerate 2 smaple
                                    data = update_data(data, stream_data[:, :window_length * trace_sampling_rate_hz+1], ibucket)
                                else:
                                    break

                                trace_name = 'bucket%d$%d,:3,:15001' % (ibucket, len(data[ibucket]) - 1)
                                idx = meta.index[meta['CODE'] == CODE].tolist()[0]
                                meta.iloc[idx, meta.columns.get_loc("trace_%s_arrival_sample" % phase)] = int(arrival_sample)
                                meta.iloc[idx, meta.columns.get_loc("trace_%s_arrival_uncertainty_s" % phase)] = ptime_uncertainty
                                meta.iloc[idx, meta.columns.get_loc("trace_name")] = trace_name
                                meta.iloc[idx, meta.columns.get_loc("trace_sampling_rate_hz")] = trace_sampling_rate_hz
                                meta.iloc[idx, meta.columns.get_loc("trace_%s_onset" % phase)] = onset
                                meta.iloc[idx, meta.columns.get_loc("trace_%s_polarity" % phase)] = polarity
                                meta.iloc[idx, meta.columns.get_loc("trace_start_time")] = str(trace_start_time)
                                meta.iloc[idx, meta.columns.get_loc("split")] = split
                        else:
                            meta = meta.append({
                                "source_id": source_id, "source_origin_time": source_origin_time, "source_magnitude_type": source_magnitude_type,
                                "source_magnitude_uncertainty": "%.3f" % source_magnitude_uncertainty, 
                                "source_horizontal_uncertainty_km": "%.3f" % source_horizontal_uncertainty,
                                "source_depth_uncertainty_km": "%.3f" % source_depth_uncertainty, 
                                "source_latitude_deg": "%.3f" % source_latitude_deg, "source_longitude_deg": "%.3f" % source_longitude_deg, 
                                "source_type": source_type,
                                "source_depth_km": "%.3f" % source_depth_km, "source_magnitude": source_magnitude,
                                "station_network_code": station_network_code, "trace_channel": trace_channel[:2], 
                                "station_code": station_code, "station_location_code": station_location_code,
                                "station_latitude_deg": station_latitude_deg,  "station_longitude_deg": station_longitude_deg,
                                "station_elevation_m": station_elevation_m,
                                "trace_%s_arrival_sample" % phase: int(arrival_sample), 
                                "trace_%s_arrival_uncertainty_s" % phase: ptime_uncertainty,
                                "trace_%s_onset" % phase: onset,
                                "trace_%s_polarity" % phase: polarity,
                                "CODE": CODE}, ignore_index = True)
                    except:
                        pass

            if ide == eventlimit:
                break
        
        # save meta and waveform only for this mpi rank
        # merging is required after all mpi rank returns
        # select those channels only both P and S pick exists
        select = (pd.notnull(meta['trace_S_arrival_sample'])) & (pd.notnull(meta['trace_P_arrival_sample']))
        meta_PS = meta[select]
        meta_PS = meta_PS.drop(columns = "CODE")
        meta_PS = meta_PS.drop(columns = "trace_S_polarity") # dont rely on S polarity
        meta_PS.to_csv("../data/mpiextract/proc%s_metadata.csv" % str(quake_year), sep = ',', index=False)
        
        f = h5py.File("../data/mpiextract/proc%s_waveforms.hdf5" % str(quake_year), mode = "w")
        f['/data_format/component_order'] ='ZNE'
        for b in range(nbucket):
            f['/data/bucket%d' % (b + 1)] = data[b + 1]
        f.close()
