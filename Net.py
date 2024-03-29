"""
Net.py - a simple implementation of a Network class in Micropython
Adapted by Arijit Sengupta from Adafruit/StackOverflow

This is not tested - use at your own risk
"""

import time
import network
import urequests as requests

class Net:
    
    def __init__(self, ssid, password):
        self._ssid = ssid
        self._password = password
        self._wlan = None
        
    def connect(self, max_wait=10):
        self._wlan = network.WLAN(network.STA_IF)
        self._wlan.active(True)
        self._wlan.connect(self._ssid, self._password)

        # Wait for connection to establish
        while max_wait > 0:
            if self._wlan.status() < 0 or self._wlan.status() >= 3:
                    break
            max_wait -= 1
            print('waiting for connection...')
            time.sleep(1)
            
        # Manage connection errors
        if self._wlan.status() != 3:
            raise RuntimeError('Network Connection has failed')
        else:
            print('connected')
    
    def disconnect(self):
        self._wlan.disconnect()
        
        
    def getJson(self, url):    
        try:
            if self._wlan == None:
                self.connect()
            data=requests.get(url)
            jsondata = data.json()
            data.close()
            return jsondata
        except:
            print("could not connect (status =" + str(self._wlan.status()) + ")")
            return None