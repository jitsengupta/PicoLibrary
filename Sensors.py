"""
# Sensors.py
# A simple Sensor hierarchy for digital and analog sensors
# Added support for Ultrasonic Sensor on 9/11/23
# Added support for DHT11/DHT22 sensor on 6/14/24
# Author: Arijit Sengupta
"""

from machine import Pin, ADC
import utime
import math
import dht
from Log import *

class Sensor:
    """
    The top level sensor class - assume each sensor uses 
    at least one pin. We do not create the IO here because
    some sensors may use Analog inputs
    
    Parameters
    --------
    pin: pin number where the sensor is connected
    lowActive: set to True if the sensor gets low (or under threshold)
    when tripped. So an analog light sensor should normally get a high
    value but when covered, go low. So lowActive should be True
    
    A force sensor would be opposite - tripped when force gets high
    so lowActive should be False
    """
    
    def __init__(self, pin, name='Sensor', lowActive = True):
        self._pin = pin
        self._lowActive = lowActive
        self._name = name
        
    def tripped(self)->bool:
        Log.e(f"tripped not implemented for {type(self).__name__} {self._name}")
        return False

class DigitalSensor(Sensor):
    """
    A simple digital sensor (like the commonly available LC-393 that is a light sensor)
    has a digital output that flips based on a manual threshold control

    We are just going to poll this to keep things simple
    """
    
    def __init__(self, pin, name='Digital Sensor', lowActive=True):
        super().__init__(pin, name, lowActive)
        self._pinio = Pin(self._pin, Pin.IN)

    def tripped(self)->bool:
        v = self._pinio.value()
        if (self._lowActive and v == 0) or (not self._lowActive and v == 1):
            Log.i(f"DigitalSensor {self._name}: sensor tripped")
            return True
        else:
            return False
        
class TiltSensor(DigitalSensor):
    """
    A tilt sensor looks like a cap but has just a metal ball on two contacts
    when you tilt, the ball rolls off and the contact opens. That way its very
    much like a button which is always pressed.
    """
    
    def __init__(self, pin, name='Tilt Sensor'):
        # Init - do not call the super init - just create the Pin.
        super().__init__(pin, name)
        self._pinio = Pin(pin, Pin.IN, Pin.PULL_UP)
        
    def tripped(self):
        if self._pinio.value() == 1:
            Log.i(f"TiltSensor {self._name}: sensor tripped")
            return True
        else:
            return False

class AnalogSensor(Sensor):
    """
    A simple analog sensor that returns a voltage or voltage ratio output
    that can be read in using an ADC. Pico reads in via a 16bit unsigned

    We are just going to poll this to keep things simple
    """
    
    def __init__(self, pin, name='Analog Sensor', lowActive=True, threshold = 30000):
        """ analog sensors will need to be sent a threshold value to detect trip """
        
        super().__init__(pin, name, lowActive)
        self._pinio = ADC(self._pin)
        self._threshold = threshold

    def tripped(self)->bool:
        """ sensor is tripped if sensor value is higher or lower than threshold """
        
        v = self.rawValue()
        if (self._lowActive and v < self._threshold) or (not self._lowActive and v > self._threshold):
            Log.i(f"AnalogSensor {self._name}: sensor tripped")
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
    
    def __init__(self, pin, name='Temp Sensor', lowActive=False, threshold=60):
        """
        Create a new temp sensor - similar to regular analog sensor
        but now tripped will return true when temp is lower than threshold (lowActive=True)
        and higher than threshold (lowActive=False)
        """
        
        super().__init__(pin, name, lowActive, threshold)
        
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
    
    Continuing to use the lowActive and threshold like AnalogSensor however.

    init by sending trigger, echo and optionally lowActive and threshold
    parameters. Threshold defaults to 10cm, and lowActive defaults to true
    so when distance is < 10cm, it will return true for tripped.
    """

    def __init__(self, *, trigger=0, echo=1, name='Ultrasonic', lowActive = True, threshold=10.0):
        super().__init__(trigger, name, lowActive)
        self._trigger = Pin(trigger, Pin.OUT)
        self._echo = Pin(echo, Pin.IN)
        self._threshold = threshold

    def getDistance(self)->float:
        """ Get the distance of obstacle from the sensor in cm """
        
        self._trigger.off()
        utime.sleep_us(2)
        self._trigger.on()
        utime.sleep_us(5)
        self._trigger.off()
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
        if (self._lowActive and v < self._threshold) or (not self._lowActive and v > self._threshold):
            Log.i(f"UltrasonicSensor {self._name}: sensor tripped")
            return True
        else:
            return False

# DHT11/DHT22 Sensor
class DHTSensor(DigitalSensor):
    def __init__(self, pin, name='DHT', lowActive=False, threshold=60, poll_delay=2000, sensor_type='DHT11'):
        """
        Create a new DHT sensor - similar to regular digital sensor but can take
        either the form of a DHT11 or DHT22 based on the sensor_type parameter

        DHT11 is less accurate but cheaper, DHT22 is more accurate but more expensive

        Note that the DHT sensor is a digital sensor but it returns two values - temperature
        and humidity. So we subclass DigitalSensor but override the rawValue method

        Also, the DHT sensor is a bit slow, so we will not poll it as frequently as other sensors.
        To avoid to much polling, a default poll parameter is set to 2 seconds.

        The threshold is set to 60F by default, but can be changed. This is used to determine
        if the sensor is tripped or not. Only the temperature is used for tripping.
        """
        
        super().__init__(pin, name, lowActive)
        self._sensor_type = sensor_type
        self._sensor_class = dht.DHT11 if sensor_type == "DHT11" else dht.DHT22
        self._dht_sensor = self._sensor_class(Pin(self._pin))
        self._last_poll_time = 0
        self._poll_delay = poll_delay
        self._threshold = threshold

    def getTemperature(self):
        """
        Return the temperature of the sensor
        """
        
        if utime.ticks_ms() - self._last_poll_time > self._poll_delay:
            self._dht_sensor.measure()
        self._last_poll_time = utime.ticks_ms()
        return self._dht_sensor.temperature()

    def getHumidity(self):
        """
        Return the humidity of the sensor
        """
        
        if utime.ticks_ms() - self._last_poll_time > self._poll_delay:
            self._dht_sensor.measure()
        self._last_poll_time = utime.ticks_ms()
        return self._dht_sensor.humidity()

    def rawValue(self):
        """
        Returns a tuple of temperature and humidity
        """
        
        if utime.ticks_ms() - self._last_poll_time > self._poll_delay:
            self._dht_sensor.measure()
        self._last_poll_time = utime.ticks_ms()
        return (self._dht_sensor.temperature(), self._dht_sensor.humidity())

    def tripped(self)->bool:
        """
        Sensor is tripped if temperature is higher or lower than threshold
        """
        
        if self._lowActive:
            return self.getTemperature() < self._threshold
        else:
            return self.getTemperature() >= self._threshold
