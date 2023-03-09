"""
A simple buzzer class - use it to play and pause different sounds
ranging from fequencies 10 through 10000
default volume is half volume - set it between 0 and 10
""" 
import time
from machine import Pin, PWM

class Buzzer:
    def beep(self, tone=500, duration=150):
        print(f"Beeping the buzzer at {tone}hz for {duration} ms")
        self.play(tone)
        time.sleep(duration / 1000)
        self.stop()
    
class ActiveBuzzer(Buzzer):
    def __init__(self, pin):
        self._buz = Pin(pin, Pin.OUT)
   
    def play(self, tone=500):
        self._buz.value(1)
        
    def stop(self):
        self._buz.value(0)
    
class PassiveBuzzer(Buzzer):
    def __init__(self, pin):
        print("PassiveBuzzer: constructor")
        self._buz = PWM(Pin(pin))
        self._volume = 5
        self._playing = False
        self.stop()

    def play(self, tone=500):
        print(f"PassiveBuzzer: playing tone {tone}")
        self._buz.freq(tone)
        self._buz.duty_u16(self._volume * 100)
        self._playing = True

    def stop(self):
        print("PassiveBuzzer: stopping tone")
        self._buz.duty_u16(0)
        self._playing = False

    def setVolume(self, volume=5):
        print(f"PassiveBuzzer: changing volume to {volume}")
        self._volume = volume
        if (self._playing):
            self._buz.duty_u16(self._volume * 100)
