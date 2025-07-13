#!/usr/bin/env python3
"""
Bluetooth scanner module for detecting specific devices using bleak.
Handles Bluetooth Low Energy (BLE) scanning and device detection.
"""

import asyncio
import time
from typing import Optional, Tuple
from bleak import BleakScanner


class BluetoothScanner:
    def __init__(self):
        """Initialize the Bluetooth scanner."""
        self.target_device_name = "Printer001"
    
    async def scan_for_device_async(self, timeout=5) -> Tuple[bool, Optional[str]]:
        """
        Scan for the target Bluetooth device using bleak.
        
        Args:
            timeout: Maximum time to scan in seconds (default: 5)
            
        Returns:
            Tuple of (success: bool, device_address: Optional[str])
        """
        try:
            print(f"Scanning for device: {self.target_device_name})")
            print(f"Timeout: {timeout} seconds")
            print("Starting BLE scan...")
            
            # Use a simpler approach with shorter intervals
            scanner = BleakScanner()
            start_time = time.time()
            
            while (time.time() - start_time) < timeout:
                # Scan for a short interval
                devices = await scanner.discover(timeout=0.5)
                
                for device in devices:
                    # print(f"  - {device.name} ({device.address})")
                    
                    # Check if this is our target device
                    if (device.name == self.target_device_name):
                        print(f"✓ Target device found: {device.name} ({device.address})")
                        return True, device.address
            
            print(f"✗ Target device not found within {timeout} seconds")
            return False, None
            
        except Exception as e:
            print(f"Error during BLE scan: {e}")
            return False, None
    
    def scan_for_device(self, timeout=5) -> Tuple[bool, Optional[str]]:
        """
        Synchronous wrapper for the async scan function.
        
        Args:
            timeout: Maximum time to scan in seconds (default: 5)
            
        Returns:
            Tuple of (success: bool, device_address: Optional[str])
        """
        try:
            return asyncio.run(self.scan_for_device_async(timeout))
        except Exception as e:
            print(f"Error running async scan: {e}")
            return False, None


def scan_for_printer(timeout=5) -> Tuple[bool, Optional[str]]:
    """
    Convenience function to scan for Printer001 device.
    
    Args:
        timeout: Maximum time to scan in seconds (default: 5)
        
    Returns:
        Tuple of (success: bool, device_address: Optional[str])
    """
    scanner = BluetoothScanner()
    return scanner.scan_for_device(timeout)


async def scan_for_printer_async(timeout=5) -> Tuple[bool, Optional[str]]:
    """
    Async convenience function to scan for Printer001 device.
    
    Args:
        timeout: Maximum time to scan in seconds (default: 5)
        
    Returns:
        Tuple of (success: bool, device_address: Optional[str])
    """
    scanner = BluetoothScanner()
    return await scanner.scan_for_device_async(timeout)


if __name__ == "__main__":
    # Test the scanner
    print("Bluetooth Device Scanner (using bleak)")
    print("=" * 40)
    
    success, address = scan_for_printer(5)
    
    if success:
        print(f"\nSUCCESS: Device found at {address}")
    else:
        print(f"\nFAILED: Device not found within timeout period") 