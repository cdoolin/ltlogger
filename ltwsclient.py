import websocket # pip install websocket_client
import json
import time
import numpy as np



class LTWebsockClient(object):
    def __init__(self, server, port):
        
        self.ws = websocket.create_connection(f"ws://{server}:{port}/socket")
        self.ws.settimeout(2) # 2 seconds
        
        # on connect, server sends info of all measurements saved on server
        r = self.wait_for("update_measurements")
        self.measurements = r['measurements']
    
    
    def call(self, action, **kwargs):
        kwargs.update(action=action)
        self.ws.send(json.dumps(kwargs))
        
    def recv(self):
        msg = self.ws.recv()
        return json.loads(msg)

    def wait_for(self, action):
        waiting = True
        while waiting:
            msg = self.recv()

            if msg['action'] == action:
                return msg

    @property
    def names(self):
        return list(self.measurements.keys())
        
    def get_last_measurements(self, name, dt):
        """get the recorded measurements with name over the last dt seconds
        
        Args:
            name (str): Name of measurement to get
            dt (float): Get all measurements recorded in last dt seconds
            
        Returns: 
            iterable of shape [N][2], conatining N pairs of (time, value) records
        """
        self.call("get_data", 
            name = name,
            ta = (time.time() - dt) * 1000) # javascript timestamps are in ms :(
        resp = self.wait_for("got_data")
        
        data = np.asarray(resp['data'])
        
        if len(data) > 0:
            # convert to second timestamps
            data = data * np.array([.001, 1])
            
        return data


if __name__ == '__main__':
    server = "onnes.ccis.ualberta.ca"
    port = "3173"
    print(f"connecting to {server}:{port}")

    lt = LTWebsockClient(server, port)
    print("connected")
    print("measurement names {lt.names}")

    last_5min = lt.get_last_measurements(lt.names[0], 5*60)

    print(f"measurements of '{lt.names[0]} from last 5 minutes:")
    print(last_5min)
