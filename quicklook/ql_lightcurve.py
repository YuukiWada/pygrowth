#!/usr/bin/env python
import astropy.io.fits as fitsio
from astropy.table import vstack
import matplotlib.pyplot as plt
import numpy as np
import math
import sys

def data_selection(event, adc_channel, upper, lower, start_count, clock):
    ch_mask=(event["boardIndexAndChannel"]==adc_channel)
    ch_data=event[ch_mask]
    upper_mask=(ch_data["phaMax"]<=upper+2048)
    upper_data=ch_data[upper_mask]
    lower_mask=(upper_data["phaMax"]>=lower+2048)
    lower_data=upper_data[lower_mask]
    normal_mask=(lower_data["timeTag"]>=start_count)
    normal_data=lower_data[normal_mask]
    return_mask=(lower_data["timeTag"]<start_count)
    return_data=lower_data[return_mask]
    return_data["timeTag"]+=2**40
    merged_data=vstack([normal_data["timeTag"], return_data["timeTag"]])
    time_data=merged_data["col0"].astype(float)
    time_data=(time_data-float(start_count))/clock
    return time_data

# reading argiment parameters
args=sys.argv

if len(args)<5:
    print("Error: invalid number of arguments")
    print("Usage: python ql_spec.py <input file> <adc channel> <bin width (sec)> <lower threshold> <upper threshold>")
    exit()

input_file=args[1]
adc_channel=int(args[2])
bin_width=float(args[3])
lower=int(args[4])
upper=int(args[5])
clock=1.0e8

# open fits file
fits_file=fitsio.open(input_file)
event=fits_file[1].data

start_count=event["timeTag"][0]
end_count=event["timeTag"][len(event)-1]
if start_count>end_count:
    end_count+=2**40
obs_time=float(end_count-start_count)/clock
bin_num=math.floor(obs_time/bin_width)+1
bin_max=float(bin_num)*bin_width

time_data=data_selection(event, adc_channel, upper, lower, start_count, clock)
weights=np.ones(len(time_data))/bin_width

# plot data
plt.hist(time_data, range=(0.0, bin_max), bins=bin_num, histtype="step", weights=weights, color="black")
plt.xlabel("time (sec)")
plt.ylabel("count rate (counts/s)")
plt.xlim(0.0, bin_max)
plt.show()
