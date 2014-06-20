import zmq
from time import sleep, time
import argparse
import random

pars = argparse.ArgumentParser()
pars.add_argument("name")
pars.add_argument("-s", "--server", action="store", default="localhost")
args = pars.parse_args()


context = zmq.Context()

sender = context.socket(zmq.REQ)
sender.connect("tcp://%s:2173" % args.server)


while True:
    msg = "%s;%s;%f;%d" % ("put", args.name, random.random(), int(time()))
    print(msg)
    sender.send(msg)
    sender.recv()
    sleep(2)

