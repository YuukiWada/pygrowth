#!/usr/bin/env python
import astropy.io.fits as fitsio
import matplotlib.pyplot as plt
import numpy as np
import math
import sys

args=sys.argv

if len(args)<2:
    print("Error: invalid number of arguments")
    print("Usage: python ql_spec.py <input file> <adc channel> <binning (option)>")
    exit()

input_file=args[1]
adc_channel=int(args[2])
if len(args)>3:
    rebin=int(args[3])
    if (rebin>2048) or (rebin<1):
        print("The number of binning should be more than 0 and less than 2048")
        rebin=1
    elif math.log2(rebin).is_integer() != True:
        print("The number of binning should be 2 to the power of n")
        rebin=1
else:
    rebin=1

bin_num=int(2048/rebin)

fits_file=fitsio.open(input_file)
#fits_file.info()
event=fits_file[1].data

clock=1.0e8
start_count=event["timeTag"][0]
end_count=event["timeTag"][len(fits_file[1].data)-1]
if start_count>end_count:
    end_count+=2**40
obs_time=float(end_count-start_count)/clock

#print('{:.2f}'.format(obs_time))
#exit()

#print(len(fits_file[1].data))
mask=(event["boardIndexAndChannel"]==adc_channel)
newdata = event[mask]

weights=np.ones(len(newdata["phaMax"]))/(float(rebin)*obs_time)
plt.hist(newdata["phaMax"]-2048.0, range=(-0.5, 2047.5), bins=bin_num, histtype="step", weights=weights)
plt.yscale('log')
plt.xlabel("Channel")
plt.ylabel("Spectrum (counts/ch/s)")

#ax_yticklocs=plt.yaxis.get_ticklocs()
#ax_yticklocs = list(map(lambda x: x * len(range(-3,3))*1.0/binnum, ax_yticklocs))
#plot.yaxis.set_ticklabels(list(map(lambda x: "%0.2f" % x, ax_yticklocs)))

plt.show()
# exit()
