from time import sleep
import argparse

# configure command line arguments
pars = argparse.ArgumentParser()
pars.add_argument("-s", "--server", action="store", default="localhost")
pars.add_argument("--every", "-e",  type=float, default=10)
pars.add_argument("--port", "-p",  type=str, default="COM4")
args = pars.parse_args()

# load ltlogger client
import ltclient
c = ltclient.LTClient(server=args.server)
c.config("he_lvl", "LHe Level", "%")

# use serial communication to talk to mercury iTC
import serial
s = serial.Serial(args.port, timeout=1)

value0 = None
while True:
    s.write("READ:DEV:DB5.L1:LVL:SIG:HEL:LEV\n")
    m = s.readline()
    try:
        val = m[m.rindex(":") + 1:m.rindex("%")]
        val = float(val)
    except ValueError:
        print("bad response: %s" % m)
        val = value0
        
    if val != value0:
        print("%s %%" % val)
        c.put("he_lvl", float(val))
        value0 = float(val)
    else:
        print("same")
    sleep(args.every)
