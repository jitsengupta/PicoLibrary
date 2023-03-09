from machine import Pin, ADC

"""
A simple Sensor hierarchy
"""

"""
The top level sensor class - assume each sensor uses 
at least one pin. We do not create the IO here because
some sensors may use Analog inputs
"""
class Sensor:
    def __init__(self, pin):
        self._pin = pin

"""
A simple digital light sensor (like the commonly available LC-393)
has a digital output that flips based on a manual threshold control

We are just going to poll this to keep things simple
"""
class DigitalLightSensor(Sensor):
    def __init__(self, pin):
        super().__init__(pin)
        self._pinio = Pin(self._pin, Pin.IN)

    def covered(self)->bool:
        if self._pinio.value() == 1:
            print("DigitalLightSensor: sensor detected cover")
            return True
        else:
            return False

class AnalogLightSensor(Sensor):
    def __init__(self, pin, threshold = 30000):
        super().__init__(pin)
        self._pinio = ADC(self._pin)
        self._threshold = threshold

    def covered(self)->bool:
        if self._pinio.read_u16() > self._threshold:
            print("AnalogLightSensor: sensor detected cover")
            return True
        else:
            return False

    def rawValue(self):
        return self._pinio.read_u16()
