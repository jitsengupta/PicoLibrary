# test.py Test program for IR remote control decoder
# Supports Pyboard, ESP32 and ESP8266

# Author: Peter Hinch
# Copyright Peter Hinch 2020-2022 Released under the MIT license

# Run this to characterise a remote.

from sys import platform
import time
import gc
from machine import Pin, freq
from micropython_ir import *

# PIN DEFINITIONS
IR_PIN = 4  # Pin for IR receiver

class IRReceiver:
    """
    IR receiver class. Instantiate with a pin and a callback function.
    Create a receiver with a pin, name and a handler object. The handler
    object should have a method named ircodeReceived. This method will be
    called with the received data, address and control code.
    """

    def __init__(self, pin=IR_PIN, name='IR', handler=None):
        self._pin = Pin(pin, Pin.IN)
        self._name = name
        self._handler = handler
        self._ir = NEC_16(self._pin, self._cb)
        self._ir.error_function(print_error)  # Show debug information
        self._ir.verbose = True

    def setHandler(self, handler):
        """
        Set the handler object for the IR receiver.
        """
        
        self._handler = handler

    def close(self):
        """ 
        Close the IR receiver.
        """
        self._ir.close()
        gc.collect()

    def _cb(self, data, addr, ctrl):
        if self._handler:
            self._handler.ircodeReceived(self._name, data, addr, ctrl)
        else:
            print(f"{self._name} Data 0x{data:02x} Addr 0x{addr:04x} Ctrl 0x{ctrl:02x}")
