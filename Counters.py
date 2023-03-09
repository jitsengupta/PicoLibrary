import time
from machine import Timer

class Counter:
    def __init__(self):
        print("Counter: constructor")
        self._count = 0

    def reset(self):
        print("Counter - reset")
        self._count = 0

class UpDownCounter(Counter):
    def __init__(self, min = None, max = None):
        print("Updowncounter constructor")
        super().__init__()
        self._min = min
        self._max = max

    def up(self, step=1):
        print("Updowncounter incrementing")
        if (self._max is None or self._count + step <= self._max):
            self._count = self._count + step

    def down(self, step=1):
        print("Updowncounter decrementing")
        if (self._min is None or self._count - step >= self._min):
            self._count = self._count + step

    def __str__(self)->str:
        return f"{self._count}"

class TimeKeeper(Counter):
    def __init__(self):
        print("Timekeeper: constructor")
        super().__init__()
        self._starttime = 0

    def start(self):
        print("Timekeeper: start")
        self._starttime = time.ticks_ms()

    def stop(self):
        print("Timekeeper: stop")
        self._count = self._count + time.ticks_diff(time.ticks_ms(),self._starttime)

    def __str__(self) -> str:
        curtime = self._count + time.ticks_diff(time.ticks_ms(),self._starttime)
        ms = curtime % 1000
        sec = (curtime // 1000) % 60
        min = (curtime // 60000) % 60
        hr = (curtime // 3600000)
        return f"{hr:02d}:{min:02d}:{sec:02d}.{ms:03d}"

class HardwareTimer(Counter):
    def __init__(self, handler):
        super().__init__()
        self._handler = handler
        self._timer = Timer(-1)
        self._started = False

    def start(self, seconds):
        self._count = seconds
        self._timer.init(period = seconds*1000, mode=Timer.PERIODIC, callback = self._handler.timeout())
        self._started = True

    def cancel(self):
        if self._started:
            self._timer.deinit()
        self._started = False
        self._count = 0


class SoftwareTimer(Counter):
    def __init__(self, handler):
        super().__init__()
        self._handler = handler
        self._starttime = 0
        self._started = False

    def start(self, seconds):
        print(f"Starting timer with {seconds} seconds")
        self._count = seconds
        self._starttime = time.ticks_ms()
        self._started = True

    def cancel(self):
        if self._started:
            self._starttime = 0
            print(f"{self._count} sec timer cancelled")
        self._started = False
        self._count = 0

    def check(self):
        if self._started and time.ticks_diff(time.ticks_ms(), self._starttime) > self._count * 1000:
            print(f"{self._count} sec timer is up")
            self._started = False
            self._count = 0
            self._handler.timeout()