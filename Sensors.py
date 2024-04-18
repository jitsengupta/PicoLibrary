"""
# Sensors.py
# A simple Sensor hierarchy for digital and analog sensors
# Added support for Ultrasonic Sensor on 9/11/23
# Author: Arijit Sengupta
"""

from machine import Pin, ADC
import utime
import math
from Log import *

class Sensor:
    """
    The top level sensor class - assume each sensor uses 
    at least one pin. We do not create the IO here because
    some sensors may use Analog inputs
    
    Parameters
    --------
    pin: pin number where the sensor is connected
    lowactive: set to True if the sensor gets low (or under threshold)
    when tripped. So an analog light sensor should normally get a high
    value but when covered, go low. So lowactive should be True
    
    A force sensor would be opposite - tripped when force gets high
    so lowactive should be False
    """
    
    def __init__(self, pin, lowactive = True):
        self._pin = pin
        self._lowactive = lowactive
        
    def tripped(self)->bool:
        Log.e(f"tripped not implemented for {type(self).__name__}")
        return False

class DigitalSensor(Sensor):
    """
    A simple digital sensor (like the commonly available LC-393 that is a light sensor)
    has a digital output that flips based on a manual threshold control

    We are just going to poll this to keep things simple
    """
    
    def __init__(self, pin, lowactive=True):
        super().__init__(pin, lowactive)
        self._pinio = Pin(self._pin, Pin.IN)

    def tripped(self)->bool:
        v = self._pinio.value()
        if (self._lowactive and v == 0) or (not self._lowactive and v == 1):
            Log.i("DigitalLightSensor: sensor tripped")
            return True
        else:
            return False
        
class TiltSensor(DigitalSensor):
    """
    A tilt sensor looks like a cap but has just a metal ball on two contacts
    when you tilt, the ball rolls off and the contact opens. That way its very
    much like a button which is always pressed.
    """
    
    def __init__(self, pin):
        # Init - do not call the super init - just create the Pin.

        self._pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        
    def tripped(self):
        return self._pin.value() == 1

class AnalogSensor(Sensor):
    """
    A simple analog sensor that returns a voltage or voltage ratio output
    that can be read in using an ADC. Pico reads in via a 16bit unsigned

    We are just going to poll this to keep things simple
    """
    
    def __init__(self, pin, lowactive=True, threshold = 30000):
        """ analog sensors will need to be sent a threshold value to detect trip """
        
        super().__init__(pin, lowactive)
        self._pinio = ADC(self._pin)
        self._threshold = threshold

    def tripped(self)->bool:
        """ sensor is tripped if sensor value is higher or lower than threshold """
        
        v = self.rawValue()
        if (self._lowactive and v < self._threshold) or (not self._lowactive and v > self._threshold):
            Log.i("AnalogSensor: sensor tripped")
            return True
        else:
            return False

    def rawValue(self):
        return self._pinio.read_u16()

class TempSensor(AnalogSensor):
    """
    Temperature sensor as a subclass of Analog Sensor - Temp sensor is a bit more
    defined since it technically returns a temperature. Note that thermistors are
    not totally accurate, but the teperature fluctuations - increases and decreases
    are what matters.
    """
    
    def __init__(self, pin, lowactive=False, threshold=60):
        """
        Create a new temp sensor - similar to regular analog sensor
        but now tripped will return true when temp is lower than threshold (lowactive=True)
        and higher than threshold (lowactive=False)
        """
        
        super().__init__(pin, lowactive, threshold)
        
    def rawValue(self):
        """
        Reture the temperature (approx) in fahrenheit
        """
        
        adcvalue = super().rawValue()
        voltage = adcvalue / 65535.0 * 5
        Rt = 10 * voltage / (5 -voltage)
        tempK = (1 / (1 / (273.15+25) + (math.log(Rt/10)) / 3950))
        tempF = int((tempK - 273.15) * 1.8) + 32
        return tempF
        
class UltrasonicSensor(Sensor):
    """
    A simple implementation of an ultrasonic sensor with digital IO
    pins for trigger and echo.
    
    While technically Ultrasonic sensor is not an analog sensor since it
    uses digital pins, it does have continuous data, so subclassing
    AnalogSensor makes more sense. But given AnalogSensor should only be
    used in ADC pins, it is better to subclass the Sensor superclass.
    
    Continuing to use the lowactive and threshold like AnalogSensor however.

    init by sending trigger, echo and optionally lowactive and threshold
    parameters. Threshold defaults to 10cm, and lowactive defaults to true
    so when distance is < 10cm, it will return true for tripped.
    """

    def __init__(self, trigger, echo, *, lowactive = True, threshold=10.0):
        super().__init__(trigger, lowactive)
        self._trigger = Pin(trigger, Pin.OUT)
        self._echo = Pin(echo, Pin.IN)
        self._threshold = threshold

    def getDistance(self)->float:
        """ Get the distance of obstacle from the sensor in cm """
        
        self._trigger.low()
        utime.sleep_us(2)
        self._trigger.high()
        utime.sleep_us(5)
        self._trigger.low()
        while self._echo.value() == 0:
            signaloff = utime.ticks_us()
        while self._echo.value() == 1:
            signalon = utime.ticks_us()
        timepassed = signalon - signaloff
        distance = (timepassed * 0.0343) / 2
        return distance

    def tripped(self)->bool:
        """ sensor is tripped if distance is higher or lower than threshold """
        
        v = self.getDistance()
        if (self._lowactive and v < self._threshold) or (not self._lowactive and v > self._threshold):
            Log.i("UltrasonicSensor: sensor tripped")
            return True
        else:
            return False
