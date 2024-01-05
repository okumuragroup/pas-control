# Okumura Group Photoacoustic Spectroscopy Package

## What is this?
This repository is a set of Python scripts used to control the photoacoustic spectrometer in the Okumura Group at Caltech. Most of this code is wrappers for various C-based drivers and VISA commands, which might be useful to others who use similar instruments.

## Installing
### Prerequisites
Many of the instruments here require the use of vendor-provided DLLs. We cannot redistribute these here. Please first install the vendor-provided software. Notably, the instruments in this repo which require vendor-provided software are:

- HighFinesse WS Ultimate 2
- Maxon motor (https://www.maxongroup.com/maxon/view/content/epos-detailsite)
- Newport Power Meter
  - We found that even newer versions of the power meter control software work for old meters, such as the Newport 1928-C: https://www.newport.com/medias/sys_master/images/images/he1/h70/9130793205790/Computer-Interface-Software-v3.0.4.zip)

You will also likely require some basic drivers for VISA communication, including:
- Some VISA implementation (tested with NI-VISA: https://www.ni.com/en/support/downloads/drivers/download.ni-visa.html)
- Drivers for your GPIB/IEEE 488.2 interface (we're using a NI GPIB-USB-HS: https://www.ni.com/en/support/downloads/drivers/download.ni-488-2.html)

### Cloning
This project uses git submodules to incorporate the *drivepy* project, which means rather than doing a typical `git clone`, you should instead use
`git clone --recurse-submodules`.

### Set up the conda environment
It is assumed that you have a working conda installation. Create a new environment based on the provided `environment.yml` file with the command

`conda env create -f environment.yml`

After that, the code should be ready to use!