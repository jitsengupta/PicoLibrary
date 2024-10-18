"""
Keypad.py - a simple implementation of a mxn keypad
typically used for providing input to microcontrollers

This is a fairly simple implementation and does use
a blocking scan, so cannot use this for detecting multi-presses

# Author: Arijit Sengupta
"""
from machine import Pin
import utime

default_keys = [
    ['1','2','3','A'],
    ['4','5','6','B'],
    ['7','8','9','C'],
    ['*','0','#','D']
]

class Keypad:
    """
    Keypad is a mxn matrix - read by turning the rows into 
    outputs and columns into inputs. Read by setting each row
    high one at a time, then checking which column became high
    and returning the value at the column.

    These come in many sizes, so keeping it at least somewhat
    flexible to support keypads of different types, but
    defaulting to the standard hex keypads that are most
    commonly available.
    """

    def __init__(self, row_pins, col_pins):
        """
        Initialize the keypad - send in the pin numbers that
        connect the rows and pin numbers that connect the columns
        """
        self._lastscan = 0
        self._rows = len(row_pins)
        self._cols = len(col_pins)

        self._row_pins = [None] * self._rows
        self._col_pins = [None] * self._cols
        self._keys = default_keys

        for r in range(0, self._rows):
            self._row_pins[r] = Pin(row_pins[r], Pin.OUT)

        for c in range(0, self._cols):
            self._col_pins[c] = Pin(col_pins[c], Pin.IN, Pin.PULL_DOWN)

    def setKeys(self, keys = default_keys):
        """
        Set the keys if they are not the default
        hex keypad
        """

        self._keys = keys

    def scanKey(self,delay=250)->str:
        """
        Scan the keypad once and return if anything is detected
        to be pressed. returns None if nothing is pressed.
        
        To avoid multi-presses, if a request comes from scanKey within
        delay ms of the last valid scan, we are going to return None
        """
        if utime.ticks_ms()-self._lastscan < delay:
            return None
        for rowKey in range(self._rows):
            self._row_pins[rowKey].value(1)
            for colKey in range(self._cols):
                if self._col_pins[colKey].value() == 1:
                    key = self._keys[rowKey][colKey]
                    self._row_pins[rowKey].value(0)
                    self._lastscan = utime.ticks_ms()
                    return(key)
            self._row_pins[rowKey].value(0)
        return None

        