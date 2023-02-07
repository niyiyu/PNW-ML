# Pacific Northwest Curated Seismic Dataset
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
## A ML-ready curated data set for a wide range of seismic signals from Pacific Northwest.

![map](./figures/README_overview.png)

## Overview
Each dataset has two files: waveform and metadata. All follow the structure of [seisbench](https://seisbench.readthedocs.io/en/latest/). See [here](https://seisbench.readthedocs.io/en/latest/pages/data_format.html) to learn more about the  file structure. Download using the link below. Note that you may access the data directly from Google Colab. See `Google Colab` section below.

### ComCat Events
- EH?, BH?, and HH? channel (velocity)
  - waveform (~63 GB): Coming soon
  - metadata (50.4 MB): [[Google Drive](https://drive.google.com/file/d/1bKDITx8KiDGZUaUoWQSZilpo7GhdWxKv/view?usp=sharing)]

- EN? (accelerometer)
  - waveform (~2.1 GB): Coming soon
  - metadata (1.7 MB): [[Google Drive](https://drive.google.com/file/d/1xpeaoC3NsZqyICIbNHF2J46WsfZwwF6K/view?usp=sharing)]

### Noise Waveform
- EH?, BH, and HH? channel (velocity)
  - waveform (~18 GB): Coming soon
  - metadata (4.9 MB): [[Google Drive](https://drive.google.com/file/d/1Ou5AKRczEqnNRsSEUSafIRlGcXTvLLUW/view?usp=sharing)]
  
### Exotic Events
  - waveform (~3.9 GB): Coming soon
  - metadata (1.4 MB): [[Google Drive](https://drive.google.com/file/d/1brCZkrKjRtToLxBX5ob7qHX6EBq00nAM/view?usp=sharing)]

### Northern California Sequence (Dec 2022)
  - waveform (~347 MB):
  - metadata (126 KB): [[Google Drive](https://drive.google.com/file/d/1BhLVODzlu407JDZ0OteoPgZlTE-o469O/view?usp=sharing)]

### Inspect Dataset
Here are two ways to look at PNW dataset. 
1. Jupyter Notebook
   
A jupyter notebook is available to load and plot PNW dataset at [here](./notebooks/inspect_pnw_dataset.ipynb). Download and run it on a local machine to enable the interactive plotting (e.g., zoom in/out for checking the picks).

1. Google Colab [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1z6Ls_cj5cHu0ml_9DK3ExIm3b4EcNsg8?usp=sharing)

If you are more familiar with Google Colab, go to the link above. Note that interactive plotting is not available.

## Metadata
| Attribute      | Description | Example |
| ----------- | ----------- |-------|
| event_id | Event identifier | uw10564613 |
| source_origin_time | Source origin time in UTC | 2002-10-03T01:56:49.530000Z |
| source_latitude_deg | - | 48.553 |
| source_longitude_deg | - | -122.52 |
| source_type | - | earthquake |
| source_type_pnsn_label | PNSN AQMS event type | eq |
| source_depth_km | - | 14.907 |
| source_magnitude_preferred | - | 2.1 |
| source_magnitude_type_preferred | - | Md |
| source_magnitude_uncertainty_preferred | - | 0.03 |
| source_local/duration/hand_magnitude | Ml, Md, and Mh if available | 1.32 |
| source_local/duration_magnitude_uncertainty | magnitude uncertainty if available | 0.15 |
| source_depth_uncertainty_km | - | 1.69 |
| source_horizontal_uncertainty_km | - |0.694 |
| station_network_code | FDSN network code | UW |
| station_code | FDSN station code | GNW |
| station_location_code | FDSN location code | 01 |
| station_latitude_deg | - | 47.5641 |
| station_longitude_deg | - | -122.825 |
| station_elevation_m | - | 220.0 |
| trace_channel | FDSN channel code (first two digits) | BH |
| trace_name | Bucket and array index | bucket1\$0,:3:15001 |
| trace_sampling_rate_hz | All traces resampled to 100 Hz | 100 |
| trace_start_time |  Trace start time in UTC | 2002-10-03T01:55:59.530000Z |
| trace_P/S_arrival_sample | Closest sample index of arrival  | 8097 |
| trace_P/S_arrival_uncertainty_s | Picking uncertainty in second |  0.02 |
| trace_P/S_onset |  |  emergent |
| trace_P_polarity | - |  undecidable |
| trace_snr_db | SNR for each component |  6.135|3.065|11.766 |

## Reference
Yiyu Ni(*), Alexander R. Hutko, Francesca Skene, Marine A. Denolle, Stephen D. Malone, Paul Bodin, J. Renate Hartog, Amy Wright, "Curated Pacific Northwest Seismic Dataset", submitted to Seismica