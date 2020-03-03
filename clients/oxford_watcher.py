import os
import argparse
import sys
import time
import datetime

parser = argparse.ArgumentParser(description="watches oxford fridge log files and reports changes to ltlog")
parser.add_argument("path", type=str, help="path to file to watch")
parser.add_argument("--every", "-e", type=float, default=1, help="delay in seconds between checking the file (default 1)")
parser.add_argument("--server", "-s" type=str, default="localhost", help="location of ltlog server")

args = parser.parse_args()

if not os.path.exists(args.path):
    print("%s doesn't exit" % args.path)
    sys.exit(1)

f = open(args.path, 'r')

# times in log file are time after the file was created
# creation labview timestamp in first line of logfile
timestr = f.readline()
# read labview timestamp
logstart = int(timestr[timestr.find("-") + 1:])
# convert to unix timestamp in local timezone
logstart = logstart - 2082844800 # - time.altzone 

# go to end of file
f.seek(0, os.SEEK_END)

names = ["G1_press", "G2_press", "G3_press", "P1_press", "P2_press",
    "MC_htr", "Still_htr", "Sorb_htr", "V12A", "V6", "V1K",
    "MC_temp", "1K_temp", "Sorb_temp",]
labels = ["G1 Press.", "G2 Press.", "G3 Press.", "P1 Press.", "P2 Press.", "M/C Heater", "Still Heater", "Sorb Heater",
    "V12A", "V6", "V1K", "M/C Temp", "1K Pot Temp", "Sob Temp"]
units = "mBar,mBar,mBar,mBar,mBar,uW,mW,mW,%,%,%,K,K,K".split(",")

import ltclient
client = ltclient.LTClient(server=args.server)

for name, label, unit in zip(names, labels, units):
    client.config(name, label, unit)

while True:
    line = f.readline()

    if len(line) < 1:
        time.sleep(args.every)
        continue
    
    row = line.split()
    now = logstart + int(row[0])
    #meas = {name: float(val) for name, val in zip(names, row[1:])}
    print time.time() - now
    for name, val in zip(names, row[1:]):
        client.put(name, val, time=now)
    #print(", ".join(line.split()))

