"""
# Lights.py
# implementation of different types of lights
# both digitally controlled (on/off)
# or PWM-controlled (dimming) to set brightness
# Author: Arijit Sengupta
"""

import utime
from machine import Pin, PWM
from Log import *
import _thread
MAX = 65535

baton = _thread.allocate_lock()

class Light:
    """
    The Light base class - just an LED controlled by a digital IO
    Pin. Save the pin in an instance variable
    """
    
    def __init__(self, pin, name="Unnamed"):
        """
        Light constructor - save the pin and set it to OUTPUT mode
        pin is the NUMBER of the pin that the LED is connected to. So
        if connecting to GP21, pass the value 21 to pin        
        name is an optional name of the light
        """
            
        Log.i(f"Light: constructor")
        self._name = name
        self._pin = pin
        self._blinking = False
        self._led = Pin(self._pin, Pin.OUT)  # We need this to use the IO functions

    def on(self):
        """ on: Turn the light on """
        
        Log.i(f"Light: turning on {self._name} light at pin {self._pin}")
        self._led.value(1)

    def off(self):
        """ off: turn the light off """
        
        Log.i(f"Light: turning off {self._name} light at pin {self._pin}")
        self._led.value(0)

    def flip(self):
        """ flip: turn off if it was on, on if it was off """
        
        Log.i(f"Light: Toggling {self._name} light at pin {self._pin}")
        self._led.toggle()

    def blink(self, delay=0.5, times=1):
        """ blink: turn on for delay sec, off for delay sec [times] times"""

        Log.i(f"Light: Blink {self._name} {times} times for {delay} sec")
        for x in range(0,times):
            self.on()
            utime.sleep(delay)
            self.off()
            utime.sleep(delay)


class DimLight(Light):
    """
    The Dimmable Light subclass - will have the standard on off methods
    and in addition will have the ability to set brightness
    """

    def __init__(self, pin, name="Unnamed"):
        """ Dimmable light constructor """

        Log.i("Dimmable light constructor")
        super().__init__(pin, name)
        self._pwm = PWM(self._led)  # Create an instance of PWM object (pulse-width modulation)
        self._pwm.freq(100000)   # set frequency to 100 khz
        self._onState = False
        self._running = False

    def on(self):
        """ Turn on - full brightness max is 255 """
        
        self._running = False
        self._onState = True
        Log.i(f"Dimlight: turn Light {self._name} on (full brightness)")
        self.setBrightness(MAX)

    def off(self):
        """  Turn off - set brightness to 0 """
        
        self._running = False
        self._onState = False
        Log.i(f"Dimlight - turn Light {self._name} off (brightness 0)")
        self.setBrightness(0)

    def flip(self):
        """ flip: turn off if it was on, on if it was off """
        
        Log.i(f"Light: Toggling {self._name} light at pin {self._pin}")
        if self._onState:
            self.off()
        else:
            self.on()       
        
    def setBrightness(self, brightness):
        """ Set brightness to a specific level 0-255 """

        Log.i(f"Dimlight: setting Light {self._name} brightness to {brightness}")
        if (brightness == MAX):
            self._pwm.duty_u16(MAX)
        else:
            self._pwm.duty_u16(brightness * brightness)
        
        if brightness < 50:
            self._onState = False
        else:
            self._onState = True

    def upDown(self):
        """
        # Do a quick demo of going up and down full brightness levels
        # Here it is better to use ChangeDutyCycle
        """
        
        Log.i(f"Dimlight: do an up-down demo on Light {self._name}")
        self._running = True
        dc = 0
        for i in range (0, 25):
            if not self._running:
                break
            dc += 10
            self.setBrightness(dc)
            utime.sleep_ms(100)

        for i in range (0, 25):
            if not self._running:
                break
            dc -= 10
            self.setBrightness(dc)
            utime.sleep_ms(100)
        self._running = False