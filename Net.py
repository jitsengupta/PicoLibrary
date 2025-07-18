"""
Net.py - a simple implementation of a Network class in Micropython
Incorporates both Station(STA) and Access Point(AP) modes
Adapted by Arijit Sengupta from Adafruit/StackOverflow

Also includes a single-page WebServer to support basic I/O operations
on the Pico.

This is not thoroughly tested - use at your own risk.
"""

import time
import network
import urequests as requests
import ubinascii
import json
from Log import *

class Net:
    
    def __init__(self):
        """
        Initialize wifi access point with an ssid and password
        Note that empty passwords are accepted so you can connect to secure
        networks with an empty password ""
        For unsecured networks, use None for password
        """
        
        self._sta = None
        self._ap = None
        self._blink = False
        
    def connect(self, ssid, password=None, max_wait=10):
        """
        Connect to the wifi network with a maximum wait time
        """

        self._sta = network.WLAN(network.STA_IF)
        self._sta.active(True)
        if password is not None:
            self._sta.connect(ssid, password)
        else:
            self._sta.connect(ssid, security=0)

        # Wait for connection to establish
        Log.i(f'Net: connecting to {ssid}')
        print('waiting for connection...', end="")
        while max_wait > 0:
            if self._sta.status() < 0 or self._sta.status() >= network.STAT_GOT_IP:
                    break
            max_wait -= 1
            print('.', end="")
            time.sleep(1)
            
        # Manage connection errors
        if self._sta.status() != network.STAT_GOT_IP:
            raise RuntimeError('Network Connection has failed!')
        else:
            print("Connected!")
            Log.i('Net: connected!')
    
    def startAccessPoint(self, ssid, password=None):
        """
        Start an access point with the given ssid and password
        If password is None, then no password is set
        """
        
        self._ap = network.WLAN(network.AP_IF)
        self._ap.active(True)
        if password is not None:
            self._ap.config(essid=ssid, password=password)
        else:
            self._ap.config(essid=ssid, security=0)

        Log.i(f'Net: Access Point started with SSID {ssid}')

    def getAccessPointInfo(self):
        """
        Get the access point information as a dictionary
        Returns None if no access point is started
        """
        
        if self._ap is not None:
            return {
                'ssid': self._ap.config('essid'),
                #'password': self._ap.config('password'),
                'active': self._ap.active(),
                'mac': ubinascii.hexlify(self._ap.config('mac'),':').decode()
            }
        else:
            return None
        
    def getStationInfo(self):
        """
        Get the station information as a dictionary
        Returns None if no station is connected
        """
        if self._sta is not None:
            return {
                'ssid': self._sta.config('essid'),
                #'password': self._sta.config('password'),
                'active': self._sta.active(),
                'mac': ubinascii.hexlify(self._sta.config('mac'),':').decode(),
                'ip': self.getLocalIp()
            }
        else:
            return None
        
    def isConnected(self):
        """
        Check if the station is connected to a wifi network
        Returns True if connected, False otherwise
        """
        
        if self._sta is not None:
            return self._sta.active() and self._sta.status() == network.STAT_GOT_IP
        elif self._ap is not None:
            return self._ap.active()
        else:
            return False
        
    def isAccessPointActive(self):
        """
        Check if the access point is active
        Returns True if active, False otherwise
        """
        
        if self._ap is not None:
            return self._ap.active()
        else:
            return False
        
    def getStatus(self):
        """
        Get the status of the station and access point
        Returns a dictionary with the status of both
        """
        
        return {
            'station': self.getStationInfo(),
            'access_point': self.getAccessPointInfo()
        }
    
    def getStatusString(self):
        """
        Get a string representation of the status of the station and access point
        """
        
        sta_info = self.getStationInfo()
        ap_info = self.getAccessPointInfo()
        
        sta_str = f"Station: {sta_info['ssid']} ({sta_info['ip']})" if sta_info else "Station: Not connected"
        ap_str = f"Access Point: {ap_info['ssid']}" if ap_info else "Access Point: Not started"
        
        return f"{sta_str}\n{ap_str}"

    def disconnect(self):
        """ Disconnect from wifi network """
        if self._sta:
            self._sta.disconnect()
            self._sta.active(False)
            self._sta = None
        self._ap = None
        
    
    def getLocalIp(self):
        """ Get the local IP address as a string """

        if self._sta is not None and self._sta.active():
            info = self._sta.ifconfig()
            return info[0]
        elif self._ap is not None and self._ap.active():
            info = self._ap.ifconfig()
            return info[0]            
        else:
            return 'Not connected'
        
    def getMac(self):
        """ Get the Mac address of the interface being used """
        
        mac = None
        if self._sta:
            mac = ubinascii.hexlify(self._sta.config('mac'),':').decode()
        elif self._ap:
            mac = ubinascii.hexlify(self._ap.config('mac'),':').decode()
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
            if self._sta == None:
                self.connect()
            data=requests.get(url)
            jsondata = data.json()
            data.close()
            return jsondata
        except Exception as e:
            Log.e(f"could not connect {e}")
            return None

    def putJson(self, url, data):
        """
        Use the PUT method to update data into a remote webservice
        The webservice should be configured to accept data in JSON format.
        Passed in data should be a dictionary with all parameters
        that are expected by this webservice.
        
        Returns the status code or None if fail
        """
        
        headers = {
            "Content-Type": "application/json"
        }

        try:
            response = requests.put(url, data=json.dumps(data), headers=headers)
            status = response.status_code
            Log.d(f"Status Code:{status}")
            Log.d(f"Response:{response.text}")
            response.close()
            return status
        except Exception as e:
            Log.e(f"Failed to send request: {e}")
            return None
        
    def postJson(self, url, data):
        """
        Similar to the above, use POST instead of PUT
        Configure web service to accept JSON and create new entries
        """
        
        headers = {
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(url, data=json.dumps(data), headers=headers)
            status = response.status_code
            Log.d(f"Status Code:{status}")
            Log.d(f"Response:{response.text}")
            response.close()
            return status
        except Exception as e:
            Log.e(f"Failed to send request: {e}")
            return None

class WebServer:
    """
    A skeleton webserver class that uses the Net class to run a blocking web server. Once
    started, it runs forever in this implementation, until Ctrl-C is pressed.

    To use this WebServer, you should have some basic understanding of HTML and/or Javascript
    and CSS. Since this server only supports a single webpage, you need to make sure that
    you can handle all functionality in one page. Forms can be used, and GET/POST requests
    to the page can be made either via redirect or Forms.

    To implement a webpage, subclass this class and override the generate_html method.
    The generate_html method should return a string containing the raw HTML with any
    embedded information you want to show. generate_html will receive a dictionary 
    of any parameters that were received via GET or POST.

    A simple example of generate_html is included with this class.
    """
    
    def __init__(self, net):
        """
        Constructor takes an instance of the Network class. Before
        Calling, make sure network has been activated either as a Station
        or an Access Point.
        """
        self._net = net
    
    def serveUI(self, port=80):
        """
        Serve a single-page UI on the given port.
        This is a blocking call and will serve the UI until disconnected.

        Ctrl-C will stop the server.
        """
        
        import socket
        
        if not self._net.isConnected():
            Log.e("Cannot serve UI: Not connected to any network")
            return
        
        addr = socket.getaddrinfo(self._net.getLocalIp(), port)[0][-1]
        s = socket.socket()
        try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except:
            # SO_REUSEADDR might not be available on all MicroPython implementations
            pass
        
        # Try to bind with retry logic
        max_retries = 5
        for attempt in range(max_retries):
            try:
                s.bind(addr)
                break
            except OSError as e:
                if e.errno == 98:  # EADDRINUSE
                    if attempt < max_retries - 1:
                        print(f"Port {port} in use, waiting 2 seconds... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(2)
                        continue
                    else:
                        print(f"Port {port} still in use after {max_retries} attempts")
                        print("Try changing the port number or wait a bit longer")
                        raise
                else:
                    raise
        
        s.listen(1)
        
        print(f"Web server started on port {port}")
        print("Server is running... Press Ctrl+C to stop")
        
        Log.i(f"Serving UI on http://{addr[0]}:{addr[1]}")
        cl = None
        
        try:
            while True:
                try:
                    cl, addr = s.accept()
                    Log.i(f"Client connected from {addr}")
                    request = cl.recv(1024).decode('utf-8')
                    #request = str(request)
                    Log.d(f"Request: {request[:200] + "..." if len(request) > 200 else request}")
                    
                    params = self.parse_request(request)
                    Log.d(f"Params: {params}")
                    
                    # Serve a simple HTML page with the status            
                    html = self.generate_html(params)
                    response = f"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n{html}"
                    
                    cl.send(response.encode('utf-8'))
                    cl.close()
                except KeyboardInterrupt:
                    print("\nKeyboard interrupt received - shutting down server gracefully...")
                    break
                except Exception as e:
                    print(f"Error handling request: {e}")
                    if cl:
                        try:
                            cl.close()
                        except:
                            pass
                        cl = None
                        
        except KeyboardInterrupt:
            print("\nKeyboard interrupt received - shutting down server gracefully...")
        finally:
            # Clean up any remaining connection
            if cl:
                try:
                    cl.close()
                    print("Active connection closed")
                except:
                    pass
            
            # Close the server socket
                try:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, b'\x00' * 8)  # Immediate close
                except:
                    pass
                try:
                    s.close()
                    print("Server socket closed")
                except:
                    pass
                s = None
            
            print("Waiting 2 seconds for socket cleanup...")
            time.sleep(2)
            
            print("Server shutdown complete")
       
    def generate_html(self, params = None):
        """
        Subclass Webserver, and override generate_html to change its capabilities
        This is a simple implementation, capable of only serving a single web page.

        To allow multiple pages, a micropython webserver implementation such as
        Microdot, TinyWeb or MicroPyServer is strongly recommended.
        
        Any parameters received, either via GET or POST is passed through as
        the params parameter.

        """

        html = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <title>Pico Web Server</title>
            <link rel="icon" href="data:;base64,=">
            </head>
            <body>
            <h1>Network Status</h1>
            <pre>{self._net.getStatusString()}</pre>
            <pre>Params: {params}</pre>
            </body></html>"""
        return html
    
    def parse_data(self, data):
        """Parse form data from GET or POST request"""
        try:
            # Simple parsing for form data
            params = {}
            if data:
                pairs = data.split('&')
                for pair in pairs:
                    if '=' in pair:
                        key, value = pair.split('=', 1)
                        # Simple URL decoding
                        value = value.replace('+', ' ')
                        params[key] = value
            return params
        except:
            return {}
        
    def parse_request(self, request):
        """Parse HTTP request and return an array of GET parameters"""

        try:
            # Simple parsing for GET parameters
            params = {}
            print(f"Request is {request}")
            
            if request.startswith('POST'):
                # Extract POST data
                lines = request.split('\r\n')
                post_data = lines[-1] if lines else ""                    
                params = self.parse_data(post_data)
            elif request.startswith('GET'):
                lines = request.split('\r\n')
                print(f"Lines: {lines}")
                url = lines[0].split()[1]
                if '?' in url:
                    params_str = url.split('?', 1)[1]
                    params = self.parse_data(params_str)
            else:
                Log.e("We only support GET and POST requests!")
            return params
        except Exception as e:
            Log.e(e)
            return {}
