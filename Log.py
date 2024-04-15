"""
Log.py - a simplistic Logging process. Built to kind of mimic the
Android Logging process, but at the same time having a global level
set to see the types of logs being displayed.

Basic usage:

Log.level = DEBUG  # set global log level

# Options are: ALL/INFO (everything) DEBUG (debug and higher), ERRO (only errors)
Log.i(f'help')     # Info message: f-strings recommended for showing variables
Log.d(f'value: {v}') # Debug message
Log.e(f'Exception: {x}') # Error message
Log.name('Myproject') # Set a global project name
"""

""" Debug levels """
ALL = 4  # All messages are displayed
INFO = 3  # Basically the same as ALL - for future-proofing
DEBUG = 2  # Info is hidden - debug and higher shown
ERROR = 1  # Only error messages shown
NONE = 0  # No messages are shown from log classes


class Log:

    name = ''
    level = ALL

    @classmethod
    def i(cls, message):
        if (cls.level >= INFO):
            Log.pr(message)

    @classmethod
    def d(cls, message):
        if (cls.level >= DEBUG):
            Log.pr(message)

    @classmethod
    def e(cls, message):
        if (cls.level >= ERROR):
            Log.pr(message)

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
    
    Log.level = ERROR
    Log.i(f'This should NOT print (level: {Log.level})')
    Log.e(f'This should print (level: {Log.level})')
    

