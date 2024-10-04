# PicoLibrary

This is an ESP32 branch of the PicoLibrary - specific to only the generic Micropython firmware
on the ESP32-max (Acebott variant for ESP32). This should in theory work for most ESP32 variants
but likely not be tested for all potential hardware variants.

A collection of classes around the Raspberry Pi Pico Hardware interface to make it easy to 
work with Lights (LEDs, RGB LEDs), Sound (active and passive buzzers), Displays (Dot matrix 
with Max7219, 7 segment displays bare and with TM 1637, 160x LCD modules with I2C backpacks
and without I2C, as well as OLED/LCD displays with I2C).

Also includes simple support for buttons and a basic implementation of a state model for
creating simple state machines.

Currently supported hardware - (more to be added)

* Buttons - both pulled-down and pulled-up buttons supported
* Buzzers - both active and passive buzzers supported
* LEDs - Basic LEDs (on/off) and Dimmable LEDs (setting brightness level)
* Composite lights - TrafficLight (red, yellow, green), Pixel (R, G, B) and NeoPixel (PIO)
* Displays - 160x displays (both I2C as well has GPIO)
* Displays - OLED displays (SSD1306 driver)
* LCD Displays - Currently ST7789 only supported
* Displays - 7 segment displays (both sda/scl controlled as well as bit-banged using PIO)
* LED matrix displays - (MAX7219 driver)
* Sensors - both ditigal (0/1) as well as Analog (ADC 16 bit) sensors
* Specialized Sensors - Ultrasonic Sensor, Temp sensor, DHT11/DHT12 temp/hum sensor and Tilt sensor

Contact Dr. Sengupta if you need support for any other hardware
