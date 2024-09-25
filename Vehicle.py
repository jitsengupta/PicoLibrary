from machine import Pin, PWM

# Pin Definitions (Adjust according to your hardware)
PWM1_PIN = 19
PWM2_PIN = 23
SHCP_PIN = 18
EN_PIN = 16
DATA_PIN = 5
STCP_PIN = 17
PWM_FREQ = 1000
MINSPEED = 500 # Minimum speed for the motors (seems to stall below this)

# Movement Directions (Adapt based on your motor driver)
FORWARD = 163
BACKWARD = 92
MOVE_LEFT = 106
MOVE_RIGHT = 149
TOP_LEFT = 34
BOTTOM_LEFT = 72
TOP_RIGHT = 129
BOTTOM_RIGHT = 20
STOP = 0
CONTRAROTATE = 83
CLOCKWISE = 172

# Model selections
MODEL1 = 25
MODEL2 = 26
MODEL3 = 27
MODEL4 = 28

# Servo directions (assuming these control servos)
MOTOR_LEFT = 230 
MOTOR_RIGHT = 231

# Motor directions (assuming individual motor control)
M1_FORWARD = 128
M1_BACKWARD = 64
M2_FORWARD = 32
M2_BACKWARD = 16
M3_FORWARD = 2
M3_BACKWARD = 4
M4_FORWARD = 1
M4_BACKWARD = 8 

class Vehicle:
    def __init__(self):
        # Initialize PWM objects for motor speed control
        self.pwm1 = PWM(Pin(PWM1_PIN))
        self.pwm2 = PWM(Pin(PWM2_PIN))
        self.pwm1.freq(PWM_FREQ)  # Set PWM frequency (adjust as needed)
        self.pwm2.freq(PWM_FREQ)

        # Initialize control pins
        self.shcp_pin = Pin(SHCP_PIN, Pin.OUT)
        self.en_pin = Pin(EN_PIN, Pin.OUT)
        self.data_pin = Pin(DATA_PIN, Pin.OUT)
        self.stcp_pin = Pin(STCP_PIN, Pin.OUT)

        self.en_pin.value(0)  # Enable motor driver (adjust logic if needed)
        self.cuspeed = 0

    def forward(self, speed=-1):
        """Moves the vehicle forward. Speed is optional. If no speed specified it will use the previous speed."""
        self.move(FORWARD, speed)

    def backward(self, speed=-1):
        """Moves the vehicle backward. Speed is optional. If no speed specified it will use the previous speed."""
        self.move(BACKWARD, speed)

    def left(self, speed=-1):
        """Moves the vehicle left. Speed is optional. If no speed specified it will use the previous speed."""
        self.move(MOVE_LEFT, speed)

    def right(self, speed=-1):
        """Moves the vehicle right. Speed is optional. If no speed specified it will use the previous speed."""
        self.move(MOVE_RIGHT, speed)

    def rotate_left(self, speed=-1):
        """Rotates the vehicle left. Speed is optional. If no speed specified it will use the previous speed."""
        self.move(CONTRAROTATE, speed)

    def rotate_right(self, speed=-1):
        """Rotates the vehicle right. Speed is optional. If no speed specified it will use the previous speed."""
        self.move(CLOCKWISE, speed)
        
    def stop(self):
        """Stops the vehicle."""
        self.cuspeed = 0
        self.move(STOP, 0)

    def set_speed(self, speed=MINSPEED):
        """Sets the motor speed."""
        self.cuspeed = speed

    def move(self, direction=FORWARD, speed=-1):
        """
        Controls the vehicle's movement.

        Args:
            direction (int): Desired movement direction (use constants like FORWARD, BACKWARD, etc.).
            speed (int): Motor speed from 0 to 1023.

            A negative speed value will set the speed to the last value set by set_speed().
        """

        # Use the last set speed if speed is negative
        if speed < 0 or (speed > 0 and speed < MINSPEED):
            # Set the speed to a minimum value if it's below the minimum
            self.set_speed(MINSPEED)
        else:
            self.cuspeed = speed

        # Set motor speeds (assuming both motors use the same speed)
        self.pwm1.duty(speed) 
        self.pwm2.duty(speed)

        # Send direction bits to shift register
        self.stcp_pin.value(0)  # Pull latch pin low
        self.shift_out(direction) 
        self.stcp_pin.value(1)  # Latch data

    def shift_out(self, value):
        """Shifts out a byte of data to the shift register."""
        for i in range(8):
            self.data_pin.value((value >> (7 - i)) & 0x01)
            self.shcp_pin.value(1)
            self.shcp_pin.value(0)