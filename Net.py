"""
Net.py - a simple implementation of a Network class in Micropython
Adapted by Arijit Sengupta from Adafruit/StackOverflow

This is not thoroughly tested - use at your own risk
"""

import time
import network
import urequests as requests
import ubinascii
from Log import *

class Net:
    
    def __init__(self, ssid, password):
        """
        Initialize wifi access point with an ssid and password
        Note that empty passwords are accepted so you can connect to secure
        networks with an empty password ""
        For unsecured networks, use None for password
        """
        
        self._ssid = ssid
        self._password = password
        self._wlan = None
        self._blink = False
        self._wlan = network.WLAN(network.STA_IF)
        
    def connect(self, max_wait=10):
        """
        Connect to the wifi network with a maximum wait time
        """
        self._wlan.active(True)
        if self._password != None:
            self._wlan.connect(self._ssid, self._password)
        else:
            self._wlan.connect(self._ssid, security=0)

        # Wait for connection to establish
        Log.i(f'Net: connecting to {self._ssid}')
        print('waiting for connection...', end="")
        while max_wait > 0:
            if self._wlan.status() < 0 or self._wlan.status() >= 3:
                    break
            max_wait -= 1
            print('.', end="")
            time.sleep(1)
            
        # Manage connection errors
        if self._wlan.status() != 3:
            raise RuntimeError('Network Connection has failed!')
        else:
            print("Connected!")
            Log.i('Net: connected!')
    
    def disconnect(self):
        """ Disconnect from wifi network """
        self._wlan.disconnect()
        self._wlan.active(False)
        
    
    def getLocalIp(self):
        """ Get the local IP address as a string """

        if self._wlan.active():
            info = self._wlan.ifconfig()
            return info[0]
        else:
            return 'Not connected'
        
    def getMac(self):
        mac = ubinascii.hexlify(self._wlan.config('mac'),':').decode()
        return mac
        
    def updateTime(self, timezone = 'America/New_York'):
        """ Update local time using an the world timeapi """
        
        apiendpoint = 'https://worldtimeapi.org/api/timezone/' + timezone
        json = self.getJson(apiendpoint)
        if json:
            unixtime = json['unixtime']
            raw_offset = json['raw_offset']
            dst_offset = json['dst_offset']
            unixtime = unixtime + raw_offset + dst_offset
            import machine
            tm = time.gmtime(unixtime)
            machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))
        return time.localtime()

    def getFormattedTime(self, extra='day'):
        """
        Get the local time as a String that fits a 16 char line
        If shorter strings are desired, just use time.localtime and format as needed

        extra can be one of 'day' (shows weekday)
                            'year' shows the year
                            'sec' shows seconds
        Unfortunately only one extra can be chosen
        """
        wk = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        mon = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
        (yy, mm, dd, h, m, s, w, y) = time.localtime()
        self._blink = not self._blink
        col = ':' if self._blink else ' '
        if extra == 'sec':
            return f'{mon[mm-1]}-{dd:02} {h:02}:{m:02}:{s:02}'
        elif extra == 'day':
            return f'{wk[w]} {mon[mm-1]} {dd:02} {h:02}{col}{m:02}'
        else:
            return f'{mm:02}/{dd:02}/{yy:04} {h:02}{col}{m:02}'

    def getJson(self, url):
        """
        Get the JSON data from a REST API. Only valid JSON supported.
        Only GET for now. No POST or PUT. Returns the parsed json structure
        """
        
        try:
            if self._wlan == None:
                self.connect()
            data=requests.get(url)
            jsondata = data.json()
            data.close()
            return jsondata
        except:
            Log.e("could not connect (status =" + str(self._wlan.status()) + ")")
            return None

