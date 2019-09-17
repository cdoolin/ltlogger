import os
import argparse
import sys
import time
import datetime

parser = argparse.ArgumentParser(description="watches nanospec log files and reports changes to ltlog")
parser.add_argument("path", type=str, help="path to file to watch")
parser.add_argument("--every", "-e", type=float, default=60, help="delay in seconds between checking the file (default 60)")
parser.add_argument("--server", "-s", type=str, default="localhost", help="location of ltlog server")

args = parser.parse_args()

if not os.path.exists(args.path):
    print("%s doesn't exit" % args.path)
    sys.exit(1)

f = open(args.path, 'r')

# go to end of file
f.seek(0, os.SEEK_END)

import ltclient
client = ltclient.LTClient(server=args.server)

client.config("nanospec", "Nanospec Temp.", "mK")

epoch = datetime.datetime(1970, 1, 1)
value0 = 0

while True:
    line = f.readline()

    if len(line) < 1:
        time.sleep(args.every)
        continue
    
    row = line.split()
    value = float(row[-1])
    if value != value0:
        mo, da, ye = row[0].split("/")
        ho, mi = row[1].split(":")
        if splitd[2] == "PM":
            ho = int(ho) + 12
        time1 = datetime.datetime(int(ye), int(mo), int(da), ho, int(mi))
        secs = (time1 - epoch).seconds

        client.put("nanospec", value, time=secs)
        value0 = value

    time.sleep(args.every)

