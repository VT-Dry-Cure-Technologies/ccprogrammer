#!/usr/bin/python3
import subprocess
import signal
from bluetooth_scanner import scan_for_printer

PRINTER_DEVICE = "/dev/rfcomm0"

def bind_rfcomm(device_address):
    """Bind rfcomm0 to device address"""
    try:
        # Check if already bound
        result = subprocess.run(['rfcomm'], capture_output=True, text=True)
        if f"rfcomm0: {device_address}" in result.stdout:
            return True
        
        # Release if bound to different device
        if "rfcomm0:" in result.stdout:
            subprocess.run(['sudo', 'rfcomm', 'release', '0'])
        
        # Bind to device
        result = subprocess.run(['sudo', 'rfcomm', 'bind', '0', device_address, '1'])
        return result.returncode == 0
    except:
        return False

def print_qr_code(qr_data, number_of_prints=1):
    """Print QR code with given data"""
    success, address = scan_for_printer(5)
    if not success:
        return "Error: Printer not found"
    
    if not bind_rfcomm(address):
        return "Error: Failed to bind rfcomm"
    
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
        for i in range(number_of_prints):
            with open(PRINTER_DEVICE, 'w') as printer:
                for command in tspl_commands:
                    printer.write(command)
        return "Success"
    except Exception as e:
        return f"Error: {e}"

class QRPrinter:
    """Simple QR printer class with persistent connection"""
    
    def __init__(self):
        self.connected = False
    
    def connect(self):
        """Connect to printer"""
        print(f"Connecting to printer")

        success, address = scan_for_printer(5)
        if not success:
            return False
        
        if bind_rfcomm(address):
            self.connected = True
            return True
        return False

    def is_connected(self):
        return self.connected
    
    def print_qr_code(self, qr_data, number_of_prints=1):
        """Print QR code using existing connection"""
        if not self.connected:
            if not self.connect():
                return "Error: Cannot find printer"
        
        tspl_commands = [
            "SIZE 50 mm, 30 mm\n",
            "GAP 2 mm, 0 mm\n",
            "CLS\n",
            f"QRCODE 50,50,L,5,A,0,M2,S3,\"{qr_data}\"\n",
            "TEXT 180,75,\"3\",0,1,1,\"VTDC Tech\"\n",
            f"TEXT 180,125,\"3\",0,1,1,\"{qr_data}\"\n",
            "PRINT 1\n"
        ]

        def timeout_handler(signum, frame):
            raise TimeoutError("Printer write timeout")

        try:
            # Set 5 second timeout for file operations
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(5)
            
            with open(PRINTER_DEVICE, 'w') as printer:
                for i in range(number_of_prints):
                    for command in tspl_commands:
                        printer.write(command)
                printer.flush()
            
            signal.alarm(0)  # Cancel timeout
            return "Success"
        except TimeoutError:
            self.connected = False
            return "Error: Printer disconnected or not responding"
        except Exception as e:
            self.connected = False
            return f"Error: {e}"
        finally:
            signal.alarm(0)  # Ensure timeout is cancelled
    
    def disconnect(self):
        """Disconnect from printer"""
        try:
            subprocess.run(['sudo', 'rfcomm', 'release', '0'])
            self.connected = False
        except:
            pass

def main():
    """Example usage"""
    qr_data = "E4B13797BACC"
    
    # Method 1: Simple function call
    print_qr_code(qr_data)
    
    # Method 2: Class with persistent connection
    printer = QRPrinter()
    printer.print_qr(qr_data)
    printer.print_qr("ANOTHER_CODE", 2)
    printer.disconnect()

if __name__ == "__main__":
    main()
