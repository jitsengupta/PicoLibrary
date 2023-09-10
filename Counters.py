"""
# Counters.py
# A collection of different kinds of counters that might be used for
# various projects
# Author: Arijit Sengupta
"""

import time
from machine import Timer

class Counter:
    """
    Counter base class - provides an internal count, an initiailzer and a reset method
    everything else should be defined at subclass level
    """
    
    def __init__(self):
        print("Counter: constructor")
        self._count = 0

    def reset(self):
        print("Counter - reset")
        self._count = 0

class UpDownCounter(Counter):
    """ A basic updown counter - can go up or down, can set up a min and max """
    
    def __init__(self, min = None, max = None):
        print("Updowncounter constructor")
        super().__init__()
        self._min = min
        self._max = max

    def up(self, step=1):
        """
        count up - with an optional step. Note that if the result will be less than max,
        no change will be made.
        """
                
        print("Updowncounter incrementing")
        if (self._max is None or self._count + step <= self._max):
            self._count = self._count + step

    def down(self, step=1):
        """
        Count down - with an optional step. Note that if the result will be less than min,
        no change will be made
        """
        
        print("Updowncounter decrementing")
        if (self._min is None or self._count - step >= self._min):
            self._count = self._count - step

    def __str__(self)->str:
        """ a string representation of the internal count """
        
        return f"{self._count}"

class TimeKeeper(Counter):
    """
    Keeps time as a count. Basically a stopwatch
    Internal count stores the number of ms of counting
    Can be stopped and started many times. Only reset will set
    count to 0
    """
    
    def __init__(self):
        print("Timekeeper: constructor")
        super().__init__()
        self._starttime = 0
        self._running = False

    def start(self):
        """ Start the timer. Note that if previously stopped, this will add to previous time """
        
        print("Timekeeper: start")
        """ If timer was already running, the start will get reset to the new time """

        self._starttime = time.ticks_ms()
        self._running = True

    def stop(self):
        """ Stop the timer. Count will save the # of ms elapsed """
        
        print("Timekeeper: stop")
        """ If it was already stopped, nothing to be done """
        if self._running:
            self._running = False
            self._count = self._count + time.ticks_diff(time.ticks_ms(),self._starttime)

    def reset(self):
        """ 
        Resetting the timer will set count to 0 and starttime to the current time 
        But timer keeps running if not stopped
        """
        super().reset()
        self._starttime = time.ticks_ms()

    def __str__(self) -> str:
        """ Get a string representation of time in HH:MM:SS.ms format """
        
        curtime = self._count + (time.ticks_diff(time.ticks_ms(),self._starttime) if self._running else 0)
        ms = curtime % 1000
        sec = (curtime // 1000) % 60
        min = (curtime // 60000) % 60
        hr = (curtime // 3600000)
        return f"{hr:02d}:{min:02d}:{sec:02d}.{ms:03d}"


class BaseTimer(Counter):
    """ 
    Decided to create a base class for the Software and Hardware timers
    since there are many properties in common. Now allowing no handlers in init
    but obviously a handler has to be set in order to ensure something happens when
    the time runs out.
    """

    def __init__(self, handler=None):
        super().__init__()
        self._handler = handler
        self._started = False

    def setHandler(self, handler):
        self._handler = handler

    def start(self, seconds):
        self._count = seconds
        self._started = True

    def cancel(self):
        self._started = False
        self._count = 0

    def reset(self):
        """ Make sure reset cancels the timer first """
        
        super().reset()
        self.cancel()
        
class HardwareTimer(BaseTimer):
    """
    This uses the hardware internal timer of the Pico. This does NOT WORK on the simulator!
    The internal count here is the timer setting that is not updated until reset or cancelled
    
    """
    
    def __init__(self, handler=None):
        """
        A hardware timer must be initialized with a handler. The handler must implement
        a timeout() method which will be called when the timer is up. Ideally, there
        should only be a single timer active at a time.
        """
        
        super().__init__(handler)
        self._timer = Timer(-1)

    def start(self, seconds):
        """ Start the timer with the number of seconds to use. """
        
        super().__start(seconds)
        self._timer.init(period = int(seconds*1000), mode=Timer.ONE_SHOT, callback = self.timeout)

    def cancel(self):
        """ Cancel the timer. Note that a normal stop will cause the handler callback. """
        
        if self._started:
            self._timer.deinit()
        super().cancel()
    
    def timeout(self, timer):
        self.cancel()
        self._handler.timeout()

class SoftwareTimer(BaseTimer):
    """
    A simpler software-based timer that will work on the simulator as well. Caller
    again implements a handler method, but will need to poll the timer using the
    check method at regular intervals. Check will not return anything, but will
    call the timeout function of the caller just like the hardware timer.
    """
    
    def __init__(self, handler):
        super().__init__()
        self._handler = handler
        self._starttime = 0
        self._started = False

    def start(self, seconds):
        """ Start the timer with a set number of seconds """
        
        print(f"Starting timer with {seconds} seconds")
        self._count = seconds
        self._starttime = time.ticks_ms()
        self._started = True

    def cancel(self):
        """ Cancel the timer - timeout hander will NOT be called """
        
        if self._started:
            self._starttime = 0
            print(f"{self._count} sec timer cancelled")
        super().cancel()

    def check(self):
        """
        Periodically call the check method - can be called from anywhere
        """
        
        if self._started and time.ticks_diff(time.ticks_ms(), self._starttime) > self._count * 1000:
            print(f"{self._count} sec timer is up")
            self._started = False
            self._count = 0
            self._handler.timeout()
