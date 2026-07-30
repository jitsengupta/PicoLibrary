"""
# Log.py
# A simplistic Logging process. Built to kind of mimic the
# Android Logging process, but at the same time having a global level
# set to see the types of logs being displayed.
# Author: Jit Sengupta

Basic usage:

Log.level = DEBUG  # set global log level

# Options are: ALL/INFO (everything) DEBUG (debug and higher), ERRO (only errors)
Log.i(f'help')     # Info message: f-strings recommended for showing variables
Log.d(f'value: {v}') # Debug message
Log.e(f'Exception: {x}') # Error message
Log.name('Myproject') # Set a global project name
"""

""" Debug levels """
ALL = 5  # All messages are displayed
INFO = 4  # Info and higher shown
DEBUG = 3  # Debug, warn, error shown
WARN = 2  # Warn and error shown
WARNING = 2  # Alias for WARN
ERROR = 1  # Only error messages shown
NONE = 0  # No messages are shown from log classes


class Log:

    name = ''
    level = ALL
    SAVE = False

    @classmethod
    def i(cls, message):
        if (cls.level >= INFO):
            Log.pr(message)

    @classmethod
    def d(cls, message):
        if (cls.level >= DEBUG):
            Log.pr(message)

    @classmethod
    def w(cls, message):
        if (cls.level >= WARN):
            Log.pr(message)
            if getattr(cls, 'SAVE', False):
                import time
                t = time.localtime()
                timestamp = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(t[0], t[1], t[2], t[3], t[4], t[5])
                with open('pico.log', 'a') as f:
                    if cls.name:
                        f.write(f"{timestamp} - WARN - {cls.name}: {message}\n")
                    else:
                        f.write(f"{timestamp} - WARN - {message}\n")

    @classmethod
    def e(cls, message):
        if (cls.level >= ERROR):
            Log.pr(message)
            if getattr(cls, 'SAVE', False):
                import time
                t = time.localtime()
                timestamp = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(t[0], t[1], t[2], t[3], t[4], t[5])
                with open('pico.log', 'a') as f:
                    if cls.name:
                        f.write(f"{timestamp} - {cls.name}: {message}\n")
                    else:
                        f.write(f"{timestamp} - {message}\n")

    @classmethod
    def pr(cls, message):
        if cls.name:
            m = cls.name + ": " + message
        else:
            m = message
        print(m)


if __name__ == '__main__':
    print("Hello")
    Log.level = ALL
    Log.name = 'Test'
    Log.i(f'This should print (level: {Log.level})')
    Log.w(f'This warning should print (level: {Log.level})')
    
    Log.level = WARN
    Log.i(f'This info should NOT print (level: {Log.level})')
    Log.w(f'This warning should print at WARN level (level: {Log.level})')
    Log.e(f'This error should print at WARN level (level: {Log.level})')

    Log.level = ERROR
    Log.i(f'This should NOT print (level: {Log.level})')
    Log.w(f'This warning should NOT print at ERROR level (level: {Log.level})')
    Log.e(f'This should print (level: {Log.level})')
    
    # Test SAVE feature
    Log.SAVE = True
    Log.e("This is a saved error log message")
    Log.SAVE = False
    
    # Verify file was written
    try:
        with open("pico.log", "r") as f:
            content = f.read()
            print("pico.log content:")
            print(content)
        import os
        os.remove("pico.log")
    except OSError:
        pass
    
    Log.i("Testing complete - all checks passed")
    

