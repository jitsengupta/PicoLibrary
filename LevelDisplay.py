"""
LevelDisplay.py
A base LevelDisplay class with a couple of subclasses with implementations using
A LightStrip and an LCD Display - I may add additional implementations in the future
for example, using an actual 7 led bar - maybe with a shift register
"""
from Displays import *
from LightStrip import *
from Log import *

class LevelDisplay:
    """
    Superclass for LevelDisplay.
    Should not be initiated directly. Wish Python had a proper abstract class
    """
    def __init__(self, levels):
        """
        Create a level Display with a max number of levels.
        Note that display will be from 0 (may be nothing displayed)
        Up to _levels_ so levels is inclusive.
        """
        self._levels = levels
        self._curlevel = 0
        
    def showLevel(self, levelpct):
        """
        Show a percentage - appropriate is calculated here.
        Subclasses should overload this method and call super().showLevel(levelpct)
        to calculate the current level
        """
        
        # if percent is < 5, treat it as 0 - nothing displayed
        # if > 95, treat as full. All levels lit up.
        if levelpct <= 5:
            self._curlevel = 0
        elif levelpct >= 95:
            self._curlevel = self._levels
        else:
            self._curlevel = int(self._levels * levelpct / 100)
        Log.i(f'Showing {levelpct}% with {self._curlevel} levels')
        
class LightStripLevel(LevelDisplay):
    """
    Implementation of the Level display using a NeoPixel lightstrip.
    """
    
    def __init__(self, strip):
        """ constructor. call superclass constructor and save the lightstrip variable"""
        
        super().__init__(strip._numleds)
        self._strip = strip
        Log.i("Creating a Light strip level") 
        
    def showLevel(self, levelpct):
        """ Show the level in the light strip. """
        level = levelpct
        super().showLevel(level)
        if self._curlevel == 0:
            self._strip.off()
            return
        color = WHITE if level < 30 else YELLOW if level < 60 else PURPLE if level < 90 else RED
        self._strip.setColor(color, self._curlevel)
        

class LCDLevel(LevelDisplay):
    """
    Implementation of the Level display using an LCD Display custom chars
    """
    
    def __init__(self, display):
        # LCD display can only show 8 levels so we are fixing it
        super().__init__(8)
        self._display = display
        Log.i("Creating an LCD level") 
        
        # Add the custom chars to the PRAM
        for p in range(0,8):
            arr = [0x00]*8
            for z in range(0,p+1):
                arr[7-z] = 0xff
            self._display.addShape(p, arr)

    def showLevel(self, levelpct, row=0, col=0):
        level = levelpct
        super().showLevel(level)
        if self._curlevel == 0:
            self._display.showText('.       ', row, col)
            return
        for l in range (0, self._curlevel):
            self._display.showText(chr(l), row, col+l)
        if self._curlevel < 8:
            self._display.showText(' '*(8-self._curlevel),row, col+self._curlevel)

