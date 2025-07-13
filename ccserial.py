#!/usr/bin/env python3
"""
Serial communication module for FT232H device monitoring.
Handles serial output recording and device information extraction.
"""

import serial
import time
import threading
from datetime import datetime


class SerialRecorder:
    def __init__(self, gui_callback=None):
        """
        Initialize the serial recorder.
        
        Args:
            gui_callback: Function to call for GUI updates (optional)
        """
        self.gui_callback = gui_callback
    
    def record_device_info(self, port, duration=5, baudrate=921600):
        """
        Record serial output and extract device information.
        
        Args:
            port: Serial port to connect to
            duration: Recording duration in seconds (default: 5)
            baudrate: Serial baudrate (default: 921600)
            
        Returns:
            dict: Dictionary with 'address', 'version', 'success' keys
        """
        try:
            # Open serial connection
            ser = serial.Serial(port, baudrate=baudrate, timeout=1)
            
            # Record for specified duration
            start_time = time.time()
            output = ""
            asked = False
            address_received = False
            version_received = False
            line_buffer = ""
            address = None
            version = None
            
            while time.time() - start_time < duration:
                if ser.in_waiting > 0:
                    data = ser.read(ser.in_waiting)
                    try:
                        text = data.decode('utf-8', errors='replace')
                        output += text
                        
                        # Add to line buffer and process complete lines
                        line_buffer += text
                        lines = line_buffer.split('\n')
                        
                        # Keep the last line in buffer if it's incomplete
                        if not text.endswith('\n'):
                            line_buffer = lines[-1]
                            lines = lines[:-1]
                        else:
                            line_buffer = ""
                        
                        for line in lines:
                            # Check for complete device info line
                            if line.startswith('[ALL ]: Device: Shell; ID:'):
                                print(line + '\n', end='', flush=True)
                                # Extract address from the line
                                if 'ID:' in line and not address_received:
                                    address = line.split('ID:')[1].strip()
                                    address_received = True
                                    if self.gui_callback:
                                        self.gui_callback('address', address)
                            
                            # Check for partial device info line (first part)
                            elif line.startswith('[ALL ]: Device: Shell') and not line.endswith('; ID:'):
                                # This might be the first part of a split line
                                pass
                            
                            # Check for partial device info line (second part with ID)
                            elif line.strip().startswith('; ID:') and not address_received:
                                # This is the second part of a split device line
                                address = line.strip().split('ID:')[1].strip()
                                address_received = True
                                if self.gui_callback:
                                    self.gui_callback('address', address)
                            
                            # Check for version line
                            if line.startswith('[ALL ]: CoolCure2 - Version:'):
                                # Extract version from the line
                                if 'Version:' in line and not version_received:
                                    version = line.split('Version:')[1].strip()
                                    version_received = True
                                    if self.gui_callback:
                                        self.gui_callback('version', version)
                        
                        # Check if both values are received, exit early if so
                        if address_received and version_received:
                            print("\n" + "=" * 50)
                            print("Both address and version received - stopping early")
                            print("=" * 50 + "\n")
                            break
                            
                    except UnicodeDecodeError:
                        # Print as hex if can't decode
                        print(f"[HEX: {data.hex()}]", end='', flush=True)
                
                # Send query command after 1 second if not already sent
                if time.time() - start_time > 1 and asked == False:
                    asked = True
                    ser.write(b"?\n")
                
                time.sleep(0.01)  # Small delay to prevent busy waiting
            
            ser.close()
            
            # Return results
            success = address_received and version_received
            return {
                'address': address,
                'version': version,
                'success': success,
                'address_received': address_received,
                'version_received': version_received
            }
            
        except serial.SerialException as e:
            error_msg = f"Serial error: {str(e)}"
            print(f"ERROR: {error_msg}")
            return {
                'address': None,
                'version': None,
                'success': False,
                'error': error_msg
            }
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"ERROR: {error_msg}")
            return {
                'address': None,
                'version': None,
                'success': False,
                'error': error_msg
            }


def record_device_info(port, duration=5, baudrate=921600, gui_callback=None):
    """
    Convenience function to record device information.
    
    Args:
        port: Serial port to connect to
        duration: Recording duration in seconds (default: 5)
        baudrate: Serial baudrate (default: 921600)
        gui_callback: Function to call for GUI updates (optional)
        
    Returns:
        dict: Dictionary with device information
    """
    recorder = SerialRecorder(gui_callback)
    return recorder.record_device_info(port, duration, baudrate) 