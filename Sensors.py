"""
# Sensors.py
# A simple Sensor hierarchy for digital and analog sensors
# Added support for Ultrasonic Sensor on 9/11/23
# Added support for DHT11/DHT22 sensor on 6/14/24
# Author: Arijit Sengupta
"""

import utime
import math
from machine import Pin, ADC
from Log import *

class Sensor:
    """
    The top level sensor class - assume each sensor uses 
    at least one pin. We do not create the IO here because
    some sensors may use Analog inputs
    
    Parameters
    --------
    lowActive: set to True if the sensor gets low (or under threshold)
    when tripped. So an analog light sensor should normally get a high
    value but when covered, go low. So lowActive should be True
    
    A force sensor would be opposite - tripped when force gets high
    so lowActive should be False.

    Some of the digital sensors such as flame sensors, proximity sensors
    are lowActive, while others such as PIR sensors are highActive. Please
    check the sensor documentation for the correct value.
    """
    
    def __init__(self, name='Sensor', lowActive = True):
        self._lowActive = lowActive
        self._name = name

    def rawValue(self):
        Log.e(f"rawValue not implemented for {type(self).__name__} {self._name}")

    def tripped(self)->bool:
        Log.e(f"tripped not implemented for {type(self).__name__} {self._name}")
        return False

class DigitalSensor(Sensor):
    """
    A simple digital sensor (like the commonly available LC-393 that is a light sensor)
    has a digital output that flips based on a manual threshold control

    We are just going to poll this to keep things simple.

    Parameters
    --------
    pin: the pin number to which the sensor is connected
    name: the name of the sensor
    lowActive: set to True if the sensor gets low when tripped.
    """

    def __init__(self, pin, name='Digital Sensor', lowActive=True, handler=None):
        super().__init__(name, lowActive)
        self._pinio = Pin(pin, Pin.IN)
        self._handler = None
        self.setHandler(handler)

    def rawValue(self):
        return self._pinio.value()
    
    def tripped(self)->bool:
        v = self.rawValue()
        if (self._lowActive and v == 0) or (not self._lowActive and v == 1):
            Log.i(f"DigitalSensor {self._name}: sensor tripped")
            return True
        else:
            return False
        
    def setHandler(self, handler):
        """ 
	    set the handler to a new handler. Pass None to remove existing handler
	    """
        
        # if the old handler was active already, or if the new handler is None, remove the irq
        if self._handler is not None or handler is None:
            self._pinio.irq(handler = None)
    
        # Now set it to th enew handler
        self._handler = handler
        # Create the IRQ if the handler is not None
        if self._handler:
            self._pinio.irq(trigger = Pin.IRQ_FALLING | Pin.IRQ_RISING, handler = self._callback)
        
    def _callback(self, pin):
        """ The private interrupt handler - will call appropriate handlers """
        
        if self._handler is not None:
            if self.tripped():
                Log.i(f'Sensor {self._name} tripped')
                self._handler.sensorTripped(self._name)
            else:
                Log.i(f'Sensor {self._name} untripped')
                self._handler.sensorUntripped(self._name)

class TiltSensor(DigitalSensor):
    """
    A tilt sensor looks like a cap but has just a metal ball on two contacts
    when you tilt, the ball rolls off and the contact opens. That way its very
    much like a button which is always pressed.

    Connect the Tilt sensor across an IO pin and GND. When the sensor is tripped
    the pin will go high.
    """

    def __init__(self, pin, name='Tilt Sensor', handler=None):
        # Init - do not call the DigitalSensor init - just create the Pin.
        # Super-superclass init called to set name and lowactiv
        Sensor.__init__(self, name, lowActive=False)
        self._pinio = Pin(pin, Pin.IN, Pin.PULL_UP)
        self.setHandler(handler)

    def tripped(self):
        """
        A tilt sensor connector is typically always closed, so we
        initialize its pin using the internal pullup resistor. It is
        tripped when the value goes high, so there it is never lowActive
        """
        if self.rawValue() == 1:
            Log.i(f"TiltSensor {self._name}: sensor tripped")
            return True
        else:
            return False

class AnalogSensor(Sensor):
    """
    A simple analog sensor that returns a voltage or voltage ratio output
    that can be read in using an ADC. Pico reads in via a 16bit unsigned

    Since analog sensors do not have a handler, you need to poll
    the rawValue() method to get its value. The tripped method takes
    3 readings and takes the average. If the average is higher/lower
    than the threshold it will return true.
    
    Most analog sensors such as LDRs and thermistors will require
    a 10K pull-up resistor to the 3.3V rail. For better results,
    connect the sensor between the ADC pin and AGND (pin 33).
    Thermistor has a separate class - see below).
    
    Set the lowActive to True if rawValue gets lower when the sensor
    is tripped. You may need to set the threshold appropriately for
    your application.
    """
    
    def __init__(self, pin, name='Analog Sensor', lowActive=True, threshold = 30000):
        """ analog sensors will need to be sent a threshold value to detect trip """
        
        super().__init__(name, lowActive)
        self._pinio = ADC(pin)
        self._threshold = threshold

    def tripped(self)->bool:
        """ sensor is tripped if sensor value is higher or lower than threshold """
        
        # Take 3 measurements after 0.1 sec to get an average
        v1 = self.rawValue()
        utime.sleep(0.1)
        v2 = self.rawValue()
        utime.sleep(0.1)
        v3 = self.rawValue()
        
        v = (v1 + v2 + v3) / 3
        
        if (self._lowActive and v < self._threshold) or (not self._lowActive and v > self._threshold):
            Log.i(f"AnalogSensor {self._name}: sensor tripped")
            return True
        else:
            return False

    def rawValue(self):
        return self._pinio.read_u16()

class TemperatureSensor():
    """
    TemperatureSensor is essentially an abstract class/interface
    Implementing here as a basic class without using any special Python 3 notations
    """
    
    def temperature(self, unit='C'):
        """
        Return the temperature in the appropriate unit. Let's only support
        degrees Celcius (C) and Fahrenheit (F).
        """
        Log.e(f"temperature not implemented for {type(self).__name__} {self._name}")
        

    def _celciusToFahrenheit(self, t):
        return t*1.8 + 32


class Thermistor(AnalogSensor, TemperatureSensor):
    """
    Thermistor as a subclass of Analog Sensor - and it "implements" the
    TemperatureSensor interface. The rawValue is the resistance of the thermistor
    which is then converted to temperature using the Steinhart-Hart equation.
    """
    
    def __init__(self, pin, name='Thermistor', lowActive=False, threshold=30, Vd=3.3, Rp=10, Rt=10, beta=3950):
        """
        Create a new temp sensor - similar to regular analog sensor
        but now tripped will return true when temp is lower than threshold (lowActive=True)
        and higher than threshold (lowActive=False)
        
        Optional parameters:
            threshold is in degrees Celcius
            lowActive defaults to False so will trip at high temps
            Vd defaults to 3.3v - update if you use 5v rail for pullup
            Rp value of pullup resistor in K-ohms defaults to 10k
            Rt value of thermistor resistance (10k typical for 10k thermistors)
            beta - thermistor beta constant - update if different
        """
        self.vd = Vd
        self.rt = Rt
        self.rp = Rp
        self.beta = beta
        AnalogSensor.__init__(self, pin, name, lowActive, threshold)
        
    def rawValue(self):
        """
        Reture the temperature (approx) in celsius
        """

        adcvalue = AnalogSensor.rawValue(self)
        voltage = adcvalue / 65535.0 * self.vd
        r = self.rp * voltage / (self.vd -voltage)
        tempK = (1 / (1 / (273.15+25) + (math.log(r/self.rt)) / self.beta))
        tempC = tempK - 273.15
        return tempC
    
    def temperature(self, unit='C'):
        """ Return the measured temperature averaged from 3 readings """
        # Take 3 measurements after 0.1 sec to get an average
        v1 = self.rawValue()
        utime.sleep(0.1)
        v2 = self.rawValue()
        utime.sleep(0.1)
        v3 = self.rawValue()
        
        v = (v1 + v2 + v3) / 3
        
        if unit == 'C':
            return v
        elif unit == 'F':
            return self._celciusToFahrenheit(v)
        else:
            Log.e(f"Unknown unit {unit} for temperature")
            return None  
        
"""
Example usage of the Sensors
This part is not executed when the module is imported, but can be used for testing.
"""
if __name__ == "__main__":
    # Test the Sensors
    # A digital sensor connected to pin 11
    import time
    
    while True:
        digital_sensor = DigitalSensor(pin=11, name='Test Digital Sensor')
        print(f"Digital Sensor {digital_sensor._name} raw value: {digital_sensor.rawValue()}")
        print(f"Digital Sensor {digital_sensor._name} tripped: {digital_sensor.tripped()}")
        
        # An analog sensor connected to pin 27
        analog_sensor = AnalogSensor(pin=27, name='Test Analog Sensor', lowActive=True, threshold=30000)
        print(f"Analog Sensor {analog_sensor._name} raw value: {analog_sensor.rawValue()}")
        print(f"Analog Sensor {analog_sensor._name} tripped: {analog_sensor.tripped()}")

        time.sleep(1)

