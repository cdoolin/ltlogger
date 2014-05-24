from webui import *
import zmq.green as zmq

GO = True

#
#
#




#
# ZMQ Server Stuff
#

# initialize zmq socket in request / reply mode
context = zmq.Context()
sock = context.socket(zmq.REP)
sock.bind("tcp://*:2173")

# functions to handle various commands given to the server
# through zmq.  these functions must send a single message
# back through the socket or zmq will lock

# all arguments received as strings

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
def click(word=""):
    print("did: %s" % (word))

    uis.hello(text="hi")


@every(3)
def saysthings():
    uis.hello(text="3 secs")


# configure webserver on port 2172
serv = server(2172)
# start zmq server loop
logserver()
# start web server loop
serv.serve_forever()
