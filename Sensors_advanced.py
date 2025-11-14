import dht
from collections import namedtuple
from Sensors import *

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
        self._echo = Pin(echo, Pin.IN)
        self._threshold = threshold

    def rawValue(self):
        """ Return the distance in cm """
        return self.distance()
    
    def distance(self)->float:
        """
        Measure and return the distance in centimeters.
        
        Returns:
            Distance in cm, or -1 if measurement fails
        """
        # Send a 5us pulse to trigger
        pulse_start = 0
        pulse_end = 0
        self._trigger.off()
        utime.sleep_us(2)
        self._trigger.on()
        utime.sleep_us(5)
        self._trigger.off()
        
        # Wait for echo to go high (with timeout)
        timeout = 30000  # 30ms timeout
        start = utime.ticks_us()
        while self._echo.value() == 0:
            if utime.ticks_diff(utime.ticks_us(), start) > timeout:
                return -1
            pulse_start = utime.ticks_us()
        
        # Wait for echo to go low (with timeout)
        start = utime.ticks_us()
        while self._echo.value() == 1:
            if utime.ticks_diff(utime.ticks_us(), start) > timeout:
                return -1
            pulse_end = utime.ticks_us()
        
        # Calculate distance
        pulse_duration = utime.ticks_diff(pulse_end, pulse_start)
        # Speed of sound is 343 m/s or 0.0343 cm/us
        # Distance = (utime * speed) / 2 (divide by 2 for round trip)
        distance_cm = (pulse_duration * 0.0343) / 2
        
        return round(distance_cm, 2)
    
    def tripped(self)->bool:
        """ sensor is tripped if distance is higher or lower than threshold """
        
        v = self.rawValue()
        if (self._lowActive and v < self._threshold) or (not self._lowActive and v > self._threshold):
            Log.i(f"UltrasonicSensor {self._name}: sensor tripped")
            return True
        else:
            return False

class GasSensor(Sensor):
    """
    An encapsulated version of the MQ-2 gas sensor. Although technically it is a 
    subclass of AnalogSensor, we subclass Sensor directly to avoid using ADC pins
    only. The Gas sensor provides continuous data, so subclassing Sensor makes sense.

    In addition, the MQ2 class is used to provide calibration and gas concentration
    calculations. The calibration is done using the clean air factor of the sensor.
    The gas concentration is calculated using the resistance ratio of the sensor
    and the gas curves provided in the MQ2 datasheet.
    """

    def __init__(self, pin, name='GasSensor', lowActive=False, threshold = 0.3, baseVoltage=3.3):
        """
        Initialize the Gas sensor with the given pin, name, lowActive and threshold.
        """
        super().__init__(name, lowActive)
        self._threshold = threshold
        try:
            from mq2 import MQ2
        except ImportError:
            Log.e("mq2 module not found. Please ensure mq2.py is available.")
            raise
        self._mq2 = MQ2(pin, baseVoltage=baseVoltage)
        self._mq2.calibrate()
    
    def rawValue(self):
        """
        Return the raw resistance ratio of the sensor.
        """
        return self._mq2.readRatio()
    
    def tripped(self) -> bool:
        """
        Sensor is tripped if resistance ratio is higher or lower than threshold
        """
        return self.rawValue() < self._threshold if self._lowActive else self.rawValue() >= self._threshold
    
    def getGasConcentrations(self):
        """
        Return a dictionary of gas concentrations in ppm for various gases.
        """
        concentrations = {
            'LPG': self._mq2.readLPG(), 
            'Smoke': self._mq2.readSmoke(), 
            'Hydrogen': self._mq2.readHydrogen(), 
            'Methane': self._mq2.readMethane()
            }
        return concentrations


DHTData = namedtuple('DHTData', ('temperature', 'humidity'))

# DHT11/DHT22 Sensor
class DHTSensor(Sensor, TemperatureSensor):
    def __init__(self, pin, name='DHT', lowActive=False, threshold=30, poll_delay=2000, sensor_type='DHT11'):
        """
        Create a new DHT sensor - can take
        either the form of a DHT11 or DHT22 based on the sensor_type parameter

        DHT11 is less accurate but cheaper, DHT22 is more accurate but more expensive

        Note that the DHT sensor is a digital sensor but it returns two values - temperature
        and humidity. So we subclass DigitalSensor but override the rawValue method

        Also, the DHT sensor is a bit slow, so we will not poll it as frequently as other sensors.
        To avoid to much polling, a default poll parameter is set to 2 seconds.

        The threshold is set to 30 deg C by default, but can be changed. This is used to determine
        if the sensor is tripped or not. Only the temperature is used for tripping.
        """
        
        Sensor.__init__(self, name, lowActive)
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
        try:
            from mpu6050 import MPU6050
            self._mpu = MPU6050(self._i2cid, sda, scl, ofs)
        except ImportError:
            Log.e("mpu6050 module not found. Please ensure mpu6050.py is available.")
            raise


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
