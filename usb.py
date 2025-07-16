#!/usr/bin/env python3
"""
USB Device Detection Module
Handles detection and verification of FT232H devices on Linux and Windows
"""

import subprocess
import time
import platform
try:
    import serial.tools.list_ports
except ImportError:
    serial = None
try:
    import wmi
except ImportError:
    wmi = None

class USBDeviceDetector:
    """Class for detecting and managing USB devices, specifically FT232H"""
    
    def __init__(self):
        self.ft232h_vendor_id = "0403"
        self.ft232h_product_id = "6014"
        self.is_windows = platform.system() == "Windows"
    
    def check_ft232h_devices(self):
        """Check for FT232H devices using platform-appropriate method"""
        if self.is_windows:
            return self._check_ft232h_windows()
        else:
            return self._check_ft232h_linux()
    
    def _check_ft232h_linux(self):
        """Check for FT232H devices using lsusb (Linux)"""
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
                print("lsusb command failed")
                return []
                
        except subprocess.TimeoutExpired:
            print("Device check timeout")
            return []
        except Exception as e:
            print(f"Error checking Linux devices: {e}")
            return []
    
    def _check_ft232h_windows(self):
        """Check for FT232H devices using WMI (Windows)"""
        if not wmi:
            print("wmi not installed. Please install it using 'pip install wmi'")
            return []
        
        try:
            ft232h_devices = []
            c = wmi.WMI()
            for device in c.Win32_PnPEntity():
                if (device.DeviceID and 
                    self.ft232h_vendor_id.upper() in device.DeviceID and 
                    self.ft232h_product_id.upper() in device.DeviceID):
                    status = device.Status if device.Status else "Unknown"
                    device_info = f"FT232H USB Device: {device.Name} (DeviceID: {device.DeviceID}, Status: {status})"
                    ft232h_devices.append(device_info)
            if not ft232h_devices:
                print("No FT232H devices found via WMI. Check Device Manager for 'Other devices' or 'Universal Serial Bus controllers'.")
            return ft232h_devices
        except Exception as e:
            print(f"Error checking Windows devices: {e}. Try running the script as Administrator.")
            return []
    
    def find_ft232h_tty_devices(self):
        """Find tty/COM devices specifically for FT232H devices"""
        if self.is_windows:
            return self._find_ft232h_com_windows()
        else:
            return self._find_ft232h_tty_linux()
    
    def _find_ft232h_tty_linux(self):
        """Find tty devices specifically for FT232H devices (Linux)"""
        try:
            ft232h_tty_devices = []
            
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
                print(f"Linux TTY Method 1 failed: {e}")
            
            if not ft232h_tty_devices:
                try:
                    result = subprocess.run('ls /dev/ttyUSB*', shell=True, capture_output=True, text=True, timeout=3)
                    if result.returncode == 0:
                        for line in result.stdout.strip().split('\n'):
                            if line.strip():
                                ft232h_tty_devices.append(line.strip())
                except Exception as e:
                    print(f"Linux TTY Method 2 failed: {e}")
            
            return ft232h_tty_devices
            
        except Exception as e:
            print(f"Error finding TTY devices: {e}")
            return []
    
    def _find_ft232h_com_windows(self):
        """Find COM ports for FT232H devices (Windows)"""
        if not serial:
            print("pyserial not installed. Please install it using 'pip install pyserial'")
            return []
        
        try:
            ft232h_com_ports = []
            ports = serial.tools.list_ports.comports()
            for port in ports:
                if port.vid == int(self.ft232h_vendor_id, 16) and port.pid == int(self.ft232h_product_id, 16):
                    ft232h_com_ports.append(port.device)
                print(f"Found COM port: {port.device} (VID: {port.vid}, PID: {port.pid}, Description: {port.description})")
            if not ft232h_com_ports:
                print("No FT232H COM ports found. Available COM ports:")
                for port in ports:
                    print(f" - {port.device} (VID: {port.vid}, PID: {port.pid})")
                if not ports:
                    print("No COM ports detected. Ensure the FTDI VCP driver (ftser2k.sys) is installed correctly.")
                    print("Steps to resolve:")
                    print("1. Unplug the FT232H device.")
                    print("2. Uninstall existing FTDI drivers using CDM Uninstaller from https://ftdichip.com/support/utilities/.")
                    print("3. Download the ARM64 driver (e.g., CDM-v2.12.36.4-WHQL-Certified.zip) from https://ftdichip.com/drivers/vcp-drivers/.")
                    print("4. Extract the ZIP and manually install 'ftdiport.inf' via Device Manager.")
                    print("5. Plug in the device and verify 'USB Serial Port (COMx)' in Device Manager.")
                    print("6. Try a different USB port (preferably USB 2.0) or another PC.")
            return ft232h_com_ports
        except Exception as e:
            print(f"Error finding COM ports: {e}")
            return []
    
    def verify_ft232h_device(self, tty_device):
        """Verify that a TTY/COM device is actually an FT232H"""
        if self.is_windows:
            return self._verify_ft232h_windows(tty_device)
        else:
            return self._verify_ft232h_linux(tty_device)
    
    def _verify_ft232h_linux(self, tty_device):
        """Verify that a TTY device is actually an FT232H (Linux)"""
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
    
    def _verify_ft232h_windows(self, com_port):
        """Verify that a COM port is actually an FT232H (Windows)"""
        if not serial:
            print("pyserial not installed. Please install it using 'pip install pyserial'")
            return False
        
        try:
            ports = serial.tools.list_ports.comports()
            for port in ports:
                if port.device == com_port and port.vid == int(self.ft232h_vendor_id, 16) and port.pid == int(self.ft232h_product_id, 16):
                    return True
            print(f"COM port {com_port} not verified as FT232H.")
            return False
        except Exception as e:
            print(f"Error verifying COM port {com_port}: {e}")
            return False
    
    def get_device_info(self, tty_device):
        """Get detailed information about a TTY/COM device"""
        if self.is_windows:
            return self._get_device_info_windows(tty_device)
        else:
            return self._get_device_info_linux(tty_device)
    
    def _get_device_info_linux(self, tty_device):
        """Get detailed information about a TTY device (Linux)"""
        try:
            result = subprocess.run(['udevadm', 'info', '--name', tty_device, '--query', 'property'], 
                                  capture_output=True, text=True, timeout=3)
            
            if result.returncode == 0:
                return result.stdout
            return ""
        except:
            return ""
    
    def _get_device_info_windows(self, com_port):
        """Get detailed information about a COM port (Windows)"""
        if not serial:
            print("pyserial not installed. Please install it using 'pip install pyserial'")
            return ""
        
        try:
            ports = serial.tools.list_ports.comports()
            for port in ports:
                if port.device == com_port:
                    info = f"Name: {port.description}\n"
                    info += f"DeviceID: {port.device}\n"
                    info += f"VID: {port.vid}\n"
                    info += f"PID: {port.pid}\n"
                    info += f"Serial Number: {port.serial_number}\n"
                    info += f"Manufacturer: {port.manufacturer}\n"
                    return info
            return f"No device info found for {com_port}"
        except Exception as e:
            return f"Error getting device info for {com_port}: {e}"
    
    def scan_devices(self):
        """Scan for all FT232H devices and their TTY/COM ports"""
        ft232h_devices = self.check_ft232h_devices()
        tty_devices = self.find_ft232h_tty_devices()
        
        return {
            'ft232h_devices': ft232h_devices,
            'tty_devices': tty_devices,
            'connected': len(ft232h_devices) > 0 or len(tty_devices) > 0,
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
        }

# Convenience functions for easy access
def get_ft232h_devices():
    """Get list of FT232H devices"""
    detector = USBDeviceDetector()
    return detector.check_ft232h_devices()

def get_ft232h_tty_ports():
    """Get list of FT232H TTY/COM ports"""
    detector = USBDeviceDetector()
    return detector.find_ft232h_tty_devices()

def verify_device(tty_device):
    """Verify if a TTY/COM device is an FT232H"""
    detector = USBDeviceDetector()
    return detector.verify_ft232h_device(tty_device)

def scan_all_devices():
    """Scan for all FT232H devices and return complete info"""
    detector = USBDeviceDetector()
    return detector.scan_devices()

if __name__ == "__main__":
    detector = USBDeviceDetector()
    result = detector.scan_devices()
    print(f"Scan result: {result}")