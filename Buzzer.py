"""
# Buzzer.py - Object-oriented implementation of active and passive buzzers
# Author: Arijit Sengupta
"""

import time
from machine import Pin, PWM
from Log import *

class Buzzer:
    """
    A simple buzzer class - use it to play and pause different sounds
    ranging from fequencies 10 through 10000
    default volume is half volume - set it between 0 and 10
    """ 
    
    def beep(self, tone=500, duration=150):
        Log.i(f"Beeping the buzzer at {tone}hz for {duration} ms")
        self.play(tone)
        time.sleep(duration / 1000)
        self.stop()
    
class ActiveBuzzer(Buzzer):
    """
    An active buzzer has an internal oscillator that plays a fixed tone when power is applied
    Cannot control the tone. Only turn on and off.
    """
    
    def __init__(self, pin):
        self._buz = Pin(pin, Pin.OUT)
   
    def play(self, tone=500):
        """ Play sound. Tone is ignored. """
        
        self._buz.value(1)
        
    def stop(self):
        """ Stop the sound. """
        
        self._buz.value(0)
    
class PassiveBuzzer(Buzzer):
    """
    A passive buzzer does not have an internal oscillator. MC needs to send a PWM signal
    to play tones. The tone is controlled by the frequency of the PWM, and the volume level
    is controlled by the duty cycle. Setting duty cycle to 0 stops sound.
    """
    
    def __init__(self, pin):
        Log.i("PassiveBuzzer: constructor")
        self._buz = PWM(Pin(pin))
        self._volume = 5
        self._playing = False
        self.stop()

    def play(self, tone=500):
        """ play the supplied tone. """
        
        Log.i(f"PassiveBuzzer: playing tone {tone}")
        self._buz.freq(tone)
        self._buz.duty_u16(self._volume * 100)
        self._playing = True

    def stop(self):
        """ Stop playing sound """
        
        Log.i("PassiveBuzzer: stopping tone")
        self._buz.duty_u16(0)
        self._playing = False

    def setVolume(self, volume=5):
        """ Change the volume of the sound currently playing and future plays """
        
        Log.i(f"PassiveBuzzer: changing volume to {volume}")
        self._volume = volume
        if (self._playing):
            self._buz.duty_u16(self._volume * 100)

# Known tones from https://github.com/james1236/buzzer_music
tones = {
    'C0':16,
    'C#0':17,
    'D0':18,
    'D#0':19,
    'E0':21,
    'F0':22,
    'F#0':23,
    'G0':24,
    'G#0':26,
    'A0':28,
    'A#0':29,
    'B0':31,
    'C1':33,
    'C#1':35,
    'D1':37,
    'D#1':39,
    'E1':41,
    'F1':44,
    'F#1':46,
    'G1':49,
    'G#1':52,
    'A1':55,
    'A#1':58,
    'B1':62,
    'C2':65,
    'C#2':69,
    'D2':73,
    'D#2':78,
    'E2':82,
    'F2':87,
    'F#2':92,
    'G2':98,
    'G#2':104,
    'A2':110,
    'A#2':117,
    'B2':123,
    'C3':131,
    'C#3':139,
    'D3':147,
    'D#3':156,
    'E3':165,
    'F3':175,
    'F#3':185,
    'G3':196,
    'G#3':208,
    'A3':220,
    'A#3':233,
    'B3':247,
    'C4':262,
    'C#4':277,
    'D4':294,
    'D#4':311,
    'E4':330,
    'F4':349,
    'F#4':370,
    'G4':392,
    'G#4':415,
    'A4':440,
    'A#4':466,
    'B4':494,
    'C5':523,
    'C#5':554,
    'D5':587,
    'D#5':622,
    'E5':659,
    'F5':698,
    'F#5':740,
    'G5':784,
    'G#5':831,
    'A5':880,
    'A#5':932,
    'B5':988,
    'C6':1047,
    'C#6':1109,
    'D6':1175,
    'D#6':1245,
    'E6':1319,
    'F6':1397,
    'F#6':1480,
    'G6':1568,
    'G#6':1661,
    'A6':1760,
    'A#6':1865,
    'B6':1976,
    'C7':2093,
    'C#7':2217,
    'D7':2349,
    'D#7':2489,
    'E7':2637,
    'F7':2794,
    'F#7':2960,
    'G7':3136,
    'G#7':3322,
    'A7':3520,
    'A#7':3729,
    'B7':3951,
    'C8':4186,
    'C#8':4435,
    'D8':4699,
    'D#8':4978,
    'E8':5274,
    'F8':5588,
    'F#8':5920,
    'G8':6272,
    'G#8':6645,
    'A8':7040,
    'A#8':7459,
    'B8':7902,
    'C9':8372,
    'C#9':8870,
    'D9':9397,
    'D#9':9956,
    'E9':10548,
    'F9':11175,
    'F#9':11840,
    'G9':12544,
    'G#9':13290,
    'A9':14080,
    'A#9':14917,
    'B9':15804
}

# Some basic do re mi tones
DO = tones['C4']
RE = tones['D4']
MI = tones['E4']
FA = tones['F4']
SO = tones['G4']
LA = tones['A4']
TI = tones['B4']
DO2 = tones['C5']
