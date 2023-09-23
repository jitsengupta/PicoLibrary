"""
Scanner.py - simple implementation of blocking or unblocking barcode scanner
Written by Arijit Sengupta
Uses stdin to read items scanned.
"""
import sys, select

class Scanner:
    """
    A simplistic Scanner class - give it a prompt and get a response back
    either within a timeout or by blocking indefinitely
    
    No init method - has no attributes
    """
    
    def scanData(self, prompt='Scan code: ', timeout=-1, clear=True) -> str:
        """
        show a prompt, and wait indefinitely (timeout -1 )
        or wait for a certain amount of time (timeout a positive integer)
        returns None if nothing was scanned within the timeout period
        
        Usage:
        s = Scanner()
        barcode = s.Data() # blocking scan
        data = s.scanData(timeout=5) # Wait 5 secondes to enter code

        NOTE - if using in Wokwi, input buffer does not need to be cleared
        NOTE 2. Wokwi does not seem to echo the keyboard data - I may be missing something
        data = s.scanData(timeout=5, clear=False) # no need to clear stdin
        """
        if timeout <=0:
            return input(prompt)
        else:
            print(prompt, end='')
            i, o, e = select.select( [sys.stdin], [], [], timeout)

            if (i):
                l1 = sys.stdin.readline().strip()
                # for some reason on the pico hitting enter causes
                # two scans. This is a temp fix until we can find a
                # better option
                if clear:
                    l2 = sys.stdin.readline().strip()
                    while l2:
                        l2 = sys.stdin.readline().strip()
                return l1
            else:
              return None
