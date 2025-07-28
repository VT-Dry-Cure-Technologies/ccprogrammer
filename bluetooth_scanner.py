#!/usr/bin/env python3
"""
Bluetooth scanner module for detecting specific devices using bleak.
Handles Bluetooth Low Energy (BLE) scanning and device detection.
"""

import asyncio
import time
from typing import Optional, Tuple
from bleak import BleakScanner
from bleak.backends.scanner import AdvertisementData


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
                    print(f"  - {device.name} ({device.address})")
                    
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


def parse_manufacturer_data(manufacturer_data):
    """
    Parse manufacturer data to extract deviceId.
    Assumes deviceId is stored as a string after 2 bytes of manufacturer id.
    """
    # Example: {0xFFFF: b'\x12\x34DEVICEID'}
    for key, value in manufacturer_data.items():
        if len(value) > 2:
            # DeviceId is after the first 2 bytes
            try:
                device_id = value[2:].decode(errors='replace')
                return device_id
            except Exception:
                continue
    return None

async def scan_for_my_devices(timeout=5, deviceId=None):
    """
    Scan for BLE devices advertising service data with UUID FFF1, return (True, RSSI) if deviceId is found, else (False, None) after timeout.
    """
    TARGET_SERVICE_DATA_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"
    print(f"Scanning for BLE devices advertising service data UUID {TARGET_SERVICE_DATA_UUID} and deviceId {deviceId}")
    found = False
    rssi_value = None
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def detection_callback(device, adv):
        nonlocal found, rssi_value
        service_data = adv.service_data if hasattr(adv, 'service_data') else {}
        if TARGET_SERVICE_DATA_UUID not in service_data:
            return
        device_id_bytes = service_data[TARGET_SERVICE_DATA_UUID]
        try:
            adv_device_id = device_id_bytes.decode(errors='replace')
        except Exception:
            adv_device_id = device_id_bytes.hex()
        # Compare case-insensitive, ignore colons
        adv_device_id_clean = adv_device_id.replace(":", "").upper()
        target_device_id_clean = deviceId.replace(":", "").upper() if deviceId else None
        if adv_device_id_clean == target_device_id_clean:
            rssi = adv.rssi if hasattr(adv, 'rssi') else None
            rssi_display = rssi if rssi is not None else 'N/A'
            print(f"Device found: Address={device.address}, DeviceId={adv_device_id}, RSSI={rssi_display}dBm")
            found = True
            rssi_value = rssi
            # Stop the scanner and set the event
            loop.create_task(scanner.stop())
            stop_event.set()

    scanner = BleakScanner(detection_callback)
    await scanner.start()
    try:
        await asyncio.wait_for(stop_event.wait(), timeout=timeout)
    except asyncio.TimeoutError:
        await scanner.stop()
    return (found, rssi_value)


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


# For manual testing
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2 and sys.argv[1] == "mydevices":
        device_id = sys.argv[2]
        result = asyncio.run(scan_for_my_devices(5, device_id))
        print("FOUND" if result else "NOT FOUND")
    else:
        # Test the scanner
        print("Bluetooth Device Scanner (using bleak)")
        print("=" * 40)
        
        success, address = scan_for_printer(5)
        
        if success:
            print(f"\nSUCCESS: Device found at {address}")
        else:
            print(f"\nFAILED: Device not found within timeout period") 