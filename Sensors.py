"""
# Sensors.py
# A simple Sensor hierarchy for digital and analog sensors
# Added support for Ultrasonic Sensor on 9/11/23
# Added support for DHT11/DHT22 sensor on 6/14/24
# Author: Arijit Sengupta
"""

import utime
import math
import dht
from machine import Pin, ADC
from collections import namedtuple
from mpu6050 import *
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
    
    def __init__(self, pin, name='Digital Sensor', lowActive=True):
        super().__init__(name, lowActive)
        self._pinio = Pin(pin, Pin.IN)

    def rawValue(self):
        return self._pinio.value()
    
    def tripped(self)->bool:
        v = self.rawValue()
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

    Connect the Tilt sensor across an IO pin and GND. When the sensor is tripped
    the pin will go high.
    """
    
    def __init__(self, pin, name='Tilt Sensor'):
        # Init - do not call the super init - just create the Pin.
        super().__init__(pin, name)
        self._pinio = Pin(pin, Pin.IN, Pin.PULL_UP)
        
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

    We are just going to poll this to keep things simple
    """
    
    def __init__(self, pin, name='Analog Sensor', lowActive=True, threshold = 30000):
        """ analog sensors will need to be sent a threshold value to detect trip """
        
        super().__init__(name, lowActive)
        self._pinio = ADC(pin)
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
    
    def __init__(self, pin, name='Thermistor', lowActive=False, threshold=30):
        """
        Create a new temp sensor - similar to regular analog sensor
        but now tripped will return true when temp is lower than threshold (lowActive=True)
        and higher than threshold (lowActive=False)

        tempthreshold is in degrees Celcius
        """
        
        AnalogSensor.__init__(self, pin, name, lowActive, threshold)
        
    def rawValue(self):
        """
        Reture the temperature (approx) in celsius
        """
        
        adcvalue = AnalogSensor.rawValue(self)
        voltage = adcvalue / 65535.0 * 5
        Rt = 10 * voltage / (5 -voltage)
        tempK = (1 / (1 / (273.15+25) + (math.log(Rt/10)) / 3950))
        tempC = tempK - 273.15
        return tempC
    
    def temperature(self, unit='C'):
        if unit == 'C':
            return self.rawValue()
        elif unit == 'F':
            return self._celciusToFahrenheit(self.rawValue())
        else:
            Log.e(f"Unknown unit {unit} for temperature")
            return None  
        
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
        super().__init__(name, lowActive)
        self._trigger = Pin(trigger, Pin.OUT)
        self._echo = Pin(echo, Pin.IN, Pin.PULL_DOWN)
        self._threshold = threshold

    def rawValue(self):
        """ Return the distance in cm """
        return self.distance()
    
    def distance(self)->float:
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
        
        v = self.rawValue()
        if (self._lowActive and v < self._threshold) or (not self._lowActive and v > self._threshold):
            Log.i(f"UltrasonicSensor {self._name}: sensor tripped")
            return True
        else:
            return False

DHTData = namedtuple('DHTData', ('temperature', 'humidity'))

# DHT11/DHT22 Sensor
class DHTSensor(DigitalSensor, TemperatureSensor):
    def __init__(self, pin, name='DHT', lowActive=False, threshold=30, poll_delay=2000, sensor_type='DHT11'):
        """
        Create a new DHT sensor - similar to regular digital sensor but can take
        either the form of a DHT11 or DHT22 based on the sensor_type parameter

        DHT11 is less accurate but cheaper, DHT22 is more accurate but more expensive

        Note that the DHT sensor is a digital sensor but it returns two values - temperature
        and humidity. So we subclass DigitalSensor but override the rawValue method

        Also, the DHT sensor is a bit slow, so we will not poll it as frequently as other sensors.
        To avoid to much polling, a default poll parameter is set to 2 seconds.

        The threshold is set to 30 deg C by default, but can be changed. This is used to determine
        if the sensor is tripped or not. Only the temperature is used for tripping.
        """
        
        DigitalSensor.__init__(self,pin, name, lowActive)
        self._sensor_type = sensor_type
        self._sensor_class = dht.DHT11 if sensor_type == "DHT11" else dht.DHT22
        self._dht_sensor = self._sensor_class(Pin(pin))
        self._last_poll_time = 0
        self._poll_delay = poll_delay
        self._threshold = threshold

    def temperature(self, unit='C'):
        """
        Return the temperature of the sensor
        """
        
        (t, h) = self.rawValue()

        if unit == 'C':
            return t
        elif unit == 'F':
            return self._celciusToFahrenheit(t)
        else:    
            Log.e(f"Unknown unit {unit} for temperature")
            return None      

    def humidity(self):
        """
        Return the humidity of the sensor
        """
        
        (t, h) = self.rawValue()
        return h

    def rawValue(self):
        """
        Returns a tuple of temperature and humidity
        """
        
        if utime.ticks_ms() - self._last_poll_time > self._poll_delay:
            self._dht_sensor.measure()
            self._last_poll_time = utime.ticks_ms()
        return (DHTData(self._dht_sensor.temperature(), self._dht_sensor.humidity()))

    def tripped(self)->bool:
        """
        Sensor is tripped if temperature is higher or lower than threshold
        """
        
        if self._lowActive:
            tripped = self.temperature() < self._threshold
        else:
            tripped = self.temperature() >= self._threshold
        
        if tripped:
            Log.i(f"DHT Sensor {self._name}: sensor tripped")
            
        return tripped
        
MPUData = namedtuple('MPUData', ('acc_x', 'acc_y', 'acc_z', 'gyro_x', 'gyro_y', 'gyro_z', 'temperature'))

# MPU6050 Sensor
class MPU(Sensor, TemperatureSensor):
    """
    The MPU Sensor is a 6-axis sensor that returns acceleration and gyro data
    It is a digital sensor that uses I2C to communicate with the Pico. It is
    not an analog sensor, but it is a continuous sensor, so we subclass Sensor
    instead of DigitalSensor.

    I am using an MPU6050 driver that auto-calibrates the sensor when the class
    is initialized. Ensure that the sensor is placed on a flat surface when the
    class is initialized. If this cannot be guaranteed, call the calibrate method
    when possible to re-initialize the sensor. The calibration offsets are printed
    to the console when calibration is complete. Once calibration data is available,
    it may be passed as an argument to the constructor to avoid recalibration.

    The MPU6050 sensor is a 3.3V sensor, so ensure that the vcc pin of the sensor
    is connected to the 3.3V pin of the Pico. The sensor is connected to the I2C bus
    of the Pico, so ensure that the SDA and SCL pins are connected correctly.
    """

    def __init__(self, name='MPU6050', sda = 0, scl = 1, ofs=None, lowActive=False, threshold=30):
        """
        Parameters:
        name: the name of the sensor
        sda, scl = the SDA and SCL pins of the I2C bus
        ofs = the calibration offsets of the sensor (if available)
        """

        Sensor.__init__(self, name, lowActive)
        self._i2cid = -1 # lets set an invalid value to start with
        self._sda = sda
        self._scl = scl
        self._threshold = threshold

        if (sda == 0 and scl == 1) or (sda == 4 and scl == 5) or (sda == 8 and scl == 9) or (sda == 12 and scl == 13) or (sda == 16 and scl == 17) or (sda == 20 and scl == 21):    
            self._i2cid = 0
        elif (sda == 2 and scl == 3) or (sda == 6 and scl == 7) or (sda == 10 and scl == 11) or (sda == 14 and scl == 15) or (sda == 18 and scl == 19) or (sda == 26 and scl == 27):
            self._i2cid = 1
        else:
            raise ValueError('Invalid SDA/SCL pins')

        self._mpu = MPU6050(self._i2cid, sda, scl, ofs)

    def calibrate(self):
        """
        Calibrate the sensor by placing it on a flat surface
        re-initialize the sensor which will auto-calibrate
        """

        self._mpu = MPU6050(self._i2cid, self._sda, self._scl)

    def temperature(self, unit='C'):
        """
        Return the temperature of the sensor
        """

        if unit == 'C':
            return self._mpu.celsius
        elif unit == 'F':
            return self._mpu.fahrenheit
        else:
            Log.e(f"Unknown unit {unit} for temperature")
            return None
        
    def rawValue(self):
        """
        Return the raw data from the sensor
        which is in the form of a named tuple containing both acceleration and gyro data
        """
        d = self._mpu.data
        return MPUData(d[0], d[1], d[2], d[3], d[4], d[5], self._mpu.celsius)
    
    def angles(self):
        """
        Return the angles of the sensor in the form of a named tuple containing the pitch and roll angles
        """

        return self._mpu.angles
    
    def tripped(self)->bool:
        """
        Sensor is tripped if temperature is higher or lower than threshold
        """

        if self._lowActive:
            tripped = self.temperature() < self._threshold
        else:
            tripped = self.temperature() >= self._threshold
        
        if tripped:
            Log.i(f"DHT Sensor {self._name}: sensor tripped")
            
        return tripped

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

