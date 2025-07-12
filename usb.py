#!/usr/bin/env python3
"""
USB Device Detection Module
Handles detection and verification of FT232H devices
"""

import subprocess
import time

class USBDeviceDetector:
    """Class for detecting and managing USB devices, specifically FT232H"""
    
    def __init__(self):
        self.ft232h_vendor_id = "0403"
        self.ft232h_product_id = "6014"
    
    def check_ft232h_devices(self):
        """Check for FT232H devices using lsusb"""
        try:
            result = subprocess.run(['lsusb'], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                ft232h_devices = []
                lines = result.stdout.split('\n')
                
                for line in lines:
                    if f'{self.ft232h_vendor_id}:{self.ft232h_product_id}' in line or 'FT232H' in line:
                        ft232h_devices.append(line.strip())
                
                return ft232h_devices
            else:
                return []
                
        except subprocess.TimeoutExpired:
            print("Device check timeout")
            return []
        except Exception as e:
            print(f"Error checking devices: {e}")
            return []
    
    def find_ft232h_tty_devices(self):
        """Find tty devices specifically for FT232H devices"""
        try:
            ft232h_tty_devices = []
            
            # Method 1: Use udevadm to check all ttyUSB devices for FT232H
            try:
                result = subprocess.run('ls /dev/ttyUSB*', shell=True, capture_output=True, text=True, timeout=3)
                if result.returncode == 0:
                    for tty_device in result.stdout.strip().split('\n'):
                        if tty_device:
                            udev_result = subprocess.run(['udevadm', 'info', '--name', tty_device, '--query', 'property'], 
                                                       capture_output=True, text=True, timeout=3)
                            
                            if udev_result.returncode == 0:
                                udev_output = udev_result.stdout
                                if (f'ID_VENDOR_ID={self.ft232h_vendor_id}' in udev_output and 
                                    f'ID_MODEL_ID={self.ft232h_product_id}' in udev_output):
                                    ft232h_tty_devices.append(tty_device)
            except Exception as e:
                print(f"Method 1 failed: {e}")
            
            # Method 2: Fallback - if we found FT232H devices but no TTY, show all ttyUSB
            if not ft232h_tty_devices:
                try:
                    result = subprocess.run('ls /dev/ttyUSB*', shell=True, capture_output=True, text=True, timeout=3)
                    if result.returncode == 0:
                        for line in result.stdout.strip().split('\n'):
                            if line.strip():
                                ft232h_tty_devices.append(line.strip())
                except Exception as e:
                    print(f"Method 2 failed: {e}")
            
            return ft232h_tty_devices
            
        except Exception as e:
            print(f"Error finding TTY devices: {e}")
            return []
    
    def verify_ft232h_device(self, tty_device):
        """Verify that a TTY device is actually an FT232H"""
        try:
            result = subprocess.run(['udevadm', 'info', '--name', tty_device, '--query', 'property'], 
                                  capture_output=True, text=True, timeout=3)
            
            if result.returncode == 0:
                output = result.stdout
                if (f'ID_VENDOR_ID={self.ft232h_vendor_id}' in output and 
                    f'ID_MODEL_ID={self.ft232h_product_id}' in output):
                    return True
            
            return False
        except:
            return False
    
    def get_device_info(self, tty_device):
        """Get detailed information about a TTY device"""
        try:
            result = subprocess.run(['udevadm', 'info', '--name', tty_device, '--query', 'property'], 
                                  capture_output=True, text=True, timeout=3)
            
            if result.returncode == 0:
                return result.stdout
            return ""
        except:
            return ""
    
    def scan_devices(self):
        """Scan for all FT232H devices and their TTY ports"""
        ft232h_devices = self.check_ft232h_devices()
        tty_devices = self.find_ft232h_tty_devices()
        
        return {
            'ft232h_devices': ft232h_devices,
            'tty_devices': tty_devices,
            'connected': len(ft232h_devices) > 0,
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
        }

# Convenience functions for easy access
def get_ft232h_devices():
    """Get list of FT232H devices"""
    detector = USBDeviceDetector()
    return detector.check_ft232h_devices()

def get_ft232h_tty_ports():
    """Get list of FT232H TTY ports"""
    detector = USBDeviceDetector()
    return detector.find_ft232h_tty_devices()

def verify_device(tty_device):
    """Verify if a TTY device is an FT232H"""
    detector = USBDeviceDetector()
    return detector.verify_ft232h_device(tty_device)

def scan_all_devices():
    """Scan for all FT232H devices and return complete info"""
    detector = USBDeviceDetector()
    return detector.scan_devices() 