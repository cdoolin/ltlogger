import zmq
from time import sleep, time
import argparse
import random

pars = argparse.ArgumentParser()
pars.add_argument("name")
pars.add_argument("-s", "--server", action="store", default="localhost")
pars.add_argument("--label", "-l", type=str, default="")
pars.add_argument("--units", "-u", type=str, default="")
pars.add_argument("--every", "-e",  type=float, default=2)
args = pars.parse_args()

import ltclient

c = ltclient.LTClient(server=args.server)

c.config(args.name, args.label, args.units)


while True:
    c.put(args.name, random.random())
    sleep(args.every)
