"""
OtherDisplays.py - This file contains the implementation of other displays
than the basic 16x2 LCD display that comes with the basic kits. This will
allow us to reduce the number of imports in the main code and also allow
us to keep the number of files in the project to a minimum.

# Currently supports 4-digit seven-segment displays - both with a tm1637 backpack
# and without (using PIO) - PIO 7 seg only supports number
# Also supports MAX7219 Dot Matrix displays
"""

from Displays import *
from Log import *
import rp2
from rp2 import PIO

class SevenSegmentDisplay(Display):
    """
    Seven Segment Display class - implements a 4-digit seven segment display
    Decimal points not supported - colon can be used when showing two numbers
    """

    def __init__(self, clk=16, dio=17):
        import tm1637
        self._tm = tm1637.TM1637(clk=Pin(clk), dio=Pin(dio))

    def reset(self):
        """ clear the display screen  """
        
        self._tm.write([0, 0, 0, 0])

    def showNumber(self, number):
        """ show a single number """
        
        self._tm.number(number)

    def showNumbers(self, num1, num2, colon=True):
        """  Show two numbers optionally separated by a colon by default, the colon is shown """
        
        self._tm.numbers(num1, num2, colon)

    def showText(self, text):
        """
        Show a string - only first 4 characters will be shown
        for anything bigger than 4 characters.
        """
        
        self._tm.show(text)

    def scroll(self, text, speed=250):
        """
        Scroll a longer text - note that this will use a sleep
        call to pause between movements.
        """
        
        self._tm.scroll(text, speed)

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
        
        # Mapping alphanumeric chars to 7-segment display byte
        # A=1, B=2, C=4, D=8, E=16, F=32, G=64, DP=128
        self._chars = {
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
            '_': 0x08, '=': 0x48, '.': 0x80
        }
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