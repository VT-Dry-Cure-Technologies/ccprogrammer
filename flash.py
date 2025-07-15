#!/usr/bin/env python3
"""
ESP32 Flashing Module
Handles flashing ESP32 devices using esptool.
"""

import subprocess
import os
import sys
from pathlib import Path
import esptool

class ESP32Flasher:
    def __init__(self):
        self.firmware_dir = Path(__file__).parent / "firmware"

    def flash_device(self, port):
        """
        Flash ESP32 device using esptool library
        Args:
            port (str): The TTY port (e.g., '/dev/ttyUSB0')
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            # Check if firmware files exist
            if not self.firmware_dir.exists():
                return False, f"Firmware directory not found: {self.firmware_dir}"

            # Define firmware file paths
            bootloader_bin = self.firmware_dir / "CC2_Operation.ino.bootloader.bin"
            partitions_bin = self.firmware_dir / "CC2_Operation.ino.partitions.bin"
            firmware_bin = self.firmware_dir / "CC2_Operation.ino.bin"
            filesystem_bin = self.firmware_dir / "CC2_Operation.ino.filesystem.bin"

            # Check if all required files exist
            required_files = [bootloader_bin, partitions_bin, firmware_bin, filesystem_bin]
            missing_files = [f.name for f in required_files if not f.exists()]

            if missing_files:
                return False, f"Missing firmware files: {', '.join(missing_files)}"

            args = [
                '--chip', 'esp32s3',
                '--port', port,
                '--baud', '921600',
                '--before', 'default-reset',
                '--after', 'hard-reset',
                'write_flash', '-z',
                '0x0000', str(bootloader_bin),
                '0x8000', str(partitions_bin),
                '0x10000', str(firmware_bin),
                '0x210000', str(filesystem_bin)
            ]

            print(f"Flashing device on port: {port}")
            print(f"esptool args: {' '.join(args)}")

            try:
                esptool.main(args)
                return True, "Flashing completed successfully!"
            except SystemExit as e:
                if e.code == 0:
                    return True, "Flashing completed successfully!"
                else:
                    return False, f"Flashing failed with exit code {e.code}"
        except Exception as e:
            return False, f"Error during flashing: {str(e)}"

    def check_esptool_available(self):
        """
        Check if esptool is available as a Python module
        Returns:
            bool: True if esptool is importable, False otherwise
        """
        try:
            import esptool
            return True
        except ImportError:
            return False
    
    def get_firmware_info(self):
        """
        Get information about available firmware files
        
        Returns:
            dict: Information about firmware files
        """
        info = {
            "firmware_dir": str(self.firmware_dir),
            "dir_exists": self.firmware_dir.exists(),
            "files": {}
        }
        
        if self.firmware_dir.exists():
            firmware_files = [
                "CC2_Operation.ino.bootloader.bin",
                "CC2_Operation.ino.partitions.bin", 
                "CC2_Operation.ino.bin",
                "CC2_Operation.ino.filesystem.bin"
            ]
            
            for file_name in firmware_files:
                file_path = self.firmware_dir / file_name
                info["files"][file_name] = {
                    "exists": file_path.exists(),
                    "size": file_path.stat().st_size if file_path.exists() else 0
                }
        
        return info

def main():
    """Test function for the flasher"""
    flasher = ESP32Flasher()
    
    # Check esptool availability
    if not flasher.check_esptool_available():
        print("❌ esptool not found. Please install esptool or activate the correct virtual environment.")
        return
    
    print("✅ esptool is available")
    
    # Get firmware info
    firmware_info = flasher.get_firmware_info()
    print(f"\nFirmware directory: {firmware_info['firmware_dir']}")
    print(f"Directory exists: {firmware_info['dir_exists']}")
    
    if firmware_info['dir_exists']:
        print("\nFirmware files:")
        for file_name, file_info in firmware_info['files'].items():
            status = "✅" if file_info['exists'] else "❌"
            size_mb = file_info['size'] / (1024 * 1024) if file_info['size'] > 0 else 0
            print(f"  {status} {file_name} ({size_mb:.2f} MB)")
    
    # Test with a port (you would need to provide an actual port)
    if len(sys.argv) > 1:
        port = sys.argv[1]
        print(f"\nTesting flash on port: {port}")
        success, message = flasher.flash_device(port)
        print(f"Result: {'✅' if success else '❌'} {message}")

if __name__ == "__main__":
    main() 