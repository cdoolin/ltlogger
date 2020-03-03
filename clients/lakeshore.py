import zmq
from time import sleep, time
import argparse
import random
import visa

pars = argparse.ArgumentParser()
pars.add_argument("-s", "--server", action="store", default="localhost", help="ltlog server location")
pars.add_argument("--every", "-e",  type=float, default=4, help="time between measurements in s (default 2)")
pars.add_argument("--visa", action="store_true", default=False, help="connect to visa and drop to console")
pars.add_argument("--verbose", "-v", action="store_true", default=False, help="be verbose and print data collected")
args = pars.parse_args()


# Set up the connection with the LakeShore
rm = visa.ResourceManager()
LakeShore = rm.get_instrument('GPIB::12::INSTR')

if args.visa:
    import IPython, sys
    ls = LakeShore
    IPython.embed()
    sys.exit(0)

import ltclient

c = ltclient.LTClient(server=args.server)

c.config("lakeshore1", "LSR Still", "Ohm")
c.config("lakeshore2", "LSR ColdPlate Temp.", "Ohm")
c.config("lakeshore3", "LSR Demag Mag.", "Ohm")
c.config("lakeshore4", "LSR Sample Mag.", "Ohm")
c.config("lakeshore5", "LSR Mixing Chamber", "Ohm")

c.config("lakeshoreT1", "LST Still", "K")
c.config("lakeshoreT2", "LST ColdPlate Temp.", "K")
c.config("lakeshoreT3", "LST Demag Mag.", "K")
c.config("lakeshoreT4", "LST Sample Mag.", "K")
c.config("lakeshoreT5", "LST Mixing Chamber", "K")



while True:
    channel, autoscan = LakeShore.ask("scan?").strip().split(',')
    channel = int(channel)
    
    if autoscan == '0':
        print("warning, autoscan is off")
        
    if channel in [1, 2, 3, 4, 5]:
        data = LakeShore.ask("RDGR? %d" % channel).strip()
        dataT = LakeShore.ask("RDGK? %d" % channel).strip()
        c.put("lakeshore%d" % channel, float(data))
        c.put("lakeshoreT%d" % channel, float(dataT))
        if args.verbose:
            print("channel %d: %f Ohm  %f K" % (channel, float(data), float(dataT)))
    else:
        print("wasn't expecting data from channel %d" % channel)
#    for i in range(1, 5):
#        data = LakeShore.ask("RDGR? %d" % i)
#        c.put("lakeshore%d" % i, float(data))
    sleep(args.every)
