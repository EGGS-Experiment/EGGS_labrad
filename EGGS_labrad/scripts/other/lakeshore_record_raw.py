# general imports
import numpy as np
from itertools import count
from time import time, sleep
from datetime import datetime

# file imports
import os
import csv

# serial imports
from serial import Serial, PARITY_ODD

# user arguments
COM_PORT =              'COM7'
SAVE_FILE_NAME =        'lakeshore_data'
POLL_INTERVAL_S =       5
PRINT_INTERVAL_ITER =   1


'''
PREPARE
'''
# open serial connection to lakeshore device and clear I/O buffers
ser = Serial(COM_PORT, baudrate=57600, bytesize=7, stopbits=1, parity=PARITY_ODD, timeout=5)
ser.reset_input_buffer()
ser.reset_output_buffer()

# save file to %HOME%/Documents
save_dir = os.path.join(os.path.expanduser('~'), 'Documents')
os.chdir(save_dir)
print("Save Location: {}".format(save_dir))
# tmp remove

# get start date to create file name
date = datetime.now()
filename = '{0:s}__{1:02d}_{2:02d}__{3:s}_{4:02d}_{5:02d}.csv'.format(SAVE_FILE_NAME,
                                                                     date.hour, date.minute,
                                                                     str(date.year), date.month, date.day)
print("Filename: {}".format(filename))
# raise Exception('stop here')


'''
START
'''
# start streaming temperature data to a file
with open(filename, 'w', newline='\n') as file_csv:

    # create csv writer object
    writer = csv.writer(file_csv)

    # get start time
    starttime = time()

    # begin infinite polling loop
    for i in count(0):

        try:
            # query lakeshore for temperature data
            ser.write(b'KRDG? 0\r\n')
            temp_data = ser.read_until(b'\n')

            # convert response into a list of floats
            temp_data = [float(val_str) for val_str in temp_data.decode().strip().split(',')]

            # timestamp results and save to csv file
            writer.writerow([time() - starttime] + temp_data)
            file_csv.flush()

            # print data to log at given interval
            if (i % PRINT_INTERVAL_ITER) == 0:
                print('{}: {}'.format(datetime.fromtimestamp(time()), temp_data))

            # sleep until next polling cycle
            sleep(POLL_INTERVAL_S)

        except Exception as e:
            # close file and serial object
            file_csv.close()
            ser.close()

            # print error message
            print("{}: Closed file due to error.".format(datetime.fromtimestamp(time())))
            print(e)
