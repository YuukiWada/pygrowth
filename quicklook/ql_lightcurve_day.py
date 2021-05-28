#!/usr/bin/env python
from astropy.table import vstack, Table
from dateutil.relativedelta import relativedelta
import astropy.io.fits as fitsio
import matplotlib.pyplot as plt
import numpy as np
import datetime
import subprocess
import math
import sys
import os

def data_selection(event, adc_channel, upper, lower, start_count, duration, clock):
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
    time_data=duration+((time_data-float(start_count))/(clock*3600.0))
    return time_data

def get_list(input_dir, date):
    command=["find", input_dir, "-name", date+"*.fits.gz"]
    file_retrieve=subprocess.Popen(command, stdout=subprocess.PIPE)
    input_file_names=[]
    for line in file_retrieve.stdout:
        input_file_names.append(str(line, encoding='utf-8', errors='replace').rstrip('\n'))
    input_file_names.sort()
    return input_file_names
        
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

if len(args)<1:
    print("Error: invalid number of arguments")
    print("Usage: python ql_lightcurve_date.py <input directory> <output directory> <start date> <end date> <adc channel> <threshold>")
    exit()

input_dir=args[1]
output_dir=args[2]
date=[args[3], args[4]]
adc_channel=int(args[5])
threshold=int(args[6])
clock=1.0e8

date_start=datetime.datetime.strptime(date[0], "%Y%m%d")
date_end=datetime.datetime.strptime(date[1], "%Y%m%d")
num_days=(date_end-date_start).days+1

# create output directories
bin_width=[1.0, 10.0, 1.0, 10.0]
low_th=[threshold, threshold, 30, 30]
dirs=["./"+output_dir+"/"+"high_1s", "./"+output_dir+"/"+"high_10s", "./"+output_dir+"/"+"all_1s", "./"+output_dir+"/"+"all_10s"]

for directory in dirs:
    if os.path.isdir(directory)==False:
        os.makedirs(directory)

print(input_dir)

for day in range(num_days):
    date_obj=date_start+relativedelta(days=day)
    date_calc=date_obj.strftime("%Y%m%d")
    print(date_calc)
    input_file_names=get_list(input_dir, date_calc)
    if len(input_file_names)!=0:
        for n in range(4):
            duration=0.0
            for i, input_file in enumerate(input_file_names):
                try:
                    fits_file=fitsio.open(input_file)
                    event=fits_file[1].data
                    start_count=event["timeTag"][0]
                    end_count=event["timeTag"][len(event)-1]
                    if start_count>end_count:
                        end_count+=2**40
                    obs_time=float(end_count-start_count)/clock
                    data_time=data_selection(event, adc_channel, 2048, low_th[n], start_count, duration, clock)
                    if i==0:
                        data=data_time
                    else:
                        data=vstack([data, data_time])
                    duration+=obs_time/3600.0
                except:
                    print("The FITS file is corrupted.")
            weights=np.ones(len(data))/bin_width[n]
            output_file=dirs[n]+"/"+date_calc+".png"
            bin_max=25.0
            bin_num=round(bin_max*3600.0/bin_width[n])
            plot_histogram(data["col0"], output_file, bin_max, bin_num, weights)

exit()
