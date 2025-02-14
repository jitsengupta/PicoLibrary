"""
RFIDReader.py - a simple implementation of a NFC reader using the MFRC522 module

This is a simple implementation of a RFID reader using the MFRC522 module. 
It is a class that can be used to read and write data to an NFC/13.56 MHz RFID tag.

It uses the Soft_spi class to communicate with the MFRC522 module, and the mfrc522 module to 
interact with the RFID tags. Soft_spi is used because the MFRC522 module uses _spi communication,
and using Soft_spi allows us to use any GPIO pins for communication.

# Author: Arijit Sengupta
"""

from machine import Pin, SoftSPI
import mfrc522
import utime
from Log import *

class RFIDReader:
    """
    The RFIDReader class can be used to create an instance of a RC522 RFID reader.
    Only methods that are implemented are getTagID, readData, writeData, and clearData.
    """
    def __init__(self, mosi, miso, sck, sda):
        """
        The constructor for the RFIDReader class. It initializes the Soft_spi object 
        and the MFRC522 object.

        Parameters:
        - mosi: The pin number for the MOSI pin
        - miso: The pin number for the MISO pin
        - sck: The pin number for the SCK pin
        - sda: The pin number for the CS pin (many boards use SDA for this pin)
        """

        Log.i("RFIDReader constructor")
        self._spi = SoftSPI(baudrate=100000, polarity=0, phase=0, sck=Pin(sck), mosi=Pin(mosi), miso=Pin(miso)) # Soft_spi
        self._sda = Pin(sda, Pin.OUT)
        self._reader = mfrc522.MFRC522(self._spi, self._sda)
        self._key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]  # Default key

    def getTagID(self)->str:
        """
        Get the tag ID of the RFID tag that is detected by the reader.
        The tag ID is a hexadecimal string that represents the unique ID of the tag and is used
        to identify the tag. Typically this is programmed in the facotry and cannot be changed.

        Returns the tag ID as a hexadecimal string if a tag is detected, otherwise returns None.
        """
        
        (stat, tag_type) = self._reader.request(self._reader.CARD_REQIDL)
        if stat != self._reader.OK:
            # try again - every other request seems to return error for some reason
            (stat, tag_type) = self._reader.request(self._reader.CARD_REQIDL)
            
        if stat == self._reader.OK:
            (stat, raw_uid) = self._reader.anticoll()
            if stat == self._reader.OK:
                tag_id_str = ""
                for byte in raw_uid:
                    tag_id_str += "{:02x}".format(byte) # Format with leading zero
                return tag_id_str
        return None

    def readData(self)->str:
        """        
        Read the data stored on the RFID tag that is detected by the reader.
        The data is stored in the data blocks of the tag and can be read by authenticating
        the tag and reading the data blocks. The data is stored as a string of characters.
        """
        
        tag_id = self.getTagID()

        (stat, raw_uid) = self._reader.anticoll()  # Get raw_uid again after successful tag detection
        if stat != self._reader.OK:
            return None

        if self._reader.select_tag(raw_uid) != self._reader.OK:
            self._reader.stop_crypto1()
            return None

        data = ""
        for i in range(1, 64):
            if (i + 1) % 4 != 0:
                if self._reader.auth(self._reader.AUTH, i, self._key, raw_uid) == self._reader.OK:
                    block_data = self._reader.read(i)
                    if block_data:
                        try:
                            block_string = bytearray(block_data).decode()
                            data += block_string.strip('\x00')
                            if len(data) >= 80:
                                break
                        except UnicodeDecodeError:
                            pass  # Handle potential decoding errors

                else:
                    self._reader.stop_crypto1()
                    return None

        self._reader.stop_crypto1()
        Log.d(f'Tag {tag_id} read data: {data}')
        return data

    def writeData(self, data)->bool:
        """
        Write a string of data to the RFID tag that is detected by the reader.
        Most MIFARE tags have 64 data blocks, each of which can store 16 bytes of data. So
        technically you can store up to 1024 bytes of data on a MIFARE tag. However, for this
        implementation, we are limiting the data to 80 characters (80 bytes) to keep it simple.

        Parameters:
        - data: The string of data to write to the tag. Must be 80 characters or less.
        Returns True if the data is written successfully, otherwise returns False.
        """
        if len(data) > 80:
            raise ValueError("Data must be 80 characters or less.")

        tag_id = self.getTagID()
        if not tag_id:
            return False
            
        (stat, raw_uid) = self._reader.anticoll() # Get raw_uid again after successful tag detection
        if stat != self._reader.OK:
            return None


        if self._reader.select_tag(raw_uid) != self._reader.OK:
            self._reader.stop_crypto1()
            return False

        padded_data = data + '\x00' * (80 - len(data))
        data_blocks = [padded_data[i:i + 16] for i in range(0, len(padded_data), 16)]

        block_index = 0
        for i in range(1, 64):
            if (i + 1) % 4 != 0:
                if self._reader.auth(self._reader.AUTH, i, self._key, raw_uid) == self._reader.OK:
                    if block_index < len(data_blocks):
                        status = self._reader.write(i, data_blocks[block_index].encode())
                        if status != self._reader.OK:
                            self._reader.stop_crypto1()
                            return False
                        block_index += 1
                else:
                    self._reader.stop_crypto1()
                    return False

        self._reader.stop_crypto1()
        Log.d(f'Wrote data: {data} to tag: {tag_id}')
        return True

    def clearData(self)->bool:
        """
        Clear all data stored on the RFID tag that is detected by the reader.
        This method writes null bytes (0x00) to all data blocks of the tag to clear the data.
        Returns True if the data is cleared successfully, otherwise returns False.
        """

        tag_id = self.getTagID()
        if not tag_id:
            return False

        (stat, raw_uid) = self._reader.anticoll()
        if stat != self._reader.OK:
            return None

        if self._reader.select_tag(raw_uid) != self._reader.OK:
            self._reader.stop_crypto1()
            return False

        clear_block = bytearray(16)  # Block filled with null bytes (0x00)

        for i in range(1, 64):  # Iterate through data blocks
            if (i + 1) % 4 != 0:  # Skip sector trailer blocks
                if self._reader.auth(self._reader.AUTH, i, self._key, raw_uid) == self._reader.OK:
                    status = self._reader.write(i, clear_block)
                    if status != self._reader.OK:
                        self._reader.stop_crypto1()
                        return False  # Stop if writing fails
                else:
                    self._reader.stop_crypto1()
                    return False  # Authentication failed

        self._reader.stop_crypto1()
        return True
    
if __name__ == "__main__":       
    # Example usage (replace with your actual pin numbers):
    reader = RFIDReader(mosi=5, miso=6, sck=4, sda=7)

    tag_id = reader.getTagID()
    if tag_id:
        print(f"Tag ID: {tag_id}")
        tag_id = reader.getTagID()
        
        read_data = reader.readData()
        if read_data:
            print("Read data:", read_data)
        
        if reader.writeData("Hello, RFID!"):
            print("Data written successfully.")
        else:
            print("Failed to write data.")
        
    else:
        print("No tag detected.")