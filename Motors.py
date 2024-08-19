"""
Motors.py - a class containing code to drive different types
of motors.
# Author: Arijit Sengupta
"""

from machine import Pin, PWM
from time import sleep
from Log import *

class Motor:
    """
    A Motor superclass just to keep things together if we need to
    Currently simply stores the main pin (some motors take multiple pins)
    and a name for the motor.
    """
    
    def __init__(self, pin, name='Unnamed Motor'):
        self._pin = pin
        self._name = name


class Stepper(Motor):
    """
    A stepper motor is a powerful precision motor that can be controlled to 
    any angle (0-360). Usually requires a lot more power than what the
    Pico can deliver so will most likely need a separate power supply.
    Also requires a separate stepper motor driver since the current requirements
    are also higher than what the Pico can deliver.

    Different drivers exist - Wokwi supports the A4988 motor driver so 
    that is what I am implementing here.
    """

    def __init__(self, steppin=27, dirpin=26, *, name='Unnamed Stepper'):
        """
        For a stepper driven by A4988, we need two inputs - step and dir
        Technically there are 2 additional ones - reset and sleep but
        we are not using them here.
        """

        super().__init__(steppin, name)
        self._dirpin = dirpin
        self._step = Pin(steppin, Pin.OUT)
        self._dir = Pin(dirpin, Pin.OUT)
        self._curPos = 0 # Does a stepper go to 0 automatically?
        self._running = False

    def setAngle(self, angle):
        """
        set the stepper angle to a value in degrees. Technically can
        be any number. Note that higher than 360 will cause multiple
        rotations of the stepper.
        """
        
        Log.i(f"Setting angle of {self._name} to {angle}")
        self.rotate(angle - self._curPos)
        self._running = False

    def rotate(self, angle):
        """
        Rotate the servo by a certain angle.
        positive will be clockwise, negative will be anti-clockwise
        
        Again, technically can be any value - but higher than 360 will
        cause multiple rotations
        """

        Log.i(f"Rotating {self._name} by {angle} degrees") 
        numsteps = round(float(angle)/1.8)
        if numsteps < 0:
            self._dir.value(0)
            numsteps = numsteps * -1
        else:
            self._dir.value(1)
        
        for x in range (0,numsteps):
            self._step.value(1)
            sleep(0.01)
            self._step.value(0)
        
        self._curPos = self._curPos + angle
        self._running = False

    def spin(self, times=1, direction=1, speed=0):
        """
        Make the stepper spin at a certain speed. Note that this
        is a blocking call until the number of times is reached.

        speed is technically a delay between steps in seconds
        0 is full speed and 0.1 is 100 ms etc.

        times is the number of full rotations the stepper will make
        0 for times will keep the motor spinning forever.

        direction is 1 for clockwise, -1 for anti-clockwise

        We try to keep track of the current position, but after spinning,
        the position may be off.
        """

        if direction != 0:
            direction = 1
        self._running = True
        self._dir.value(direction)
        self._curPos = self._curPos % 360 # Let's forget higher spin positions
        n = 0
        
        Log.i(f"Spinning {self._name} {'clockwise' if direction == 1 else 'anti-clockwise'} {times} times at speed {speed} ")
        while self._running and (times == 0 or n < times):
            n = n + 1
            for x in range(0,200):
                self._step.value(1)
                sleep(0.001 + speed)
                self._step.value(0)
                self._curPos = self._curPos + 1.8 * (1 if direction else -1)
                if self._curPos >= 360 or self._curPos < 0:
                    self._curPos = self._curPos % 360
        Log.i(f"Stopped spinning {self._name}")

class Servo(Motor):
    def __init__(self, pin, name='Unnamed Servo'):
        super().__init__(pin, name)
        self._pwm = PWM(Pin(self._pin))
        self._pwm.freq(50)
        self._curPos = -1 # Initially position is unknown

    def setAngle(self, angle):
        """
        set the servo angle to something between 0 and 180
        Anything less than 0 will be treated as 0, anything
        more will be treated as 180

        Note for Wokwi:
        Wokwi has 0 at 1500 duty, 180 at 8000 duty
        So duty = int((8000-1500)*float(angle)/180.0)
        """

        if angle < 0:
            angle = 0
        if angle > 180:
            angle = 180
        
        Log.i(f"Setting angle of {self._name} to {angle}")
        duty = int((8000-1500)*float(angle)/180.0)+1500
        self._pwm.duty_u16(duty)
        self._curPos = angle

    def rotate(self, angle):
        """
        Rotate the servo by a certain angle.
        positive will be clockwise, negative will be anti-clockwise
        Rotating below 0 will set it to 0
        First rotation will set to 90, unless an angle is set before
        """

        Log.i(f"Rotating {self._name} by {angle} degrees")  
        if self._curPos < 0:
            self.setAngle(90)
        else:
            self.setAngle(self._curPos + angle)
        
# Rui Santos & Sara Santos - Random Nerd Tutorials
# Complete project details at https://RandomNerdTutorials.com/raspberry-pi-pico-dc-motor-micropython/

class DCMotor(Motor):
    def __init__(self, enable_pin = 0, name="DCMotor", forward_pin = 1, backward_pin=2, min_duty=15000, max_duty=65535):
        super().__init__(enable_pin, name)
        self.pin1 = Pin(forward_pin, Pin.OUT)
        self.pin2 = Pin(backward_pin, Pin.OUT)
        self.enable_pin = PWM(Pin(enable_pin), 1000)
        self.min_duty = min_duty
        self.max_duty = max_duty

    def forward(self, speed=100):
        """ Spin motor forward at a percent speed (max:100)"""
        
        Log.i(f"Moving {self._name} forward at speed {speed}")
        self.speed = speed
        self.enable_pin.duty_u16(self.duty_cycle(self.speed))
        self.pin1.value(1)
        self.pin2.value(0)

    def backwards(self, speed=100):
        """ Spin motor backwards at a percent speed (max:100) """
        
        Log.i(f"Moving {self._name} backwards at speed {speed}")
        self.speed = speed
        self.enable_pin.duty_u16(self.duty_cycle(self.speed))
        self.pin1.value(0)
        self.pin2.value(1)

    def stop(self):
        """ Stop spinning the motor """
        
        Log.i(f"Stopping {self._name}")
        self.enable_pin.duty_u16(0)
        self.pin1.value(0)
        self.pin2.value(0)

    def duty_cycle(self, speed):
        if speed <= 0 or speed > 100:
            duty_cycle = 0
        else:
            duty_cycle = int(self.min_duty + (self.max_duty - self.min_duty) * (speed / 100))
        return duty_cycle
    
if __name__ == '__main__':
    m = DCMotor(enable_pin=13, forward_pin=14,backward_pin=15)
    while True:
        # Start up slow to full speed
        for x in range(20,110,10):
            m.forward(x)
            sleep(0.5)
        
        # stop for a bit
        m.stop()
        sleep(1)
        # reverse slow to full speed
        for x in range(20,110,10):
            m.backwards(x)
            sleep(0.5)
        
        # stop for a bit
        m.stop()
        sleep(1)