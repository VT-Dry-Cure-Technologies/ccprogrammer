#!/usr/bin/python3
import os

PRINTER_DEVICE = "/dev/rfcomm0"

def print_qr_code(qr_data):
    """
    Print a QR code with the given data
    
    Args:
        qr_data (str): The data to encode in the QR code
    """
    tspl_commands = [
        "SIZE 50 mm, 30 mm\n",
        "GAP 2 mm, 0 mm\n",
        "CLS\n",
        f"QRCODE 50,50,L,5,A,0,M2,S3,\"{qr_data}\"\n",
        "TEXT 180,75,\"3\",0,1,1,\"Cannatrols\"\n",
        f"TEXT 180,125,\"3\",0,1,1,\"{qr_data}\"\n",
        "PRINT 1\n"
    ]

    try:
        with open(PRINTER_DEVICE, "w") as printer:
            for command in tspl_commands:
                printer.write(command)
        print(f"QR code and text sent to printer with data: {qr_data}")
    except Exception as e:
        print(f"Error: {e}")

def main():
    """Main function to demonstrate usage"""
    # Example usage
    qr_data = "E4B13797BACC"
    print_qr_code(qr_data)

if __name__ == "__main__":
    main()
