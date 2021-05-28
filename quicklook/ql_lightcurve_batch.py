#!/usr/bin/env python
import astropy.io.fits as fitsio
from astropy.table import vstack
import matplotlib.pyplot as plt
import numpy as np
import math
import sys
import os

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

def get_list(input_file):
    list_obj=open(input_file)
    list_data=list_obj.read()
    list_obj.close()
    list_lines=list_data.split("\n")
    return list_lines

def plot_histogram(data, output_file, bin_max, bin_num, weights):
    fig=plt.figure()
    plt.hist(data, range=(0.0, bin_max), bins=bin_num, histtype="step", weights=weights, color="black")
    plt.xlabel("time (sec)")
    plt.ylabel("count rate (counts/s)")
    plt.xlim(0.0, bin_max)
    fig.savefig(output_file)
    plt.close(fig)

# reading argiment parameters
args=sys.argv

if len(args)<4:
    print("Error: invalid number of arguments")
    print("Usage: python ql_spec.py <file list> <output directory> <adc channel> <threshold>")
    exit()

file_list=args[1]
output_dir=args[2]
adc_channel=int(args[3])
threshold=int(args[4])
clock=1.0e8
input_list=get_list(file_list)

# create output directories
bin_width=[1.0, 10.0, 1.0, 10.0]
low_th=[threshold, threshold, 30, 30]
dirs=["./"+output_dir+"/"+"high_1s", "./"+output_dir+"/"+"high_10s", "./"+output_dir+"/"+"all_1s", "./"+output_dir+"/"+"all_10s"]
for directory in dirs:
    if os.path.isdir(directory)==False:
        os.makedirs(directory)
        
# reading file files
for input_file in input_list:
    if os.path.isfile(input_file)==True:
        file_name=os.path.basename(input_file).split('.', 1)[0]
        fits_file=fitsio.open(input_file)
        event=fits_file[1].data
        start_count=event["timeTag"][0]
        end_count=event["timeTag"][len(event)-1]
        if start_count>end_count:
            end_count+=2**40
        obs_time=float(end_count-start_count)/clock

        for n in range(4):
            data=data_selection(event, adc_channel, 2048, low_th[n], start_count, clock)
            weights=np.ones(len(data))/bin_width[n]
            output_file=dirs[n]+"/"+file_name+".png"
            bin_num=math.floor(obs_time/bin_width[n])+1
            bin_max=float(bin_num)*bin_width[n]
            plot_histogram(data, output_file, bin_max, bin_num, weights)

exit()
