from time import sleep
import argparse

# configure command line arguments
pars = argparse.ArgumentParser()
pars.add_argument("-s", "--server", action="store", default="localhost")
pars.add_argument("--every", "-e",  type=float, default=5)
pars.add_argument("--port", "-p",  type=str, default="COM3")
pars.add_argument("--zmqport", type=int, default=2173)
args = pars.parse_args()

# load ltlogger client
import ltclient
c = ltclient.LTClient(server=args.server, port=args.zmqport)
c.config("sorb_t", "Sorb Temp", "K")
c.config("vti_t", "VTI Temp", "K")
c.config("3hepot_t", "3He Port Temp", "K")


# use serial communication to talk to cryocon
import serial
ser = serial.Serial(args.port, timeout=1)


value0 = None
while True:
    ser.write('input? a b d\r\n')
    strvals = ser.readline().strip().split(';')
    
    c.put("sorb_t", float(strvals[0]))
    c.put("vti_t", float(strvals[1]))
    c.put("3hepot_t", float(strvals[2]))
    print("%s %s %s" % tuple(strvals))

    sleep(args.every)

ser.close()