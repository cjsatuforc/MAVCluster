#  -*- coding: utf-8 -*-

"""
Modules.connection
~~~~~~~~~~~~~~~

* Manage one single drone state.
* Implement the methods for the communication between monitor and one single drone mainly through UDP protocol.

The message should follow the example below (we will call it "MAVC message" later):
[
    {
        'Header‘: 'MAVCluster_Drone',   # or 'MAVCluster_Monitor'
        'Type': MAVC_REQ_CID            # values defined later
    },
    # If the value of 'Type' begins with 'MAVC_REQ_',then the message should contain the information above only

    # Type = MAVC_CID
    {
        'CID' : 1
    }

    # Type = MAVC_STAT
    {
        'CID' : 2,
        'Armed': True,      # Is armed or not
        'Mode': 'Auto',     # Flight mode
        'Lat' : 38.13421,   # Latitude
        'Lon' : -114.31341, # Longitude
        'Alt' : 4           # Altitude(meters)
    }
    # Type = MAVC_GO_TO
    {
        'CID': 3,
        'Lat': 38.11523,
        'Lon': -118.53556,
        'Alt': 5,
        'Time': 3           # Time limit(seconds)
    },...

    # Type = MAVC_GO_BY
    {
        'CID': 3,
        'N': 3,             # Distance in North direction(meters)
        'E': 5,             # Distance in East direction(meters)
        'Alt': 5,           # Altitude(meters)
        'Time': 3           # Time limit(seconds)
    },...
]
"""

import socket
import json

# Constant value definition of communication type
MAVC_REQ_CID = 0     # Request the Connection ID
MAVC_CID = 1         # Response to the ask of Connection ID
MAVC_REQ_STAT = 2    # Ask for the state of drone(s)
MAVC_STAT = 3        # Report the state of drone
MAVC_GO_TO = 4       # Ask drone to fly to next target specified by latitude and longitude
MAVC_GO_BY = 5       # Ask drone to fly to next target specified by the distance in both North and East directions


class Drone:
    """
        * Manage state of one single drone.
        * "Maintain" the connection between monitor and one single drone(actually the Raspberry Pi 3)
    """
    def __init__(self):
        # Initialize private attributes
        self.__task_done = False    # Whether the task has been done
        self.__host = ''            # Host name of the Pi connected
        self.__state = {            # Information of state the drone connected
            'CID': -1,
            'Armed': False,
            'Mode': '',
            'Lat': 361,
            'Lon': 361,
            'Alt': 0
        }
        #
        self.__establish_connection()

    def __establish_connection(self):
        # Wait for the request of CID
        while True:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            data_json, addr = s.recvfrom(1024)
            data_dict = json.loads(data_json)
            try:
                if data_dict[0]['Header'] == 'MAVCluster_Drone' and data_dict[0]['Type'] == MAVC_REQ_CID:
                    self.__host = addr['ipaddr']
                    break
            except KeyError:
                continue

    def __update_state(self, state_dict):
        """Deep copy of drone state.

        Args:
            state_dict: Dictionary of drone's state that monitor received from Raspberry Pi 3
        """

        for (key, value) in state_dict.items():
            self.__state[key] = value

    def get_pi_host(self):
        """Return the hostname of Pi connected"""

        return self.__host

    def listen_to_pi(self):
        """Keep listening the message sent frome the Pi"""

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        while not self.__task_done:
            state_json, addr = s.recvfrom()
            state_dict = json.loads(state_json)
            if not addr['ipaddr'] == self.__host:  # The message is not sent from the Pi
                continue
            try:
                if state_dict[0]['Header'] == 'MAVCluster_Monitor' and state_dict[0]['Type'] == MAVC_STAT:
                    self.__update_state(state_dict[1])
                    continue
            except KeyError:  # This message is not a MAVC message
                continue