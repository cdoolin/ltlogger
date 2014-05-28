from webui import *
import zmq.green as zmq
import numpy
import numpy.random as random


# turns off zmq server.
# TODO: turn off webserver too.
GO = True

#
#  Measurement Database
#

N = 100
xs = numpy.linspace(0, 6, N)

def rand(a, b):
    # generate uniform random number in [a, b)
    return (float(b) - a) * random.rand(N) + a

names = ["Valve", "Temperature", "Pressure", "Transmission"]
measurements = {
    ("%s_%d" % (names[int(random.rand()*len(names))], random.rand()*20)):
        list(rand(30, 80) + (random.rand() - 0.5) * 800. / 6. * xs)
            for i in range(10) }

print measurements.keys()
#
# ZMQ Server Stuff
#

# initialize zmq socket in request / reply mode
context = zmq.Context()
sock = context.socket(zmq.REP)
sock.bind("tcp://*:2173")

# functions to handle various commands given to the server
# through zmq.  these functions must send a single message
# back through the socket so the zmq server can start 
# receiveing the next message.

# arguments passed to functions as strings so remember to
# convert them to the appropriate type.

def ping(*args):
    sock.send("pong")

def put(name, value, timestamp=""):
    sock.send("put")
    row['type'] = name
    row['value'] = value
    row['localtime'] = timestamp
    row['servertime'] = time.time()
    row.append()
    print("put %s %f" % (name, float(value)))

def get(name):
    # gets last measurement of given type
    measurements.read_where('type == name')
    sock.send("get")
    print("get %s" % name)


# dictionary maps the command string in a zmq message
# to the correct python function.
zmqcommands = {
    "ping": ping,
    "put": put,
    "get": get,
}

@gthread
def logserver():
    """
    main zmq server event loop.  waits for a message and calls
    the appropriate function to act on the message.

    zmq messages are strings expected to be formatted like:

      <command>;<arg1>;<arg2>...

    the command is looked up in zmqcommands dictionary and arguments
    in the message are passed as arguments to the command function.
    """
    while GO:
        msg = sock.recv().split
        if msg[0] in zmqcommands.keys():
            try:
                zmqcommands[msg[0]](sock, *msg[1:])
            except TypeError as e:
                print("error running %s(%s):\n  %s" %
                         (msg[0], ", ".join(msg[1:]), e))
                sock.send("err;command failed")
        else:
            print("received unknown command \"%s\"" % msg[0])
            sock.send("err;unknown command")


#
# WebUI Stuff
#

@action
def get_measurements():
    names = sorted(measurements.keys())
    ui.update_measurements(names=names)

@action
def get_data(name):
    if name in measurements.keys():
        ui.update_data(name=name, data=measurements[name])
    else:
        ui.error(text="no measurement \"%s\"" % name)

@action
def connected():
    get_measurements()


# configure webserver on port 2172
serv = server(2172)
# start zmq server loop
logserver()
# start web server loop
serv.serve_forever()
