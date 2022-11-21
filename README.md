# Pacific Northwest Curated Seismic Dataset
## A ML-ready curated data set for a wide range of seismic signals from Pacific Northwest.


## Datasets
All datasets are made of two files: waveform and metadata. All follow the structure of [seisbench](https://seisbench.readthedocs.io/en/latest/). See [here](https://seisbench.readthedocs.io/en/latest/pages/data_format.html) to learn more about the  file structure. Download them using the link below. Note you may access the data directly from Google Colab. See `Google Colab` section below.

### ComCat Events (velocity)
- Channel EH?, BH, and HH?
- waveform (waveforms.hdf5 ~59G): https://drive.google.com/file/d/1QjtgxhdccaWFZC9Ac0AMywJYYEXq140V/view?usp=share_link
- metadata (metadata.csv ~42MB): https://drive.google.com/file/d/1pGl5YpkLi_aOJdi0rX6o8QQEIJaCq63l/view?usp=share_link


### ComCat Events (acceleration)
- Channel EN?
- waveform (waveforms.hdf5 ~2G): https://drive.google.com/file/d/1Bsa9bxxVEwLpQ9LuqRrKxT56Ww-yFJGK/view?usp=share_link
- metadata (metadata.csv ~1.4MB): https://drive.google.com/file/d/1Sd4eL_kW7FVpJ2hYdK510hOZXfc9pzqd/view?usp=share_link
  
### Exotic Events
- waveform (waveforms.hdf5 ~35G): https://drive.google.com/file/d/10fnRTU8MqwxCQMef94lCZrtXCuog6SS0/view?usp=share_link
- metadata (metadata.csv ~13.4MB): https://drive.google.com/file/d/1Rf3zt3kzr3x3El1ytIVYbuWs_5GsCGnr/view?usp=share_link

### Inspect Dataset
Here are two ways to look at PNW dataset. 
1. Jupyter Notebook
A jupyter notebook is available to load and plot PNW dataset at [here](./notebooks/inspect_pnw_dataset.ipynb). Download and run it on a local machine to enable the interactive plotting (e.g., zoom in/out).

2. Google Colab
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1z6Ls_cj5cHu0ml_9DK3ExIm3b4EcNsg8?usp=sharing)

If you are more familiar with Google Colab, go to the link above. Note that interactive plotting is not available. Please let me know if you have made interactive plotting works in Google Colab before.

## ML-enhanced PNSN catalog


## Reference
