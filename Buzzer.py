"""
# Buzzer.py - Object-oriented implementation of active and passive buzzers
# Author: Arijit Sengupta
"""

import time
from machine import Pin, PWM

class Buzzer:
    """
    A simple buzzer class - use it to play and pause different sounds
    ranging from fequencies 10 through 10000
    default volume is half volume - set it between 0 and 10
    """ 
    
    def beep(self, tone=500, duration=150):
        print(f"Beeping the buzzer at {tone}hz for {duration} ms")
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
        print("PassiveBuzzer: constructor")
        self._buz = PWM(Pin(pin))
        self._volume = 5
        self._playing = False
        self.stop()

    def play(self, tone=500):
        """ play the supplied tone. """
        
        print(f"PassiveBuzzer: playing tone {tone}")
        self._buz.freq(tone)
        self._buz.duty_u16(self._volume * 100)
        self._playing = True

    def stop(self):
        """ Stop playing sound """
        
        print("PassiveBuzzer: stopping tone")
        self._buz.duty_u16(0)
        self._playing = False

    def setVolume(self, volume=5):
        """ Change the volume of the sound currently playing and future plays """
        
        print(f"PassiveBuzzer: changing volume to {volume}")
        self._volume = volume
        if (self._playing):
            self._buz.duty_u16(self._volume * 100)
