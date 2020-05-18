# Documentation of the SAO format: https://ulcar.uml.edu/~iag/SAO-4.3.htm
Read and plot stacked SAO data

example usage:

Stacked ionograms:
python digisonde24h.py data/TR169_YYYYDDD <output>

Stacked electron density:
python ed-digisonde24h.py data/TR169_YYYYDDD <output>

Stacked electron density logaritmic:
python edlog-digisonde24h.py data/TR169_YYYYDDD <output>

directory = path to the digisonde data
YYYY = year
DDD = the day number of the year
output = filename of the resulting plot (optional argument)
if no output filename is given, the program just plot to screen
comment out last line if you do not want output to screen

The "data" directory contains data for testing purposes. 
