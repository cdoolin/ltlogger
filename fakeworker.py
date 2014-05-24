import zmq
from time import sleep

context = zmq.Context()

sender = context.socket(zmq.PUSH)
sender.connect("tcp://localhost:2173")

while True:
    sender.send("thing1")
    sleep(2)
