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

# METHOD CONSTANTS - should not be needed outside - use getJson, postJson etc
GET = 1001
POST = 1002
PUT = 1003
DELETE = 1004 # not yet supported

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
        self._status_code = 0 # last status code from network operations
        
    def connect(self, ssid, password=None, max_wait=10, pm_off=True):
        """
        Connect to the wifi network with a maximum wait time

        Parameters:
        ----------
        ssid : str
            The SSID of the network to connect to
        password : str, optional
            The password of the network to connect to
        max_wait : int, optional
            The maximum time to wait for the connection to establish
        pm_off : bool, optional
            Whether to disable power management - turned off by default
        """

        self._sta = network.WLAN(network.STA_IF)
        self._sta.active(True)
        
        if pm_off:
            # Disable power management to improve connection stability
            try:
                self._sta.config(pm=0xa11140)
            except Exception as e:
                Log.d(f"Could not disable WLAN power management: {e}")

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
            self._status_code = self._sta.status()
            raise RuntimeError('Network Connection has failed!')
        else:
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
        
    def updateTime(self, std_offset = -5):
        """ Update local time using NTP with automatic US Daylight Saving Time (DST) detection """
        import ntptime
        import machine
        
        try:
            # Sync system time with NTP (gives UTC)
            ntptime.settime()
            utc_time = time.time()
            
            # First, convert UTC to standard time (e.g., EST = UTC - 5)
            std_time = utc_time + (std_offset * 3600)
            tm = time.gmtime(std_time)
            
            # Check if DST is active for the calculated standard time
            year, month, day, hour = tm[0], tm[1], tm[2], tm[3]
            
            is_dst = False
            if month > 3 and month < 11:
                is_dst = True
            elif month == 3:
                # DST starts 2nd Sunday in March
                # Find weekday of March 1st (0 = Monday, 6 = Sunday)
                w = time.gmtime(time.mktime((year, 3, 1, 0, 0, 0, 0, 0)))[6]
                dst_start = 8 + (6 - w) % 7
                if day > dst_start or (day == dst_start and hour >= 2):
                    is_dst = True
            elif month == 11:
                # DST ends 1st Sunday in November
                # Find weekday of November 1st
                w = time.gmtime(time.mktime((year, 11, 1, 0, 0, 0, 0, 0)))[6]
                dst_end = 1 + (6 - w) % 7
                if day < dst_end or (day == dst_end and hour < 2):
                    is_dst = True
            
            # Apply an extra hour if DST is active
            if is_dst:
                local_time = std_time + 3600
                tm = time.gmtime(local_time)
            
            # Update RTC
            # tm: (year, month, mday, hour, minute, second, weekday, yearday)
            # RTC: (year, month, day, weekday, hour, minute, second, subsecond)
            machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))
        except Exception as e:
            Log.e(f"Could not update time from NTP: {e}")
            
        return time.localtime()


    def getWeatherByLocation(self, location_name):
        """ Get temperature and humidity from Open-Meteo for a given city/state name
            Returns a dictionary with resolved_location,
            temperature, humidity and rain_chance
        """
        query = location_name.replace(" ", "%20")
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={query}&count=1"
        geo_data = self.getJson(geo_url)
        
        if not geo_data or "results" not in geo_data:
            Log.e(f"Could not find coordinates for location: {location_name}")
            return None
            
        location_info = geo_data["results"][0]
        lat = location_info["latitude"]
        lon = location_info["longitude"]
        resolved_name = f"{location_info.get('name')}, {location_info.get('admin1', '')}"
        
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,precipitation_probability&temperature_unit=fahrenheit"
        weather_data = self.getJson(weather_url)
        
        if weather_data and "current" in weather_data:
            current = weather_data["current"]
            return {
                "resolved_location": resolved_name,
                "temperature": current["temperature_2m"],
                "humidity": current["relative_humidity_2m"],
                "rain_chance": current["precipitation_probability"]
            }
        
        return None

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

    def getJson(self, url, headers=None, auth=None, token=None):
        """
        Get the JSON data from a REST API. Only valid JSON returns supported.
        
        Parameters:
        REQUIRED: URL endpoint for the GET request
        
        Optional:
        headers: Any additional headers that need to be sent
        auth: Basic authentication as a tuple (username, password)
        token: Bearer token if it is to be used as authentication for retrieving
        
        Obviously only 1 should be used if auth is needed.
        
        Returns dictionary from JSON returned by web service. Returns None
        if valid JSON was not obtained.
        Check status_code after calling if None is returned        
        """
        
        # Moving all request messages into one method to avoid duplicate code
        return self._send(url, method=GET, data=None, headers=headers, auth=auth, token=token)

    def postJson(self, url, data, headers=None, auth=None, token=None):
        """
        Use POST to insert data into a remote webservice. 

        The webservice should be configured to accept data in JSON format.
        Passed in data should be a dictionary with all parameters
        that are expected by this webservice.
        
        Parameters:
        REQUIRED: URL endpoint for the GET request
        data = dictionary containing data to be sent.
           Note that this is converted to JSON with a
           content-type application/json.
           if urlencoded data is to be sent by PUT,
           please include in the URL itself.
           data may be set to None if no data needs to be PUT
        
        Optional:
        headers: Any additional headers needed.
        auth: Basic authentication as a tuple (username, password)
        token: Bearer token if it is to be used as authentication for retrieving
        
        Obviously only 1 should be used if auth is needed. 
        
        Returns dictionary from JSON returned by web service. Returns None
        if valid JSON was not obtained.
        Check status_code after calling if None is returned
        """
        return self._send(url, method=POST, data=data, headers=headers, auth=auth, token=token)
    
    
    def putJson(self, url, data, headers=None, auth=None, token=None):
        """
        Use the PUT method to update data into a remote webservice
        The webservice should be configured to accept data in JSON format.
        Passed in data should be a dictionary with all parameters
        that are expected by this webservice.
        
        Parameters:
        REQUIRED: URL endpoint for the GET request
        data = dictionary containing data to be sent.
           Note that this is converted to JSON with a
           content-type application/json.
           if urlencoded data is to be sent by PUT,
           please include in the URL itself.
           data may be set to None if no data needs to be PUT
        
        Optional:
        headers: Any additional headers needed.
        auth: Basic authentication as a tuple (username, password)
        token: Bearer token if it is to be used as authentication for retrieving
        
        Obviously only 1 should be used if auth is needed. 

        Returns dictionary from JSON returned by web service. Returns None
        if valid JSON was not obtained.
        Check status_code after calling if None is returned
        """
        return self._send(url, method=PUT, data=data, headers=headers, auth=auth, token=token)
    
    def _send(self, url, method, data=None, headers=None, auth=None, token=None, timeout=30):
        """
        Internal method to handle all requests
        """
        if method != GET: # Get method doesn't need content type
            if not headers:
                headers = {
                    "Content-Type": "application/json"
                }
            elif not "Content-Type" in headers:
                headers["Content-Type"] = "application/json"
        
        if token:
            bearer = f"Bearer {token}"
            if headers:
                headers["Authorization"] = bearer
            else:
                headers = {"Authorization": bearer}
            
        try:
            if not self.isConnected():
                raise RuntimeError("Not connected to any network")
            
            if method == GET:
                response=requests.get(url, headers=headers, auth=auth, timeout=timeout)
            elif method == PUT:
                response=requests.put(url,
                             json = data,
                             headers=headers, auth=auth, timeout=timeout)
            elif method == POST:
                response=requests.post(url,
                             json = data,
                             headers=headers, auth=auth, timeout=timeout)
            else:
                raise RuntimeError("Method not supported")
            
            self.status_code = response.status_code
            jsondata = response.json()
            Log.d(f"Status Code:{self.status_code}")
            response.close()
            return jsondata
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
        
        # Bind to 0.0.0.0 so we can listen on all interfaces, even if they connect/reconnect later.
        addr = socket.getaddrinfo('0.0.0.0', port)[0][-1]
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
                        Log.e(f"Port {port} in use, waiting 2 seconds... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(2)
                        continue
                    else:
                        Log.e(f"Port {port} still in use after {max_retries} attempts")
                        Log.e("Try changing the port number or wait a bit longer")
                        raise
                else:
                    raise
        
        s.listen(1)
        
        Log.d(f"Web server started on port {port}")
        Log.d("Server is running... Press Ctrl+C to stop")
        
        Log.i(f"Serving UI on port {port} (access via http://{self._net.getLocalIp()})")
        cl = None
        
        try:
            while True:
                try:
                    cl, addr = s.accept()
                    Log.i(f"Client connected from {addr}")
                    
                    req_raw = b""
                    while b"\r\n\r\n" not in req_raw and len(req_raw) < 4096:
                        chunk = cl.recv(512)
                        if not chunk:
                            break
                        req_raw += chunk
                    
                    if b"\r\n\r\n" in req_raw:
                        headers, body = req_raw.split(b"\r\n\r\n", 1)
                        content_length = 0
                        for line in headers.split(b"\r\n"):
                            if line.lower().startswith(b"content-length:"):
                                try:
                                    content_length = int(line.split(b":", 1)[1].strip())
                                except:
                                    pass
                                break
                        
                        while len(body) < content_length and len(req_raw) < 8192:
                            chunk = cl.recv(512)
                            if not chunk:
                                break
                            body += chunk
                        
                        request = (headers + b"\r\n\r\n" + body).decode('utf-8', 'ignore')
                    else:
                        request = req_raw.decode('utf-8', 'ignore')
                    
                    Log.d(f"Request: {request[:200] + '...' if len(request) > 200 else request}")
                    
                    params = self.parse_request(request)
                    Log.d(f"Params: {params}")
                    
                    # Serve a simple HTML page with the status            
                    html = self.generate_html(params)
                    response = f"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n{html}"
                    
                    cl.sendall(response.encode('utf-8'))
                    cl.close()
                except KeyboardInterrupt:
                    Log.e("\nKeyboard interrupt received - shutting down server gracefully...")
                    break
                except Exception as e:
                    Log.e(f"Error handling request: {e}")
                    if cl:
                        try:
                            cl.close()
                        except:
                            pass
                        cl = None
                        
        except KeyboardInterrupt:
            Log.e("\nKeyboard interrupt received - shutting down server gracefully...")
        finally:
            # Clean up any remaining connection
            if cl:
                try:
                    cl.close()
                    Log.d("Active connection closed")
                except:
                    pass
            
            # Close the server socket
                try:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, b'\x00' * 8)  # Immediate close
                except:
                    pass
                try:
                    s.close()
                    Log.d("Server socket closed")
                except:
                    pass
                s = None
            
            Log.d("Waiting 2 seconds for socket cleanup...")
            time.sleep(2)
            
            Log.d("Server shutdown complete")
       
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
            request_clean = request.lstrip()
            Log.i(f"Request (first 150 chars): {request_clean[:150]}")
            
            if request_clean.startswith('POST'):
                # Extract POST data by splitting headers and body
                parts = request_clean.split('\r\n\r\n', 1)
                post_data = parts[1] if len(parts) > 1 else ""
                Log.i(f"POST body raw data: {post_data}")
                params = self.parse_data(post_data)
            elif request_clean.startswith('GET'):
                lines = request_clean.split('\r\n')
                url = lines[0].split()[1]
                if '?' in url:
                    params_str = url.split('?', 1)[1]
                    params = self.parse_data(params_str)
            else:
                Log.e(f"Unsupported request type. Request starts with: {request_clean[:50]}")
            Log.i(f"Parsed Params: {params}")
            return params
        except Exception as e:
            Log.e(f"Error parsing request: {e}")
            return {}

if __name__ == "__main__":
    net = Net()
    net.startAccessPoint("PicoAP", "micropythoN")
    Log.i(net.getAccessPointInfo())