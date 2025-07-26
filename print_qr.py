#!/usr/bin/python3
import os
import subprocess
import re
from bluetooth_scanner import scan_for_printer
import concurrent.futures

PRINTER_DEVICE = "/dev/rfcomm0"

def check_and_bind_rfcomm(device_address):
    """
    Check if rfcomm0 is bound to the device address, if not bind it
    
    Args:
        device_address (str): The Bluetooth device address to bind
        
    Returns:
        bool: True if binding is successful or already bound, False otherwise
    """
    try:
        # Check current rfcomm bindings
        result = subprocess.run(['rfcomm'], capture_output=True, text=True)
        if result.returncode != 0:
            print("Error: rfcomm command not found or failed")
            return False
        
        # Parse rfcomm output to check if device is already bound
        rfcomm_output = result.stdout
        print(f"Current rfcomm bindings:\n{rfcomm_output}")
        
        # Check if rfcomm0 is already bound to our device
        if f"rfcomm0: {device_address}" in rfcomm_output:
            print(f"✓ rfcomm0 is already bound to {device_address}")
            return True
        
        # Check if rfcomm0 exists but is bound to a different device
        if "rfcomm0:" in rfcomm_output:
            print("rfcomm0 exists but is bound to a different device, unbinding first...")
            subprocess.run(['sudo', 'rfcomm', 'release', '0'], check=True)
        
        # Bind rfcomm0 to our device
        print(f"Binding rfcomm0 to {device_address}...")
        result = subprocess.run([
            'sudo', 'rfcomm', 'bind', '0', device_address, '1'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✓ Successfully bound rfcomm0 to {device_address}")
            return True
        else:
            print(f"✗ Failed to bind rfcomm0: {result.stderr}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"Error executing rfcomm command: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

def print_qr_code(qr_data, number_of_prints=1):
    """
    Print a QR code with the given data
    
    Args:
        qr_data (str): The data to encode in the QR code
    """
    success, address = scan_for_printer(5)
    if not success:
        return "Error: Printer not found"
    
    # Check and bind rfcomm if needed
    if not check_and_bind_rfcomm(address):
        return "Error: Failed to bind rfcomm device"
    
    tspl_commands = [
        "SIZE 50 mm, 30 mm\n",
        "GAP 2 mm, 0 mm\n",
        "CLS\n",
        f"QRCODE 50,50,L,5,A,0,M2,S3,\"{qr_data}\"\n",
        "TEXT 180,75,\"3\",0,1,1,\"VTDC Tech\"\n",
        f"TEXT 180,125,\"3\",0,1,1,\"{qr_data}\"\n",
        "PRINT 1\n"
    ]

    try:
        # Use Python file I/O to write to the rfcomm device
        print("Sending commands to printer...")
        for i in range(number_of_prints):
            with open(PRINTER_DEVICE, 'w') as printer:
                for command in tspl_commands:
                    printer.write(command)
        print(f"✓ QR code and text sent to printer with data: {qr_data}")
        return "Success"
    except Exception as e:
        print(f"Error: {e}")
        return f"Error: {e}"

def print_qr_code_with_timeout(qr_data, number_of_prints=1, timeout=15):
    """
    Run print_qr_code with a timeout. If the timeout is reached, return an error message.
    Args:
        qr_data (str): The data to encode in the QR code
        timeout (int): Timeout in seconds
    Returns:
        str: Success or error message
    """
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(print_qr_code, qr_data, number_of_prints)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            return "Error: Print operation timed out"

def main():
    """Main function to demonstrate usage"""
    # Example usage
    qr_data = "E4B13797BACC"
    print_qr_code(qr_data)

if __name__ == "__main__":
    main()
