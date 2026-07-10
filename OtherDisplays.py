"""
OtherDisplays.py - This file contains the implementation of other displays
than the basic 16x2 LCD display that comes with the basic kits. This will
allow us to reduce the number of imports in the main code and also allow
us to keep the number of files in the project to a minimum.

# Currently supports 4-digit seven-segment displays - both with a tm1637 backpack
# and without (using PIO) - PIO 7 seg only supports number
# Also supports MAX7219 Dot Matrix displays
# Now also supports MAX7219 backpack for seven segment displays
"""

from Displays import *
from Log import *
import rp2
from rp2 import PIO

# Alphanumeric character mapping for 7-segment display
# A=1, B=2, C=4, D=8, E=16, F=32, G=64, DP=128
_CHARS = {
    '0': 0x3F, '1': 0x06, '2': 0x5B, '3': 0x4F,
    '4': 0x66, '5': 0x6D, '6': 0x7D, '7': 0x07,
    '8': 0x7F, '9': 0x6F, 'A': 0x77, 'a': 0x77,
    'B': 0x7C, 'b': 0x7C, 'C': 0x39, 'c': 0x58,
    'D': 0x5E, 'd': 0x5E, 'E': 0x79, 'e': 0x79,
    'F': 0x71, 'f': 0x71, 'G': 0x3D, 'g': 0x6F,
    'H': 0x76, 'h': 0x74, 'I': 0x06, 'i': 0x04,
    'J': 0x0E, 'j': 0x0E, 'K': 0x76, 'k': 0x70,
    'L': 0x38, 'l': 0x38, 'M': 0x15, 'm': 0x15,
    'N': 0x54, 'n': 0x54, 'O': 0x3F, 'o': 0x5C,
    'P': 0x73, 'p': 0x73, 'Q': 0x67, 'q': 0x67,
    'R': 0x50, 'r': 0x50, 'S': 0x6D, 's': 0x6D,
    'T': 0x78, 't': 0x78, 'U': 0x3E, 'u': 0x1C,
    'V': 0x3E, 'v': 0x1C, 'W': 0x2A, 'w': 0x2A,
    'X': 0x76, 'x': 0x76, 'Y': 0x6E, 'y': 0x6E,
    'Z': 0x5B, 'z': 0x5B, ' ': 0x00, '-': 0x40,
    '_': 0x08, '=': 0x48, '.': 0x80,
    "'": 0x02,    # Single quote
    '"': 0x22,    # Double quote
    ',': 0x04,    # Comma
    '/': 0x24,    # Slash
    '\\': 0x12,   # Backslash
    '[': 0x39,    # Left bracket
    ']': 0x0F,    # Right bracket
    '(': 0x39,    # Left parenthesis
    ')': 0x0F,    # Right parenthesis
    '?': 0x53,    # Question mark
    '°': 0x63,    # Degree symbol
    ':': 0x48,    # Colon (mapped to '=')
    ';': 0x48     # Semicolon (mapped to '=')
}

class SevenSegmentDisplay(Display):
    """
    Seven Segment Display class - implements a multi-digit seven segment display.
    Supports both the TM1637 and MAX7219 backpacks.

    Parameters:
    -----------
    clk : int
        The clock pin number. For tm1637 this is the CLK pin. For max7219 this is sck.
    dio : int
        The data pin number. For tm1637 this is the DIO pin. For max7219 this is mosi.
    driver : str, optional (keyword-only)
        The driver to use: 'tm1637' (default) or 'max7219'.
    cs : int, optional (keyword-only)
        The Chip Select (CS) pin number (only used for max7219, default 18).
    spi_id : int, optional (keyword-only)
        The SPI interface ID (0 or 1, only used for max7219, default 0).
    num_digits : int, optional (keyword-only)
        The number of digits on the display (default 4).

    Examples:
    ---------
    1. Using TM1637 (4-digit display):
       # Connect CLK to pin 16, DIO to pin 17
       display = SevenSegmentDisplay(clk=16, dio=17, driver='tm1637')

    2. Using MAX7219 (8-digit display):
       # Connect sck to pin 18, mosi to pin 19, cs to pin 17
       display = SevenSegmentDisplay(clk=18, dio=19, driver='max7219', cs=17, num_digits=8)
    """

    def __init__(self, clk=16, dio=17, *, driver='tm1637', cs=18, spi_id=0, num_digits=4):
        from machine import Pin
        self._driver = driver
        self._num_digits = num_digits

        if driver == 'tm1637':
            import tm1637
            self._tm = tm1637.TM1637(clk=Pin(clk), dio=Pin(dio))
        elif driver == 'max7219':
            from machine import SPI
            self._spi = SPI(spi_id, baudrate=10000000, polarity=0, phase=0, sck=Pin(clk), mosi=Pin(dio))
            self._cs = Pin(cs, Pin.OUT)
            # Initialize MAX7219 registers
            self._write_max7219(0x0C, 1) # shutdown=1: normal operation
            self._write_max7219(0x0F, 0) # display test off
            self._write_max7219(0x0B, num_digits - 1) # scan limit (0 to num_digits-1)
            self._write_max7219(0x09, 0) # decode mode: no decode
            self._write_max7219(0x0A, 7) # intensity: medium brightness
            self.reset()
        else:
            raise ValueError(f"Unsupported driver: {driver}")

    def _write_max7219(self, reg, val):
        self._cs.value(0)
        self._spi.write(bytearray([reg, val]))
        self._cs.value(1)

    def reset(self):
        """ clear the display screen  """
        if self._driver == 'tm1637':
            self._tm.write([0] * self._num_digits)
        elif self._driver == 'max7219':
            for i in range(1, self._num_digits + 1):
                self._write_max7219(i, 0x00)

    def showNumber(self, number):
        """ show a single number """
        if self._driver == 'tm1637':
            self._tm.number(number)
        elif self._driver == 'max7219':
            min_val = -10**(self._num_digits - 1) + 1
            max_val = 10**self._num_digits - 1
            number = max(min_val, min(number, max_val))
            num_str = '{0: >{width}d}'.format(number, width=self._num_digits)
            self.showText(num_str)

    def showNumbers(self, num1, num2, colon=True):
        """  Show two numbers optionally separated by a colon by default, the colon is shown """
        if self._driver == 'tm1637':
            self._tm.numbers(num1, num2, colon)
        elif self._driver == 'max7219':
            half = self._num_digits // 2
            s1 = '{0:0>{width}d}'.format(num1, width=half)
            s2 = '{0:0>{width}d}'.format(num2, width=self._num_digits - half)
            self.showText(s1 + s2, colon=colon)

    def showText(self, text, colon=False, colonpos=1):
        """
        Show a string - only first num_digits characters will be shown
        for anything bigger than num_digits characters.
        """
        if self._driver == 'tm1637':
            self._tm.show(text, colon)
        elif self._driver == 'max7219':
            text = str(text)
            data = []
            i = 0
            while i < len(text) and len(data) < self._num_digits:
                char = text[i]
                val = _CHARS.get(char, 0x00)
                if i + 1 < len(text) and text[i+1] == '.':
                    val |= 0x80
                    i += 1
                data.append(val)
                i += 1
            if colon and len(data) > colonpos:
                data[colonpos] |= 0x80
            while len(data) < self._num_digits:
                data.append(0x00)
            
            # Map segments to MAX7219 bit layout
            for idx, val in enumerate(data):
                max_val = 0
                if val & 0x80: max_val |= 0x80 # DP
                if val & 0x01: max_val |= 0x40 # A
                if val & 0x02: max_val |= 0x20 # B
                if val & 0x04: max_val |= 0x10 # C
                if val & 0x08: max_val |= 0x08 # D
                if val & 0x10: max_val |= 0x04 # E
                if val & 0x20: max_val |= 0x02 # F
                if val & 0x40: max_val |= 0x01 # G
                self._write_max7219(idx + 1, max_val)

    def scroll(self, text, speed=250):
        """
        Scroll a longer text - note that this will use a sleep
        call to pause between movements.
        """
        if self._driver == 'tm1637':
            self._tm.scroll(text, speed)
        elif self._driver == 'max7219':
            import time
            padded_text = text + " " * self._num_digits
            for i in range(len(padded_text) - self._num_digits + 1):
                self.showText(padded_text[i:i + self._num_digits])
                time.sleep_ms(speed)

    def setBrightness(self, val):
        """ Set the display brightness. tm1637 uses 0-7, max7219 uses 0-15. """
        if self._driver == 'tm1637':
            self._tm.brightness(val)
        elif self._driver == 'max7219':
            if not 0 <= val <= 15:
                raise ValueError("Brightness/Intensity must be between 0 and 15")
            self._write_max7219(0x0A, val)

    def brightness(self, val):
        """ Alias for setBrightness to maintain compatibility. """
        self.setBrightness(val)

class DotMatrixDisplay(Display):
    """
    An implementation of the MAX7219 Dot Matrix display
    Fairly simplistic implementation - tested only with simulator so far 
    """

    def __init__(self, sck=18, mosi=19, cs=17):
        self._spi = SPI(0, baudrate=10000000, polarity=1, phase=0, sck=Pin(sck), mosi=Pin(mosi))
        # Create matrix display instant, which has four MAX7219 devices.
        import max7219
        self._dot = max7219.Matrix8x8(self._spi, Pin(cs, Pin.OUT), 4)
        self._dot.brightness(10)
        self.reset()

    def reset(self):
        #Clear the display.
        self._dot.fill(0)
        self._dot.show()

    def showNumber(self, number, row = 0, col = 0):
        self._dot.text(str(number), row, col, 1)
        self._dot.show()

    def showText(self, text, row = 0, col = 0):
        self._dot.text(text, row, col, 1)
        self._dot.show()

    def scroll(self, text, speed=50):
        #Get the message length
        length = len(text)
        column = (length * 8)
        for x in range(32, -column, -1):     
            #Clear the display
            self._dot.fill(0)
            # Write the scrolling text in to frame buffer
            self._dot.text(text,x,0,1)
            #Show the display
            self._dot.show()
      
            #Set the Scrolling speed. Here it is 50mS.
            time.sleep(speed/1000)

class MorseDisplay(Display):
    """
    This is a fun class - implement a Morse code display
    This can play the Morse code via a Buzzer, or show
    the code via a light, or even display it in another
    display.
    
    We need to make sure the other display is not another
    MorseDisplay though
    """
        
    def __init__(self, buz=None, light=None, otherDisplay=None):
        self._buz = buz
        self._light = light
        if isinstance(otherDisplay, OLEDDisplay) or isinstance(otherDisplay, LCDDisplay):
            self._dp = otherDisplay
        else:
            self._dp = None
            Log.e(f"Sorry, {type(otherDisplay).__name__} isn't supported")
        self._morsedict = {'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.', 'G': '--.', 'H': '....',
            'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---', 'P': '.--.',
            'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
            'Y': '-.--', 'Z': '--..', '0': '-----', '1': '.----', '2': '..---', '3': '...--', '4': '....-',
            '5': '.....', '6': '-....', '7': '--...', '8': '---..', '9': '----.'}

    def showNumber(self, number):
        """ Just convert the number to a string and show it """
        
        self.showText(self, str(number))

    def showText(self, text):
        """ Displaying a Morse decoded text on the buzzer, light and possibly display """
        
        morse = self._decodeText(text)
        if self._dp is not None:
            self._dp.showText(morse)
        # go through the string each character at a time
        for char in morse:
            # if the character is in our dictionary, then get the code
            if char == ".":
                self._displaydida(100)
            elif char == "-":
                self._displaydida(250)
            else:
                time.sleep_ms(250)
                    
    ####### Local private methods in MorseDisplay - should not be used from outside ####            
    def _decodeText(self, text):
        morse = []
        for char in text.upper():
            if char in self._morsedict:
                morse.append(self._morsedict[char])
            elif char.isspace():
                morse.append(' ')
        return " ".join(morse)
    
    def _displaydida(self, sleeptime):
        if self._buz is not None:
            self._buz.play()
        if self._light is not None:
            self._light.on()
        time.sleep_ms(sleeptime)
        if self._buz is not None:
            self._buz.stop()
        if self._light is not None:
            self._light.off()
        time.sleep_ms(100)

class SevenSegmentDisplayRaw(Display):
    """
    A Raw 7 segment display that uses RPi PIO along with internal StateMachine
    to poll 4 digits into the display. All digits are shown always so there will be
    leading zeros for numbers under 4 digits

    This does not use any shift registers. All pins must be directly connected to 
    GPIO pins sequentially. 

    Useful only in projects where you have a lot of GPIO pins to spare. Each display 
    with 4 digits requires 12 GPIO pins. 

    Parameters:
        pinstart: GPIO pin number to start sending data from (inclusive) - first 8 pins
        digstart: GPIO pin number to start sending digit data from (inclusive) - last 4 pins

        Example:
            # The following will map:
            # Pins 2-9 will be mapped to the 7 segment pins in order (a-g, dp)
            # Pins 10-13 will be mapped to the 4 digits in order (1-4)
            mydisplay = SevenSegmentDisplayRaw(pinstart=2, digstart=10)

    """
    
    def __init__(self, pinstart=2, digstart=10):
        self._digits = [
            0b11000000, # 0
            0b11111001, # 1
            0b10100100, # 2 
            0b10110000, # 3
            0b10011001, # 4
            0b10010010, # 5
            0b10000010, # 6
            0b11111000, # 7
            0b10000000, # 8
            0b10011000, # 9
            ]
        self._sm = rp2.StateMachine(0, sevseg, freq=2000, out_base=Pin(pinstart), sideset_base=Pin(digstart))
        self._sm.active(1)
  
    def _segmentize(self, num):
        return (
            self._digits[num % 10] | self._digits[num // 10 % 10] << 8
            | self._digits[num // 100 % 10] << 16 
            | self._digits[num // 1000 % 10] << 24 
        )

    def showNumber(self, n):
        self._sm.put(self._segmentize(n))
        
    def reset(self):
        self._sm.put(0xFFFFFFFF)

# Internals used by the PIO state machine
# THIS IS REQUIRED FOR THE SEVEN SEG RAW class
@rp2.asm_pio(out_init=[PIO.OUT_LOW]*8, sideset_init=[PIO.OUT_LOW]*4)
def sevseg():
    wrap_target()
    label("0")
    pull(noblock)           .side(0)      # 0
    mov(x, osr)             .side(0)      # 1
    out(pins, 8)            .side(1)      # 2
    out(pins, 8)            .side(2)      # 3
    out(pins, 8)            .side(4)      # 4
    out(pins, 8)            .side(8)      # 5
    jmp("0")                .side(0)      # 6
    wrap()

class SevenSegmentDisplaySingle(Display):
    """
    Seven Segment Display Single class - supports daisy-chained shift registers
    for a multi-digit 7-segment display.
    """
    
    def __init__(self, dataPin, clockPin, latchPin, numDigits=1):
        self._data = Pin(dataPin, Pin.OUT)
        self._clock = Pin(clockPin, Pin.OUT)
        self._latch = Pin(latchPin, Pin.OUT)
        self._numDigits = numDigits
        
        self._chars = _CHARS
        self.reset()
        
    def _shift_out(self, data_list):
        self._clock.value(0)
        self._latch.value(0)
        self._clock.value(1)
        
        for val in reversed(data_list):
            for i in range(7, -1, -1):
                self._clock.value(0)
                self._data.value((val >> i) & 1)
                self._clock.value(1)
                
        self._clock.value(0)
        self._latch.value(1)
        self._clock.value(1)

    def reset(self):
        self._shift_out([0] * self._numDigits)

    def showNumber(self, number):
        text = str(number)
        if len(text) < self._numDigits:
            text = " " * (self._numDigits - len(text)) + text
        self.showText(text)

    def showNumbers(self, num1, num2, colon=True):
        half1 = self._numDigits // 2
        half2 = self._numDigits - half1
        s1 = str(num1)
        s2 = str(num2)
        if len(s1) < half1:
            s1 = " " * (half1 - len(s1)) + s1
        if len(s2) < half2:
            s2 = "0" * (half2 - len(s2)) + s2
        self.showText(s1 + s2)

    def showText(self, text):
        text = str(text)
        data = []
        i = 0
        while i < len(text) and len(data) < self._numDigits:
            char = text[i]
            val = self._chars.get(char, 0)
            
            if i + 1 < len(text) and text[i+1] == '.':
                val |= 0x80
                i += 1
                
            data.append(val)
            i += 1
            
        while len(data) < self._numDigits:
            data.append(0)
            
        self._shift_out(data)

    def scroll(self, text, speed=250):
        text = str(text) + " " * self._numDigits
        for i in range(len(text)):
            self.showText(text[i:])
            time.sleep_ms(speed)