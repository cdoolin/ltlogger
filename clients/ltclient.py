import zmq
from time import time as now


context = zmq.Context()


class LTClient(object):
    def __init__(self, server="localhost", port=2173):
        self.s = context.socket(zmq.REQ)
        self.s.connect("tcp://%s:%d" % (server, int(port)))

    def config(self, name, label="", units=""):
        self.s.send("config;%s;%s;%s" % (name, label, units))
        self.s.recv()

    def put(self, name, value, time=None):
        if time is None:
            time = now()

        self.s.send("put;%s;%s;%s" % (name, value, time))
        self.s.recv()
