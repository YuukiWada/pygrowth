#!/usr/bin/env python
import astropy.io.fits as fitsio
from astropy.table import vstack
import numpy as np
import math
import sys
import os

def data_selection(event, adc_channel, threshold, start):
    ch_mask=(event["boardIndexAndChannel"]==adc_channel)
    ch_data=event[ch_mask]
    lower_mask=(ch_data["energy"]>=threshold*1000.0)
    lower_data=ch_data[lower_mask]
    time_data=lower_data["unixTime"]-start
    return time_data

def get_list(input_file):
    list_obj=open(input_file)
    list_data=list_obj.read()
    list_obj.close()
    list_lines=list_data.split("\n")
    return list_lines

def histogram(data, bin_max, bin_num):
    hist=np.histogram(data, bins=bin_num, range=(0.0, bin_max))
    return hist[0]


# reading argiment parameters
args=sys.argv

if len(args)<4:
    print("Error: invalid number of arguments")
    print("Usage: python calc_significance <file list> <output directory> <adc channel> <bin width (sec)> <threshold (sigma)>")
    exit()

file_list=args[1]
output_file=args[2]
adc_channel=int(args[3])
bin_width=int(args[4])
scan_threshold=float(args[5])
energy_threshold=3.0 # MeV
input_list=get_list(file_list)

# create output directories
#if os.path.isdir(output_dir)==False:
#    os.makedirs(output_dir)
        
# reading file files
with open(output_file, mode="w") as output:
    with open("./error_message.log", mode="a") as e_output:
        for input_file in input_list:
            if os.path.isfile(input_file)==True:
                try:
                    file_name=os.path.basename(input_file).split('.', 1)[0]
                    fits_file=fitsio.open(input_file)
                    event=fits_file[1].data
                    start_time=event["unixTime"][0]
                    end_time=event["unixTime"][len(event)-1]
                    obs_time=end_time-start_time
                    
                    data=data_selection(event, adc_channel, energy_threshold, start_time)
                    bin_num=math.floor(obs_time/bin_width)+1
                    bin_max=float(bin_num)*bin_width
                    hist=histogram(data, bin_max, bin_num)
                    
                    std=np.std(hist)
                    ave=np.mean(hist)
                    significance=(hist-ave)/std
                    #if np.any(significance >= scan_threshold):
                    #    value_max=np.amax(significance)
                    #    output_string=file_name+", "+str(value_max)
                    #    print(output_string)
                    
                    if np.amax(significance)>3.0:
                        th_select=ave+3.0*std
                        hist_select=hist[~(hist>th_select)]
                        std_sel=np.std(hist_select)
                        ave_sel=np.mean(hist_select)
                        sig_sel=(hist-ave_sel)/std_sel
                        if np.any(sig_sel >= scan_threshold):
                            value_max_sel=np.amax(sig_sel)
                            output_string_sel=file_name+", "+str(value_max_sel)+"\n"
                            output.write(output_string_sel)
                except:
                    error_string="Error: "+input_file
                    print(error_string)
                    e_output.write(error_string)
exit()
