from webui import *
from webui.server import Caller
import zmq.green as zmq
import numpy
import numpy.random as random
import time
import os

import tables

import argparse
pars = argparse.ArgumentParser(description="""
Provides a server to consolidate measurements to.

Workers talking to instruments can supply and request data.

Provides a web based interface for viewing received data.
""")

pars.add_argument("--load", "-l", action="store", default="", type=str,
    help="load and continue saving data to this .h5 file")
pars.add_argument("--verbose", "-v", action="store_true", default=False,
    help="enable verbose logging.")
args = pars.parse_args()

# configure webui logging
import logging
if args.verbose:
    logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ltlog")

# turns off zmq server.
# TODO: turn off webserver too.
GO = True

#
# Measurement Database
#
# measurements are saved in hdf5 files (using pytables).
# each measurement is stored in it's own table in located at
# "/measurements/<name>", where <name> is the name of the measurement.
#

if len(args.load) > 0 and os.path.isfile(args.load):
    LOGFILE = args.load
else:
    import datetime
    fname = datetime.datetime.now().strftime("%y.%m.%d_%H%M%S") + ".h5"
    LOGFILE = os.path.join("log", fname)
print("storing data to %s" % LOGFILE)
logfile = tables.open_file(LOGFILE, "a")

try:
    logfile.root.measurements
except tables.NoSuchNodeError:
    logfile.create_group("/", "measurements")


# dictionary to look up pytables table for a measurement
measurements = {t.name: t for t in logfile.list_nodes("/measurements")}
# dictionary to look up connected uis wanting data for a measurement
subscriptions = {k: Caller([]) for k in measurements.keys()}

def description(valuecol):
    return {
        'time': tables.Float64Col(pos=0),
        'servertime': tables.Float64Col(pos=1),
        'value': valuecol(pos=2),
    }



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
    """ping"""
    sock.send("pong")


def put(name, value, timestamp=""):
    """
    saves a measurement with the given name and value. If a measurement
    of that name doesn't exist, create it.

    put;<name>;<value>;<timestamp>
    """
    # use config to create table for measurements if it doesn't exist
    if name not in measurements:
        config(name)

    # if first datapoint,  update ui
    timestamp = float(timestamp)
    if measurements[name].nrows < 1:
        uis.update_measurements(measurements={
                name: {'ta': timestamp*1000., 'tb': timestamp*1000.}})

    row = measurements[name].row
    row['time'] = float(timestamp)
    row['servertime'] = int(time.time())
    row['value'] = float(value)

    subscriptions[name].update_data(
        name=name, data=[(row['time']*1000., row['value'])])

    row.append()

    sock.send("put")
    measurements[name].flush()


def get(name):
    """
    not implemented

    get;<name>
    """
    # gets last measurement of given type
    sock.send("get")
    print("get %s" % name)


def config(name, label="", units=""):
    # configures metadata for measurement.
    if name not in measurements:
       measurements[name] = logfile.create_table("/measurements",
           name, description(tables.Float64Col))
       subscriptions[name] = Caller([])

    measurements[name].title = label
    measurements[name].attrs.units = units

    uis.update_measurements(measurements={
        name: {'label': label, 'units': units}
    })
    sock.send("config")
   

# dictionary maps the command string in a zmq message
# to the correct python function.
zmqcommands = {
    "ping": ping,
    "put": put,
    "get": get,
    "config": config,
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
        msg = sock.recv().split(';')
        logger.info("zmq req %s" % str(msg))
        if msg[0] in zmqcommands:
            try:
                zmqcommands[msg[0]](*msg[1:])
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
# currently it's pythons job to convert unix timestamps (in seconds)
# to javascript ones (in ms).
#

@action
def subscribe(name):
    if ui.socks[0] not in subscriptions[name].socks:
        subscriptions[name].socks.append(ui.socks[0])

@action
def unsubscribe(name):
    if ui.socks[0] in subscriptions[name].socks:
        subscriptions[name].socks.remove(ui.socks[0])

@action
def get_measurements():
    uis.update_measurements(measurements={
        name: {
            'ta': table[0]['time'] * 1000.,
            'tb': table[-1]['time'] * 1000.,
        } for name, table in measurements.iteritems()
    })

def downsample(data, n):
    if(len(data) < n):
        return data

    keep_skip = n / float(len(data) - n)
    if keep_skip > 1: # keep more than skip
        skip = round(keep_skip)
        return [d for i, d in enumerate(data) if i % skip != 0]
    else: # skip more than keep
        keep = round(1. / keep_skip)
        return [d for i, d in enumerate(data) if i % keep == 0]

@action
def get_data(name, ta, tb=-1, n=4096):
    """
    request data for a measurement
    """
    c = "(time >= %f)" % float(ta / 1000.)
    if tb >= 0:
        c += " & (time <= %f)" % float(tb / 1000.)

    data = [(r['time'] * 1000., r['value'])
                      for r in measurements[name].where(c)]

    downsampled = False
    if len(data) > n:
        data = downsample(data, n)
        downsampled = True

    ui.got_data(name=name, data=data, downsampled=downsampled)


@action
def get_datas(times):
    """
    request data for multiple measurements at once.

    expect times to be a dictionary with keys of the measurement names,
    pointing to (initial time, end time) pairs.
    """
    datas = {}
    for name, (ta, tb) in times.iteritems():
        c = "(time >= %f)" % float(ta / 1000.)
        if tb >= 0:
            c += " && (time <= %f)" % float(tb / 1000.)
        datas[name] = [(r['time'] * 1000., r['value'])
                          for r in measurements[name].where(c)]
    uis.update_datas(datas=datas)


@action
def connected():
    ui.update_measurements(measurements={
        name: {
            'ta': table[0]['time'] * 1000.,
            'tb': table[-1]['time'] * 1000.,
            'label': table.title,
            'units': table.attrs.units,
        } for name, table in measurements.iteritems()
    })


# configure webserver on port 2172
serv = server(2172)
# start zmq server loop
logserver()
# start web server loop
serv.serve_forever()
