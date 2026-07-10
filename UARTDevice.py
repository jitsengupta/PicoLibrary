"""
# UARTDevice.py
# Base class wrapper around machine.UART for serial communication
# Author: Arijit Sengupta
"""

import time
from Log import *

class UARTDevice:
    """
    A base class for serial communication devices wrapping machine.UART.
    Provides standard API for reading, writing, and configuring UART interfaces.

    Parameters:
    ----------
    uart_id : int
        The UART peripheral ID (usually 0 or 1 on RP2040)
    baudrate : int, optional
        The communication speed in bits per second (default: 9600)
    tx_pin : int, optional
        The GPIO pin number for TX (default: None, uses board defaults)
    rx_pin : int, optional
        The GPIO pin number for RX (default: None, uses board defaults)
    timeout : int, optional
        The read timeout in milliseconds (default: 1000)

    Examples:
    ---------
    1. Creating a standard UART device:
       device = UARTDevice(uart_id=0, baudrate=9600, tx_pin=0, rx_pin=1)
       device.send("Hello World")
       response = device.receive()
    """

    def __init__(self, uart_id, baudrate=9600, tx_pin=None, rx_pin=None, timeout=1000):
        self._uart_id = uart_id
        self._baudrate = baudrate
        self._tx_pin = tx_pin
        self._rx_pin = rx_pin
        self._timeout = timeout
        self._uart = None
        self._init_uart()

    def _init_uart(self):
        """Initializes or re-initializes the underlying MicroPython machine.UART."""
        try:
            from machine import UART, Pin
            kwargs = {'baudrate': self._baudrate, 'timeout': self._timeout}
            if self._tx_pin is not None and self._rx_pin is not None:
                kwargs['tx'] = Pin(self._tx_pin)
                kwargs['rx'] = Pin(self._rx_pin)
            self._uart = UART(self._uart_id, **kwargs)
            Log.i(f"UARTDevice: Initialized UART {self._uart_id} at {self._baudrate} baud.")
        except ImportError:
            # Fallback/Mock UART for testing environments without machine module
            Log.d("UARTDevice: machine module not found. Falling back to Mock UART.")
            class MockUART:
                def __init__(self, uart_id, baudrate, timeout):
                    self.uart_id = uart_id
                    self.baudrate = baudrate
                    self.timeout = timeout
                    self._buffer = bytearray()
                    self._in_at_mode = False
                
                def write(self, data):
                    Log.d(f"[Mock UART {self.uart_id} Write]: {data}")
                    # Dynamic responses for automated self-tests
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
                    elif data == b"AT+HELP\r\n":
                        self._buffer.extend(b"AT Commands Help:\r\nAT+ADDRESS=<addr>\r\nAT+NETWORKID=<id>\r\nOK\r\n")
                    elif data == b"AT+ADDRESS=120\r\n":
                        self._buffer.extend(b"OK\r\n")
                    elif data == b"AT+ADDRESS?\r\n":
                        self._buffer.extend(b"+ADDRESS=120\r\nOK\r\n")
                    elif data == b"AT+NETWORKID=18\r\n":
                        self._buffer.extend(b"OK\r\n")
                    elif data == b"AT+NETWORKID?\r\n":
                        self._buffer.extend(b"+NETWORKID=18\r\nOK\r\n")
                    elif data.startswith(b"AT+IPR="):
                        self._buffer.extend(b"OK\r\n")
                    elif data.startswith(b"AT+PARAMETER="):
                        self._buffer.extend(b"OK\r\n")
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

            self._uart = MockUART(self._uart_id, self._baudrate, self._timeout)

    def send(self, data) -> int:
        """
        Sends data over the UART interface.

        Parameters:
        ----------
        data : str or bytes
            The data payload to be sent. If string, it is encoded to UTF-8.

        Returns:
        -------
        int
            The number of bytes written.
        """
        if isinstance(data, str):
            payload = data.encode('utf-8')
        else:
            payload = data
        
        if self._uart:
            return self._uart.write(payload)
        return 0

    def receive(self, num_bytes=None, timeout_ms=None) -> bytes:
        """
        Reads bytes from the UART interface.

        Parameters:
        ----------
        num_bytes : int, optional
            Maximum number of bytes to read. If None, reads all available bytes.
        timeout_ms : int, optional
            Specific timeout for this read operation in milliseconds.

        Returns:
        -------
        bytes
            The read data bytes.
        """
        # Temporal timeout configuration if needed
        if timeout_ms is not None and timeout_ms != self._timeout:
            self._timeout = timeout_ms
            if hasattr(self._uart, 'init'):
                self._uart.init(baudrate=self._baudrate, timeout=self._timeout)

        if self._uart:
            return self._uart.read(num_bytes) or b''
        return b''

    def readline(self) -> str:
        """
        Reads a line of text terminated by a newline character.

        Returns:
        -------
        str
            The line read, decoded as a UTF-8 string.
        """
        if self._uart:
            line_bytes = self._uart.readline()
            if line_bytes:
                return line_bytes.decode('utf-8', 'ignore')
        return ""

    def any(self) -> int:
        """
        Checks if there are bytes available in the receive buffer.

        Returns:
        -------
        int
            The number of bytes available, or 0 if none.
        """
        if self._uart and hasattr(self._uart, 'any'):
            return self._uart.any()
        return 0

    def flush(self):
        """Clears all unread data from the UART buffer."""
        while self.any() > 0:
            self.receive(self.any())

    def set_baudrate(self, baudrate):
        """
        Changes the UART baud rate.

        Parameters:
        ----------
        baudrate : int
            The new baud rate.
        """
        self._baudrate = baudrate
        if self._uart and hasattr(self._uart, 'init'):
            self._uart.init(baudrate=self._baudrate, timeout=self._timeout)
            Log.i(f"UARTDevice: Baud rate updated to {self._baudrate}")

    def close(self):
        """Releases the UART/Serial interface."""
        if self._uart:
            if hasattr(self._uart, 'deinit'):
                self._uart.deinit()
            elif hasattr(self._uart, 'close'):
                self._uart.close()
            Log.i("UARTDevice: Closed serial connection.")


if __name__ == "__main__":
    Log.level = ALL
    Log.name = "UARTDeviceTest"
    
    Log.i("Starting UARTDevice tests...")
    
    # Instantiate class (will use Mock UART since we are running locally)
    dev = UARTDevice(uart_id=1, baudrate=9600)
    
    # Test send
    bytes_sent = dev.send("AT\r\n")
    Log.i(f"Sent {bytes_sent} bytes.")
    assert bytes_sent == 4, "Send byte count mismatch"
    
    # Mock some incoming data directly into the Mock UART buffer for read testing
    if hasattr(dev._uart, '_buffer'):
        dev._uart._buffer.extend(b"OK\r\n")
    
    # Test any()
    available = dev.any()
    Log.i(f"Bytes available: {available}")
    assert available == 4, "Available byte count mismatch"
    
    # Test readline
    line = dev.readline()
    Log.i(f"Readline result: {repr(line)}")
    assert line == "OK\r\n", f"Readline mismatch: expected 'OK\\r\\n', got {repr(line)}"
    
    # Test set_baudrate
    dev.set_baudrate(115200)
    assert dev._baudrate == 115200, "Baudrate change not reflected"
    
    Log.i("Testing complete - UARTDevice verified successfully.")
