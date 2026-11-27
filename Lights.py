"""
# Lights.py
# implementation of different types of lights
# both digitally controlled (on/off)
# or PWM-controlled (dimming) to set brightness
# Author: Arijit Sengupta
"""

import time
try:
    from machine import Pin, PWM
except ImportError:
    class Pin:
        IN = 0
        OUT = 1
        def __init__(self, id, mode=-1, value=None):
            self.id = id
            self.mode = mode
            self._val = 0
        def __call__(self, val=None):
            if val is not None:
                self._val = val
            return self._val
        def value(self, val=None):
            return self.__call__(val)
        def toggle(self):
            self._val = 1 if self._val == 0 else 0
            return self._val

    class PWM:
        def __init__(self, pin):
            self.pin = pin
            self._duty = 0
        def freq(self, f):
            pass
        def duty_u16(self, val):
            self._duty = val

from Log import *
MAX = 65535

# Some color definitions - shared by DimLight and LightStrip
# May eventually move to a separate module

BLACK = (0, 0, 0)
RED = (255, 0, 0)
ORANGE = (255, 60, 0)
YELLOW = (255, 200, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
PURPLE = (180, 0, 255)
CYAN = (0, 255, 255)
INDIGO = (75, 0, 130)
WHITE = (255, 255, 255)
COLORS = (BLACK, RED, YELLOW, GREEN, CYAN, BLUE, PURPLE, WHITE, ORANGE)

class Light:
    """
    The Light base class - just an LED controlled by a digital IO
    Pin. Save the pin in an instance variable
    """
    
    def __init__(self, pin, name="Unnamed", active_high=True):
        """
        Light constructor - save the pin and set it to OUTPUT mode
        pin is the NUMBER of the pin that the LED is connected to. So
        if connecting to GP21, pass the value 21 to pin        
        name is an optional name of the light
        active_high is True for active-HIGH LEDs (default), False for active-LOW LEDs
        """
            
        Log.i(f"Light: constructor")
        self._name = name
        self._pin = pin
        self._active_high = active_high
        self._blinking = False
        self._led = Pin(self._pin, Pin.OUT)  # We need this to use the IO functions
        self.off()

    def on(self):
        """ on: Turn the light on """
        
        Log.i(f"Light: turning on {self._name} light at pin {self._pin}")
        self._led.value(1 if self._active_high else 0)

    def off(self):
        """ off: turn the light off """
        
        Log.i(f"Light: turning off {self._name} light at pin {self._pin}")
        self._led.value(0 if self._active_high else 1)

    def flip(self):
        """ flip: turn off if it was on, on if it was off """
        
        Log.i(f"Light: Toggling {self._name} light at pin {self._pin}")
        if self.isOn():
            self.off()
        else:
            self.on()

    def blink(self, delay=0.5, times=1):
        """ blink: turn on for delay sec, off for delay sec [times] times"""

        Log.i(f"Light: Blink {self._name} {times} times for {delay} sec")
        for x in range(0,times):
            self.on()
            time.sleep(delay)
            self.off()
            time.sleep(delay)

    def isOn(self)->bool:
        """
        Check to see if the light is on or off
        """

        return self._led.value() == (1 if self._active_high else 0)


class DimLight(Light):
    """
    The Dimmable Light subclass - will have the standard on off methods
    and in addition will have the ability to set brightness
    """

    def __init__(self, pin, name="Unnamed", active_high=True, freq=1000):
        """ Dimmable light constructor """

        Log.i("Dimmable light constructor")
        super().__init__(pin, name, active_high=active_high)
        self._pwm = PWM(self._led)  # Create an instance of PWM object (pulse-width modulation)
        self._pwm.freq(freq)   # Set frequency, default 1 kHz (standard for LEDs)
        self._onState = False
        self._running = False

    def on(self):
        """ Turn on - full brightness max is 255 """
        
        self._running = False
        self._onState = True
        Log.i(f"Dimlight: turn Light {self._name} on (full brightness)")
        self.setBrightness(1)

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
        """ Set brightness to a specific level 0-1 """

        Log.i(f"Dimlight: setting Light {self._name} brightness to {brightness}")
        duty = MAX if brightness == 1 else int(MAX * brightness)
        if not self._active_high:
            duty = MAX - duty
        self._pwm.duty_u16(duty)

        if brightness < 0.05:
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
        for i in range (0, 10):
            if not self._running:
                break
            dc += 0.1
            self.setBrightness(dc)
            time.sleep_ms(100)

        for i in range (0, 10):
            if not self._running:
                break
            dc -= 0.1
            if dc < 0:
                dc = 0
            self.setBrightness(dc)
            time.sleep_ms(100)
        self._running = False

## The following code is for testing purposes only
if __name__ == "__main__":
    # Create a light and turn it on
    light = Light('LED', "Test Light")
    print(light)
    light.on()
    time.sleep(1)
    light.off()

    # Create a dimmable light and set brightness
    dim_light = DimLight(3, "Test Dim Light")
    print(dim_light)
    dim_light.on()
    time.sleep(1)
    dim_light.setBrightness(0.5)  # Set brightness to 50%
    time.sleep(1)
    dim_light.off()

    # Test updown functionality
    dim_light.upDown()
    
    # Turn off the lights
    light.off()
    dim_light.off()
    Log.i("Testing complete - all lights turned off")