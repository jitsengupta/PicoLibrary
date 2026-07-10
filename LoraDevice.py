"""
# LoraDevice.py
# Subclass of UARTDevice designed for DX-LR22 LoRa module based on Semtech LLCC68
# Author: Arijit Sengupta
"""

import time
from Log import *
from UARTDevice import UARTDevice

class LoraDevice(UARTDevice):
    """
    A class to interface with the DX-LR22 LoRa serial module.
    Inherits from UARTDevice and provides methods to configure and communicate
    using AT commands and serial data transfer.

    Parameters:
    ----------
    uart_id : int
        The UART peripheral ID (usually 0 or 1 on RP2040)
    baudrate : int, optional
        The serial communication speed, default: 9600
    tx_pin : int, optional
        The GPIO pin number for TX (default: None)
    rx_pin : int, optional
        The GPIO pin number for RX (default: None)
    timeout : int, optional
        Read timeout in milliseconds (default: 1000)

    Examples:
    ---------
    1. Instantiating and sending a ping:
       lora = LoraDevice(uart_id=1, baudrate=9600)
       if lora.ping():
           Log.i("LoRa Module connected successfully")
    """

    def __init__(self, uart_id, baudrate=9600, tx_pin=None, rx_pin=None, timeout=1000):
        super().__init__(uart_id=uart_id, baudrate=baudrate, tx_pin=tx_pin, rx_pin=rx_pin, timeout=timeout)
        self._in_at_mode = False
        Log.i("LoraDevice: Initialized LoRa module controller.")

    def enter_at_mode(self) -> bool:
        """
        Sends the '+++' sequence to transition the LoRa module into AT command mode.

        Returns:
        -------
        bool
            True if command mode entered successfully, False otherwise.
        """
        if self._in_at_mode:
            return True
        Log.d("LoraDevice: Entering AT command mode...")
        self.flush()
        # DX-LR22 expects '+++\r\n' to trigger mode transition
        self.send("+++\r\n")
        resp = self._read_raw_response(expected="Entry AT", timeout_ms=1000)
        if "Entry AT" in resp:
            self._in_at_mode = True
            Log.i("LoraDevice: Successfully entered AT command mode.")
            return True
        Log.e("LoraDevice: Failed to enter AT command mode.")
        return False

    def exit_at_mode(self) -> bool:
        """
        Sends the '+++' sequence to transition the LoRa module back to transparent mode.

        Returns:
        -------
        bool
            True if exited command mode successfully, False otherwise.
        """
        if not self._in_at_mode:
            return True
        Log.d("LoraDevice: Exiting AT command mode...")
        self.flush()
        self.send("+++\r\n")
        resp = self._read_raw_response(expected="Exit AT", timeout_ms=1000)
        if "Exit AT" in resp:
            self._in_at_mode = False
            Log.i("LoraDevice: Successfully exited AT command mode.")
            return True
        Log.e("LoraDevice: Failed to exit AT command mode.")
        return False

    def _read_raw_response(self, expected="OK", timeout_ms=1000) -> str:
        """Reads incoming characters from UART until expected substring or timeout occurs."""
        start = time.ticks_ms() if hasattr(time, 'ticks_ms') else int(time.time() * 1000)
        response = ""
        while True:
            if self.any() > 0:
                line = self.readline()
                if line:
                    response += line
                    if expected in response or "ERROR" in response:
                        break
            now = time.ticks_ms() if hasattr(time, 'ticks_ms') else int(time.time() * 1000)
            elapsed = now - start
            if elapsed < 0:
                start = now
                elapsed = 0
            if elapsed > timeout_ms:
                break
            time.sleep(0.01)
        return response

    def send_at_command(self, cmd, expected="OK", timeout_ms=1000) -> str:
        """
        Sends an AT command to the LoRa module and reads the response.
        Automatically transitions the module to and from AT mode if needed.

        Parameters:
        ----------
        cmd : str
            The AT command to send (e.g. "AT+ADDRESS=120").
        expected : str, optional
            The expected substring in the response to indicate success (default: "OK").
        timeout_ms : int, optional
            Timeout for waiting for the response in milliseconds.

        Returns:
        -------
        str
            The response received from the module.
        """
        auto_mode = False
        if not self._in_at_mode and cmd.strip() != "+++":
            if not self.enter_at_mode():
                return ""
            auto_mode = True

        # Ensure command ends with CRLF
        if not cmd.endswith("\r\n"):
            cmd += "\r\n"
        
        Log.d(f"LoraDevice Sending command: {cmd.strip()}")
        self.flush()
        self.send(cmd)
        
        response = self._read_raw_response(expected, timeout_ms)
        Log.d(f"LoraDevice Received response: {response.strip()}")
        
        if auto_mode:
            self.exit_at_mode()
            
        return response

    def ping(self) -> bool:
        """
        Pings the module to check if it's responsive.

        Returns:
        -------
        bool
            True if module responds with OK, False otherwise.
        """
        resp = self.send_at_command("AT")
        return "OK" in resp

    def reset(self) -> bool:
        """
        Resets the LoRa module.

        Returns:
        -------
        bool
            True if reset succeeds.
        """
        resp = self.send_at_command("AT+RESET")
        return "OK" in resp

    def get_address(self) -> int:
        """
        Gets the module address.

        Returns:
        -------
        int
            The address of the module (0-65535), or -1 if query fails.
        """
        resp = self.send_at_command("AT+ADDRESS?")
        # Expected response: +ADDRESS=<addr>
        for line in resp.split("\n"):
            if "+ADDRESS=" in line:
                try:
                    parts = line.strip().split("=")
                    return int(parts[1])
                except (ValueError, IndexError):
                    pass
        return -1

    def set_address(self, address) -> bool:
        """
        Sets the module address.

        Parameters:
        ----------
        address : int
            The module address (0-65535).

        Returns:
        -------
        bool
            True if command succeeded.
        """
        resp = self.send_at_command(f"AT+ADDRESS={address}")
        return "OK" in resp

    def get_network_id(self) -> int:
        """
        Gets the module network ID.

        Returns:
        -------
        int
            The network ID of the module (0-255), or -1 if query fails.
        """
        resp = self.send_at_command("AT+NETWORKID?")
        for line in resp.split("\n"):
            if "+NETWORKID=" in line:
                try:
                    parts = line.strip().split("=")
                    return int(parts[1])
                except (ValueError, IndexError):
                    pass
        return -1

    def set_network_id(self, network_id) -> bool:
        """
        Sets the module network ID.

        Parameters:
        ----------
        network_id : int
            The module network ID (0-255).

        Returns:
        -------
        bool
            True if command succeeded.
        """
        resp = self.send_at_command(f"AT+NETWORKID={network_id}")
        return "OK" in resp

    def set_lora_parameters(self, sf, bw, cr, header) -> bool:
        """
        Sets the LoRa radio parameters (Spreading Factor, Bandwidth, Coding Rate, etc.).

        Parameters:
        ----------
        sf : int
            Spreading Factor (e.g. 5-12)
        bw : int
            Bandwidth (e.g. 0-9 corresponding to different bandwidths)
        cr : int
            Coding Rate (e.g. 1-4)
        header : int
            Header presence (0: explicit header, 1: implicit header)

        Returns:
        -------
        bool
            True if command succeeded.
        """
        resp = self.send_at_command(f"AT+PARAMETER={sf},{bw},{cr},{header}")
        return "OK" in resp

    def set_baudrate(self, baudrate) -> bool:
        """
        Updates both the device's internal UART baud rate and the LoRa module's baud rate.

        Parameters:
        ----------
        baudrate : int
            The new baudrate to apply.

        Returns:
        -------
        bool
            True if command succeeded.
        """
        # First send setting command to LoRa module at current baudrate
        resp = self.send_at_command(f"AT+IPR={baudrate}")
        if "OK" in resp:
            # Let the command complete and update local UART config
            time.sleep(0.1)
            super().set_baudrate(baudrate)
            return True
        return False

    def send_message(self, message) -> int:
        """
        Sends a message in transparent mode.

        Parameters:
        ----------
        message : str or bytes
            The payload to transmit.

        Returns:
        -------
        int
            The number of bytes sent.
        """
        return self.send(message)

    def receive_message(self, max_bytes=None, timeout_ms=1000) -> bytes:
        """
        Receives an incoming message payload.

        Parameters:
        ----------
        max_bytes : int, optional
            Maximum bytes to read.
        timeout_ms : int, optional
            Timeout for reading.

        Returns:
        -------
        bytes
            The received message bytes.
        """
        return self.receive(num_bytes=max_bytes, timeout_ms=timeout_ms)

    def get_info(self) -> str:
        """
        Sends the 'AT+HELP' command to retrieve LoRa command and config info.

        Returns:
        -------
        str
            The help/info information returned by the module.
        """
        return self.send_at_command("AT+HELP")


if __name__ == "__main__":
    Log.level = ALL
    Log.name = "LoraDeviceTest"
    
    Log.i("Starting LoraDevice tests...")
    
    # Initialize LoraDevice
    lora = LoraDevice(uart_id=1, baudrate=9600)
    
    # Test ping with mocked response
    ping_ok = lora.ping()
    Log.i(f"Ping response: {ping_ok}")
    assert ping_ok is True, "Ping test failed"
    
    # Test setting Address
    set_addr_ok = lora.set_address(120)
    Log.i(f"Set Address response: {set_addr_ok}")
    assert set_addr_ok is True, "Set Address failed"

    # Test getting Address
    addr = lora.get_address()
    Log.i(f"Get Address: {addr}")
    assert addr == 120, f"Get Address mismatch: expected 120, got {addr}"

    # Test setting Network ID
    set_net_ok = lora.set_network_id(18)
    Log.i(f"Set Network ID response: {set_net_ok}")
    assert set_net_ok is True, "Set Network ID failed"

    # Test getting Network ID
    net_id = lora.get_network_id()
    Log.i(f"Get Network ID: {net_id}")
    assert net_id == 18, f"Get Network ID mismatch: expected 18, got {net_id}"

    # Test get_info method
    info_text = lora.get_info()
    Log.i(f"Info/Help Response:\n{info_text}")
    assert "AT+ADDRESS" in info_text, "get_info method did not return expected command help"

    # Test sending transparency data
    bytes_sent = lora.send_message("Test message")
    Log.i(f"Transparent sent bytes: {bytes_sent}")
    assert bytes_sent == 12, "Transparent send failed"
    
    Log.i("Testing complete - LoraDevice verified successfully.")
