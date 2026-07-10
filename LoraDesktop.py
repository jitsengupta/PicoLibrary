"""
# LoraDesktop.py
# Desktop implementation of the LoRa controller using pyserial
# Author: Arijit Sengupta
"""

import time
from Log import *
from LoraDevice import LoraDevice

class LoraDesktop(LoraDevice):
    """
    A subclass of LoraDevice designed to run on desktop (Mac, PC, Linux) 
    using the 'pyserial' package to communicate with a LoRa module over USB-to-TTL.

    Parameters:
    ----------
    port : str
        The serial port name (e.g. '/dev/tty.usbserial-10' or 'COM3')
    baudrate : int, optional
        The serial baudrate, default: 9600
    timeout : int, optional
        Read timeout in milliseconds (default: 1000)

    Examples:
    ---------
    1. Instantiating on desktop:
       lora = LoraDesktop(port='/dev/tty.usbserial-10', baudrate=9600)
       if lora.ping():
           Log.i("Successfully pinged LoRa module on desktop")
    """

    def __init__(self, port, baudrate=9600, timeout=1000):
        # We intentionally bypass LoraDevice / UARTDevice constructors to avoid MicroPython machine.UART dependency
        self._uart_id = port
        self._baudrate = baudrate
        self._timeout = timeout
        self._in_at_mode = False
        self._uart = None
        self._init_desktop_serial(port, baudrate, timeout)
        Log.i(f"LoraDesktop: Initialized LoRa controller on port {port}.")

    def _init_desktop_serial(self, port, baudrate, timeout):
        """Initializes pyserial connection or falls back to MockSerial if module/port is missing."""
        try:
            import serial
            
            class PySerialUARTWrapper:
                def __init__(self, port, baudrate, timeout_ms):
                    self._ser = serial.Serial(port, baudrate, timeout=timeout_ms / 1000.0)
                
                def write(self, data):
                    return self._ser.write(data)
                
                def read(self, nbytes=None):
                    if nbytes is None:
                        if self._ser.in_waiting > 0:
                            return self._ser.read(self._ser.in_waiting)
                        return b""
                    return self._ser.read(nbytes)
                
                def readline(self):
                    return self._ser.readline()
                
                def any(self):
                    return self._ser.in_waiting
                
                def init(self, baudrate, **kwargs):
                    self._ser.baudrate = baudrate
                    if 'timeout' in kwargs:
                        self._ser.timeout = kwargs['timeout'] / 1000.0

                def close(self):
                    self._ser.close()

            # Test opening the port; if it fails (e.g. port doesn't exist), fall back to Mock
            try:
                self._uart = PySerialUARTWrapper(port, baudrate, timeout)
                Log.i(f"LoraDesktop: Connected to serial port {port}.")
            except Exception as e:
                Log.d(f"LoraDesktop: Could not open serial port {port} ({e}). Falling back to MockSerial.")
                self._use_mock_serial(port, baudrate, timeout)
                
        except ImportError:
            Log.d("LoraDesktop: pyserial module not found. Falling back to MockSerial.")
            self._use_mock_serial(port, baudrate, timeout)

    def _use_mock_serial(self, port, baudrate, timeout):
        """Initializes Mock UART wrapper for local desktop testing."""
        class MockSerial:
            def __init__(self, port, baudrate, timeout):
                self.port = port
                self.baudrate = baudrate
                self.timeout = timeout
                self._buffer = bytearray()
                self._in_at_mode = False
            
            def write(self, data):
                Log.d(f"[Mock Serial {self.port} Write]: {data}")
                if data == b"+++\r\n":
                    if not self._in_at_mode:
                        self._in_at_mode = True
                        self._buffer.extend(b"Entry AT\r\n")
                    else:
                        self._in_at_mode = False
                        self._buffer.extend(b"Exit AT\r\n")
                elif data == b"AT\r\n":
                    self._buffer.extend(b"OK\r\n")
                elif data == b"AT+RESET\r\n":
                    self._buffer.extend(b"OK\r\n")
                elif data == b"AT+ADDRESS=120\r\n":
                    self._buffer.extend(b"OK\r\n")
                elif data == b"AT+ADDRESS?\r\n":
                    self._buffer.extend(b"+ADDRESS=120\r\nOK\r\n")
                elif data == b"AT+NETWORKID=18\r\n":
                    self._buffer.extend(b"OK\r\n")
                elif data == b"AT+NETWORKID?\r\n":
                    self._buffer.extend(b"+NETWORKID=18\r\nOK\r\n")
                elif data == b"AT+HELP\r\n":
                    self._buffer.extend(b"AT Commands Help:\r\nAT+ADDRESS=<addr>\r\nAT+NETWORKID=<id>\r\nOK\r\n")
                return len(data)
            
            def read(self, nbytes=None):
                if nbytes is None:
                    res = bytes(self._buffer)
                    self._buffer = bytearray()
                    return res
                res = bytes(self._buffer[:nbytes])
                self._buffer = self._buffer[nbytes:]
                return res
            
            def readline(self):
                idx = self._buffer.find(b'\n')
                if idx == -1:
                    res = bytes(self._buffer)
                    self._buffer = bytearray()
                    return res
                res = bytes(self._buffer[:idx+1])
                self._buffer = self._buffer[idx+1:]
                return res
            
            def any(self):
                return len(self._buffer)
            
            def init(self, baudrate, **kwargs):
                self.baudrate = baudrate
                if 'timeout' in kwargs:
                    self.timeout = kwargs['timeout']

            def close(self):
                pass

        self._uart = MockSerial(port, baudrate, timeout)


if __name__ == "__main__":
    Log.level = ALL
    Log.name = "LoraDesktopTest"
    
    Log.i("Starting LoraDesktop tests...")
    
    # Initialize LoraDesktop (port '/dev/tty.mock' will trigger MockSerial fallback if it doesn't exist)
    #    lora = LoraDesktop(port="/dev/tty.mock", baudrate=9600)
    lora = LoraDesktop(port="/dev/cu.usbserial-1430", baudrate=9600)

    # Test ping
    ping_ok = lora.ping()
    Log.i(f"Ping response: {ping_ok}")
    assert ping_ok is True, "Ping test failed"
    
    '''
    # Test setting Address
    set_addr_ok = lora.set_address(120)
    Log.i(f"Set Address response: {set_addr_ok}")
    assert set_addr_ok is True, "Set Address failed"

    # Test getting Address
    addr = lora.get_address()
    Log.i(f"Get Address: {addr}")
    assert addr == 120, f"Get Address mismatch: expected 120, got {addr}"
    '''

    # Test get_info method
    info_text = lora.get_info()
    Log.i(f"Info/Help Response:\n{info_text}")
    assert "VERSION" in info_text, "get_info method did not return expected command help"

    # Test sending transparency data
    bytes_sent = lora.send_message("Desktop test message")
    Log.i(f"Transparent sent bytes: {bytes_sent}")
    assert bytes_sent == 20, "Transparent send failed"
    
    Log.i("Testing complete - LoraDesktop verified successfully.")
