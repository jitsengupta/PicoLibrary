"""
# JoystickHandle.py - Object-Oriented implementation of a Joystick Handle
# Note that this code is designed to work with an I2C-based joystick module, 
# and the register addresses and button mappings are based on a specific hardware design. 
# Adjustments may be necessary for different joystick modules.
#
# Also, unlike the standard Button class, this implementation does not include 
# any event handling for button presses. Instead, it provides methods to read the 
# current state of the buttons and the analog values of the joystick axes.
# 
# The calling routine must poll the button states and joystick positions at regular 
# intervals to detect changes.
# Created on: 2025-05-27
# Author: Arijit Sengupta
"""
import machine

JOYSTICK_I2C_ADDR         = 0x5A
JOYSTICK_BASE_REG         = 0x10
JOYSTICK_LEFT_X_REG       = 0x10
JOYSTICK_LEFT_Y_REG       = 0x11
JOYSTICK_RIGHT_X_REG      = 0x12
JOYSTICK_RIGHT_Y_REG      = 0x13

BUTTON_BASE               = 0x20

BUTTON_D_REG              = 0x24
BUTTON_B_REG              = 0x23
BUTTON_A_REG              = 0x22
BUTTON_C_REG              = 0x21
BUTTON_OK_REG             = 0x20

PRESS_DOWN                = 0
PRESS_UP                  = 1
PRESS_REPEAT              = 2
SINGLE_CLICK              = 3
DOUBLE_CLICK              = 4  
LONG_PRESS_START          = 5
LONG_PRESS_HOLD           = 6
number_of_event           = 7
NONE_PRESS                = 8

BUTTON_A = 0
BUTTON_B = 1
BUTTON_C = 2
BUTTON_D = 3
BUTTON_OK = 4

class JoystickHandle:
    def __init__(self, i2c, address=JOYSTICK_I2C_ADDR):
        self.i2c = i2c
        self.address = address
        self.left_x = 0
        self.left_y = 0

    def read_byte(self, reg):
        try:
            return self.i2c.readfrom_mem(self.address, reg, 1)[0]
        except Exception:
            return 0xFF

    def analog_read_x(self):
        self.left_x = self.read_byte(JOYSTICK_LEFT_X_REG)
        return self.left_x

    def analog_read_y(self):
        self.left_y = self.read_byte(JOYSTICK_LEFT_Y_REG)
        return self.left_y

    def get_button_status(self, button):
        if button == BUTTON_A:
            return self.read_byte(BUTTON_A_REG)
        elif button == BUTTON_B:
            return self.read_byte(BUTTON_B_REG)
        elif button == BUTTON_C:
            return self.read_byte(BUTTON_C_REG)
        elif button == BUTTON_D:
            return self.read_byte(BUTTON_D_REG)
        elif button == BUTTON_OK:
            return self.read_byte(BUTTON_OK_REG)
        else:
            return 0xFF

    def button_pressed(self, button):
        status = self.get_button_status(button)
        if status != NONE_PRESS and status != 0xFF:
            return True
        return False

    def button_released(self, button):
        status = self.get_button_status(button)
        if status == NONE_PRESS:
            return True
        return False
