import utime
from machine import Pin, PWM
import _thread
MAX = 65535

baton = _thread.allocate_lock()

"""
The Light base class - just an LED controlled by a digital IO
Pin. Save the pin in an instance variable
"""
class Light:
    # Light constructor - save the pin and set it to OUTPUT mode
    def __init__(self, name, pin):
        print(f"Light: constructor")
        self._name = name
        self._pin = pin
        self._blinking = False
        self._led = Pin(self._pin, Pin.OUT)  # We need this to use the IO functions

    # on: Turn the light on
    def on(self):
        print(f"Light: turning on {self._name} light at pin {self._pin}")
        self._led.value(1)

    def off(self):
        print(f"Light: turning off {self._name} light at pin {self._pin}")
        self._led.value(0)

    def flip(self):
        print(f"Light: Toggling {self._name} light at pin {self._pin}")
        self._led.toggle()
        
    def blink(self, delayms=250):
        print(f"Light: Blinking {self._name} light at pin {self._pin} every {delayms}ms")
        self._blinking = True
        while(self._blinking):
            baton.acquire()
            self._on()
            utime.sleep(delayms)
            self.off()
            utime.sleep(delayms)
            baton.release()

"""
The Dimmable Light subclass - will have the standard on off methods
and in addition will have the ability to set brightness
"""
class DimLight(Light):
    # Dimmable light constructor
    def __init__(self, name, pin):
        print("Dimmable light constructor")
        super().__init__(name, pin)
        self._pwm = PWM(self._led)  # Create an instance of PWM object (pulse-width modulation)
        self._pwm.freq(100000)   # set frequency to 100 khz

    # Turn on - full brightness max is 255
    def on(self):
        print(f"Dimlight: turn Light {self._name} on (full brightness)")
        self.setBrightness(MAX)

    # Turn off - 0 brightness
    def off(self):
        print(f"Dimlight - turn Light {self._name} off (brightness 0)")
        self.setBrightness(0)

    # Set brightness to a specific level 0-255
    def setBrightness(self, brightness):
        print(f"Dimlight: setting Light {self._name} brightness to {brightness}")
        if (brightness == MAX):
            self._pwm.duty_u16(MAX)
        else:
            self._pwm.duty_u16(brightness * brightness)

    # Do a quick demo of going up and down full brightness levels
    # Here it is better to use ChangeDutyCycle
    def upDown(self):
        print(f"Dimlight: do an up-down demo on Light {self._name}")
        dc = 0
        for i in range (0, 25):
            dc += 10
            self.setBrightness(dc)
            utime.sleep(100)

        for i in range (0, 25):
            dc -= 10
            self.setBrightness(dc)
            utime.sleep(100)