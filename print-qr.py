#!/usr/bin/python3
import os

PRINTER_DEVICE = "/dev/usb/lp0"
tspl_commands = [
    "SIZE 50 mm, 30 mm\n",
    "GAP 2 mm, 0 mm\n",
    "CLS\n",
    "QRCODE 50,50,L,5,A,0,M2,S3,\"E4B13797BACC\"\n",
    "TEXT 180,75,\"3\",0,1,1,\"Cannatrols\"\n",
    "TEXT 180,125,\"3\",0,1,1,\"E4B13797BACC\"\n",
    "PRINT 1\n"
]

try:
    with open(PRINTER_DEVICE, "w") as printer:
        for command in tspl_commands:
            printer.write(command)
    print("QR code and text sent to printer.")
except Exception as e:
    print(f"Error: {e}")
