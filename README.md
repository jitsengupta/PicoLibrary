# PicoLibrary

This branch includes classes required for the Acebott smart car robot.
Removed the displays and other classes that we don't need and added IR,
Vehicle, etc. as needed by the robot.

A collection of classes around the Raspberry Pi Pico Hardware interface to make it easy to 
work with Lights (LEDs, RGB LEDs), Sound (active and passive buzzers), Displays (Dot matrix 
with Max7219, 7 segment displays bare and with TM 1637, 160x LCD modules with I2C backpacks
and without I2C, as well as OLED/LCD displays with I2C).

Also includes simple support for buttons and a basic implementation of a state model for
creating simple state machines.

Currently supported hardware - (more to be added)

* Buzzers - both active and passive buzzers supported
* LEDs - Basic LEDs (on/off) and Dimmable LEDs (setting brightness level)
* Sensors - both ditigal (0/1) as well as Analog (ADC 16 bit) sensors
* Specialized Sensors - Ultrasonic Sensor, Temp sensor, DHT11/DHT12 temp/hum sensor and Tilt sensor

Contact Dr. Sengupta if you need support for any other hardware
