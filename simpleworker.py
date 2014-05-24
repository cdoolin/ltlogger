import argparse
import zmq
from time import sleep
import random

parser = argparse.ArgumentParser("Send fake data to low temp logger")
parser.add_argument("name", type=str, help="name of instrument")
parser.add_argument("--sleep", "-s", type=float, default=2, help="sleep between datas in seconds") 
parser.add_argument("--server", type=str, default="localhost", help="server location")
args = parser.parse_args()


context = zmq.Context()
sender = context.socket(zmq.PUSH)
sender.connect("tcp://%s:2173" % args.server)

while True:
    sender.send("%s;%f" % (args.name, random.random()))
    sleep(args.sleep)
