The Flir_github python script is a programm allowing the user to stream the video from the Flir Lepton 3.5 and to record a timelapse in a tif file. 
First, it asks which videosource you want to select. If there is a camera integrated to the computer, this camera is 0 and the Lepton 3.5 is the number 1. Then it opens a new window where the video is streamed.

The different libraries are written at the beginning of the script. I used a conda environment and Python 3.8.

IMPORTANT! In order to run the code, the following files must be in the same folder : LeptonUVC.dll, ManagedIR16Filters.dll, TIFFfile.dll

I recommand creating an application using pyinstaller once your configurations optimized.
