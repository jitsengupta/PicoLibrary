"""
# main.py
# Entry point for the IoT CRM kiosk on Raspberry Pi Pico 2 W
# Author: Hector Gonzalez
"""

from CRMController import CRMController

controller = CRMController()
controller.run()
