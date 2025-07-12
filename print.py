# sudo usermod -a -G lp pi
# exit
# groups
# sudo chmod 666 /dev/usb/lp0
# ls -l /dev/usb/lp0
# echo -e "SIZE 48 mm, 25 mm\nGAP 2 mm, 0 mm\nCLS\nTEXT 100,100,\"3\",0,1,1,\"TEST PRINT\"\nPRINT 1\n" > /dev/usb/lp0
# python3 -m venv ~/escpos_venv
# source ~/escpos_venv/bin/activate
# pip3 install python-escpos
import os

PRINTER_DEVICE = "/dev/usb/lp0"
tspl_commands = [
    "SIZE 48 mm, 25 mm\n",  # Label size (adjust as needed)
    "GAP 2 mm, 0 mm\n",     # Gap between labels
    "CLS\n",                # Clear buffer
    "QRCODE 100,50,L,5,A,0,M2,S3,\"https://example.com\"\n",  # QR code
    "TEXT 100,150,\"3\",0,1,1,\"Scan Me\"\n",  # Optional text
    "PRINT 1\n"             # Print one label
]

try:
    with open(PRINTER_DEVICE, "w") as printer:
        for command in tspl_commands:
            printer.write(command)
    print("QR code sent to printer.")
except Exception as e:
    print(f"Error: {e}")
