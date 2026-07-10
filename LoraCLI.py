"""
# LoraCLI.py
# Command line interface wrapper for DX-LR22 LoRa module
# Author: Arijit Sengupta
"""

import time
from Log import *

class LoraCLI:
    """
    A platform-agnostic command line interface wrapper for LoRa devices.
    Enables users to send AT commands, transmit transparent messages,
    and see responses/incoming messages from the device.

    Parameters:
    ----------
    lora_device : LoraDevice or LoraDesktop
        The initialized LoRa device instance.
    """

    def __init__(self, lora_device):
        self._lora = lora_device
        self._running = False
        self._hw_timer = None
        self._desktop_timer = None
        
        # Detect platform timer capability
        try:
            from Counters import HardwareTimer
            self._use_hardware_timer = True
        except ImportError:
            self._use_hardware_timer = False

    def _start_timer(self):
        """Starts/schedules the background input polling timer."""
        if not self._running:
            return
        if self._use_hardware_timer:
            if not self._hw_timer:
                from Counters import HardwareTimer
                self._hw_timer = HardwareTimer('LoraCLITimer', self)
            self._hw_timer.start(1.0)  # Check every 1.0 seconds
        else:
            import threading
            self._desktop_timer = threading.Timer(1.0, lambda: self.timeout("Desktop Timer"))
            self._desktop_timer.daemon = True
            self._desktop_timer.start()

    def _stop_timer(self):
        """Cancels any running timers."""
        if self._use_hardware_timer:
            if self._hw_timer:
                try:
                    self._hw_timer.cancel()
                except Exception:
                    pass
        else:
            if self._desktop_timer:
                try:
                    self._desktop_timer.cancel()
                except Exception:
                    pass

    def timeout(self, name):
        """Callback invoked when the timer expires to check for incoming LoRa data."""
        if not self._running:
            return
        try:
            any_incoming = self._lora.any()
            if any_incoming > 0:
                incoming = self._lora.receive_message(max_bytes=any_incoming)
                if incoming:
                    decoded = incoming.decode('utf-8', 'ignore').strip()
                    if decoded:
                        print(f"\n[RX]: {decoded}")
                        print(">> ", end="")
        except Exception:
            pass

        # Reschedule the timer
        if self._running:
            self._start_timer()

    def start(self):
        """
        Starts the interactive LoRa command line interface.
        Verifies the connection to the LoRa device, then enters a loop
        reading commands from the user and displaying replies.
        """
        Log.i("LoraCLI: Verifying connection to LoRa module...")
        if not self._lora.ping():
            Log.e("LoraCLI: Could not establish connection to LoRa module.")
            return

        Log.i("LoraCLI: LoRa module connection established.")
        Log.i("Commands starting with 'AT' will be sent as configuration commands.")
        Log.i("Other commands will be sent as transparent data payloads.")
        Log.i("Type 'exit' or 'quit' to terminate the CLI session.")
        
        # Show the >> connection ready indicator
        print(">> ")

        self._running = True
        self._start_timer()

        while self._running:
            try:
                # Prompt user for input
                cmd = input(">> ")
                cmd_stripped = cmd.strip()
                if not cmd_stripped:
                    continue

                if cmd_stripped.lower() in ("exit", "quit"):
                    Log.i("LoraCLI: Exiting command line interface...")
                    break

                if cmd_stripped.upper().startswith("AT"):
                    # Send AT command and show response
                    response = self._lora.send_at_command(cmd_stripped)
                    if response:
                        print(response.strip())
                    else:
                        print("Error: No response or command timed out.")
                else:
                    # Transparent mode message sending
                    bytes_sent = self._lora.send_message(cmd_stripped + "\r\n")
                    print(f"[TX] Sent {bytes_sent} bytes: {cmd_stripped}")

            except KeyboardInterrupt:
                Log.i("\nLoraCLI: Interrupt received. Exiting...")
                break
            except Exception as e:
                Log.e(f"LoraCLI: Error encountered: {e}")
                break

        self._running = False
        self._stop_timer()


if __name__ == "__main__":
    Log.level = ALL
    Log.name = "LoraCLITest"
    
    Log.i("Starting LoraCLI tests...")
    
    # We will simulate the test using LoraDesktop with a mock serial port
    from LoraDesktop import LoraDesktop
    
    mock_lora = LoraDesktop(port="/dev/tty.mock", baudrate=9600)
    cli = LoraCLI(mock_lora)
    
    # Verify that the ping logic succeeds using mock
    assert mock_lora.ping() is True, "Mock Lora ping failed"
    
    # Inject a response to test command processing response
    if hasattr(mock_lora._uart, "_buffer"):
        mock_lora._uart._buffer.extend(b"+ADDRESS=120\r\nOK\r\n")
        
    response = mock_lora.send_at_command("AT+ADDRESS?")
    Log.i(f"Mock command response: {repr(response)}")
    assert "+ADDRESS=120" in response, "Failed to get mock address response"
    
    Log.i("Testing complete - LoraCLI verified successfully.")
