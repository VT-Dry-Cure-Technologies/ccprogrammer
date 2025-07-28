#!/usr/bin/env python3
"""
Raspberry Pi FT232H Device Monitor
Monitors FT232H devices and displays connection status every second.
"""

import tkinter as tk
from tkinter import ttk, filedialog
import sys
import threading
import time
import argparse
from datetime import datetime
import re
from pathlib import Path

# Import USB detection module
from ccusb import USBDeviceDetector, scan_all_devices
from print_qr import QRPrinter

# Import flash module
from flash import ESP32Flasher

# Import serial module
from ccserial import SerialRecorder
from update import update_firmware, get_current_version_and_created_at

class FT232HMonitor:
    def __init__(self, root, auto_check=True):
        self.root = root
        self.root.title("CC2 Programmer")
        self.root.geometry("800x480")
        self.root.resizable(False, False)
        self.center_window()
        
        # Store auto_check setting
        self.auto_check = auto_check
        # if folder does not exist, create it
        self.folder_path = Path.home() / "firmwares" / "main"
        if not self.folder_path.exists():
            self.folder_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize USB detector, flasher, serial recorder, and QR printer
        self.usb_detector = USBDeviceDetector()
        self.flasher = ESP32Flasher()
        self.serial_recorder = SerialRecorder(self.gui_callback)
        self.qr_printer = QRPrinter()
        # Configure root grid
        root.columnconfigure(0, weight=1)
        root.rowconfigure(1, weight=1)
        root.rowconfigure(2, weight=0)  # For snackbar
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="20")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(1, weight=1)
        
        # Create title
        title_label = ttk.Label(self.main_frame, text="CC2 Programmer", font=('Arial', 20, 'bold'))
        title_label.grid(row=0, column=0, pady=(0, 5))

        # Add a frame to center version label and update button
        version_update_frame = ttk.Frame(self.main_frame)
        version_update_frame.grid(row=1, column=0, pady=(0, 0))

        # Add current version label (centered)
        current_version, current_created_at = get_current_version_and_created_at(self.folder_path)
        if isinstance(current_created_at, str):
            current_created_at_str = current_created_at
        else:
            current_created_at_str = current_created_at.strftime("%Y-%m-%d %H:%M:%S")
        self.version_label = ttk.Label(version_update_frame, text=f"Current Version: {current_version} ({current_created_at_str})", font=('Arial', 12))
        self.version_label.pack(side=tk.LEFT, padx=(0, 10))

        # Add folder picker button (centered)
        # Make the text not icon for linux
        folder_button = ttk.Button(version_update_frame, text="Firmware Folder", command=self.on_folder_clicked)
        folder_button.pack(side=tk.LEFT)

        # Add check for update button (centered)
        update_button = ttk.Button(version_update_frame, text="Download Latest", command=self.on_update_clicked)
        update_button.pack(side=tk.LEFT, padx=(0, 5))

        # Create status frame
        self.status_frame = ttk.Frame(self.main_frame)
        self.status_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.status_frame.columnconfigure(0, weight=1)
        
        # Create status and refresh button frame
        self.status_refresh_frame = ttk.Frame(self.status_frame)
        self.status_refresh_frame.grid(row=0, column=0, pady=10)
        
        # Device connection status
        self.status_label = ttk.Label(self.status_refresh_frame, text="Device not connected", font=('Arial', 16))
        self.status_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Refresh button (only shown when auto_check is False)
        self.refresh_button = ttk.Button(self.status_refresh_frame, text="Refresh", command=self.check_devices, width=10)
        if not self.auto_check:
            self.refresh_button.pack(side=tk.LEFT)
        
        # Dropdown and Get Serial button frame
        self.dropdown_frame = ttk.Frame(self.status_frame)
        self.dropdown_frame.grid(row=1, column=0, pady=(10, 10))
        self.dropdown_frame.grid_remove()  # Hidden by default
        style = ttk.Style()
        style.theme_use('clam')  
        style.configure("Big.TButton", font=('Arial', 14))
        style.configure(
            "Big.TCombobox",
            font=('Arial', 14),
            padding=(10, 10),  # (horizontal, vertical)
        )

        # Dropdown for FT232H TTY ports (only shown when connected)
        self.device_var = tk.StringVar()
        self.device_dropdown = ttk.Combobox(
            self.dropdown_frame,
            textvariable=self.device_var,
            state="readonly",
            width=25,
            style="Big.TCombobox"
        )
        self.device_dropdown.grid(row=0, column=0, padx=(0, 10))
        self.device_dropdown.bind("<<ComboboxSelected>>", self.on_device_selected)
        
        # Get Serial button
        self.get_serial_button = ttk.Button(self.dropdown_frame, text="Get Info", command=self.get_device_info, width=12, style="Big.TButton")
        self.get_serial_button.grid(row=0, column=1)
        
        # ESP32 Device Info (only shown when connected)
        self.device_info_frame = ttk.Frame(self.status_frame)
        self.device_info_frame.grid(row=2, column=0, pady=(10, 10))
        self.device_info_frame.grid_remove()  # Hidden by default
        
        # ESP32 Address
        self.address_label = ttk.Label(self.device_info_frame, text="Address: Not detected", font=('Arial', 12))
        self.address_label.grid(row=0, column=0, pady=(0, 5))
        
        # ESP32 Firmware Version
        self.firmware_label = ttk.Label(self.device_info_frame, text="Firmware: Not detected", font=('Arial', 12))
        self.firmware_label.grid(row=1, column=0, pady=(0, 10))
        
        # Action buttons (only shown when connected)
        self.button_frame = ttk.Frame(self.status_frame)
        self.button_frame.grid(row=3, column=0, pady=(10, 10))
        self.button_frame.grid_remove()  # Hidden by default

        # Flash button
        self.flash_button = ttk.Button(self.button_frame, text="Flash", command=self.flash_device, width=15, style="Big.TButton")
        self.flash_button.grid(row=0, column=0, padx=(0, 0))
        
        # Print button
        self.print_button = ttk.Button(self.button_frame, text="Print", width=15, style="Big.TButton", state="disabled")
        self.print_button.grid(row=0, column=1, padx=(30, 0))
        # Long-press detection for Print button
        self.print_press_time = None
        self.print_long_press_timer = None
        self.print_button.bind('<ButtonPress-1>', self.on_print_press)
        self.print_button.bind('<ButtonRelease-1>', self.on_print_release)

        # BT Test button
        self.bt_test_button = ttk.Button(self.button_frame, text="BT Test", command=self.bt_test, width=15, state="disabled", style="Big.TButton")
        self.bt_test_button.grid(row=0, column=2, padx=(30, 0))
        
        
        # Bind escape key
        self.root.bind('<Escape>', lambda e: self.root.quit())
        
        # Create snackbar frame (initially hidden)
        self.snackbar_frame = ttk.Frame(root, relief="solid", borderwidth=1)
        self.snackbar_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=20, pady=(0, 20))
        self.snackbar_frame.grid_remove()  # Hidden by default
        
        # Snackbar content
        self.snackbar_label = ttk.Label(self.snackbar_frame, text="", font=('Arial', 10), wraplength=500)
        self.snackbar_label.grid(row=0, column=0, padx=10, pady=5, sticky=(tk.W, tk.E))
        
        # Snackbar close button
        self.snackbar_close = ttk.Button(self.snackbar_frame, text="✕", width=3, command=self.hide_snackbar)
        self.snackbar_close.grid(row=0, column=1, padx=(0, 5), pady=5)
        
        # Configure snackbar frame columns
        self.snackbar_frame.columnconfigure(0, weight=1)
        
        # Snackbar auto-hide timer
        self.snackbar_timer = None
        
        # Device connected state
        self.device_connected = False
        
        # Start monitoring thread only if auto_check is True
        self.running = True
        if self.auto_check:
            self.monitor_thread = threading.Thread(target=self.monitor_devices, daemon=True)
            self.monitor_thread.start()
        
        # Initial check
        self.check_devices()
        
    def center_window(self):
        """Center the window on the screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def check_devices(self):
        """Check for FT232H devices using the USB detection module"""
        try:
            # Use the USB detection module to scan devices
            scan_result = scan_all_devices()
            
            ft232h_devices = scan_result['ft232h_devices']
            tty_devices = scan_result['tty_devices']
            
            # Update display with results
            self.update_display(ft232h_devices, tty_devices)
            
        except Exception as e:
            self.update_display([], [], error=f"Error: {str(e)}")
    
    def update_display(self, ft232h_devices, tty_devices, error=None):
        """Update the display with device information"""
        previous_device_connected = self.device_connected
        if error or not ft232h_devices:
            new_device_connected = False
            self.status_label.config(text="Device not connected", foreground="red")
            self.status_refresh_frame.grid(row=0, column=0, pady=10)
            self.hide_connected_elements()
        else:
            new_device_connected = True
            self.status_label.config(text="")  # Clear any text
            self.status_refresh_frame.grid(row=0, column=0, pady=1)
            self.show_connected_elements(tty_devices)

        if previous_device_connected != new_device_connected:
            self.clear_device_info()
            self.get_device_info()
        self.device_connected = new_device_connected
    
    def show_connected_elements(self, tty_devices):
        """Show elements when device is connected"""
        # Show dropdown frame
        self.device_dropdown['values'] = tty_devices
        if tty_devices:
            if not self.device_var.get() or self.device_var.get() not in tty_devices:
                self.device_var.set(tty_devices[0])
        self.dropdown_frame.grid()
        
        # Show device info
        self.device_info_frame.grid()
        
        # Show action buttons
        self.button_frame.grid()
    
    def hide_connected_elements(self):
        """Hide elements when device is not connected"""
        self.dropdown_frame.grid_remove()
        self.device_info_frame.grid_remove()
        self.button_frame.grid_remove()
        self.device_var.set('')
    
    def monitor_devices(self):
        """Monitor devices every second in a separate thread"""
        while self.running:
            time.sleep(1)
            # Use after() to update GUI from main thread
            self.root.after(0, self.check_devices)
    
    def on_device_selected(self, event):
        """Handle device selection from dropdown"""
        selected_port = self.device_var.get()
        self.show_snackbar(f"Selected port: {selected_port}")
    
    def gui_callback(self, field_type, value):
        """Callback function for GUI updates from serial recorder"""
        if field_type == 'address':
            self.address_label.config(text=f"Address: {value}")
            # Enable BT Test button if address is detected
            if value and value != "Not detected":
                self.bt_test_button.config(state="normal")
                self.print_button.config(state="normal")
            else:
                self.bt_test_button.config(state="disabled")
                self.print_button.config(state="disabled")
        elif field_type == 'version':
            self.firmware_label.config(text=f"Firmware: {value}")
    
    def clear_device_info(self):
        """Clear the address and firmware values"""
        self.address_label.config(text="Address: Not detected")
        self.firmware_label.config(text="Firmware: Not detected")
        self.bt_test_button.config(state="disabled")
        self.print_button.config(state="disabled")
    
    def get_device_info(self):
        """Get serial output from the selected device for 5 seconds"""
        selected_port = self.device_var.get()
        if selected_port:
            # Clear previous values
            self.clear_device_info()
            
            # Disable button during recording
            self.get_serial_button.config(state="disabled", text="Getting Info...")
            self.root.update()
            
            # Start recording in a separate thread
            recording_thread = threading.Thread(target=self._record_serial, args=(selected_port,), daemon=True)
            recording_thread.start()
        else:
            self.show_snackbar("No device selected for serial recording", "warning")
    
    def _record_serial(self, port):
        """Record serial output for 5 seconds"""
        try:
            # Use the serial recorder to get device information
            result = self.serial_recorder.record_device_info(port, duration=10, baudrate=921600)
            
            # Update GUI from main thread
            self.root.after(0, lambda: self.get_serial_button.config(state="normal", text="Get Info"))
            
            # Check if we received both values
            if result['success']:
                # self.root.after(0, lambda: self.show_snackbar("Device information received successfully", "success"))
                pass
            else:
                self.root.after(0, lambda: self.show_snackbar("Information not received", "warning"))
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"ERROR: {error_msg}")
            self.root.after(0, lambda: self.get_serial_button.config(state="normal", text="Get Info"))
            self.root.after(0, lambda: self.show_snackbar(error_msg, "error"))
    
    def flash_device(self):
        """Flash the connected device"""
        selected_port = self.device_var.get()
        if selected_port:
            self.show_snackbar(f"Flashing device on port: {selected_port}")
            
            # Disable flash button during flashing
            self.flash_button.config(state="disabled", text="Flashing...")
            self.root.update()
            
            try:
                # Perform the flashing
                success, message = self.flasher.flash_device(selected_port)
                
                if success:
                    self.show_snackbar("✅ " + message, "success")
                else:
                    self.show_snackbar("❌ " + message, "error")
                    
            except Exception as e:
                self.show_snackbar(f"❌ Error during flashing: {str(e)}", "error")
            finally:
                # Re-enable flash button
                self.flash_button.config(state="normal", text="Flash")
        else:
            self.show_snackbar("No device selected for flashing", "warning")
    
    def print_qr_code(self, number_of_prints=1):
        """Print the device's QR code"""
        address = self.address_label.cget("text").split(": ")[1]
        if address != "Not detected":
            self.show_snackbar(f"Printing QR code for device: {address}")
            print(f"Printer connected: {self.qr_printer.is_connected()}")
            # Connect to printer if not already connected
            if not self.qr_printer.is_connected():
                if not self.qr_printer.connect():
                    self.show_snackbar("Printer not found", "error")
                    return
            
            # Print the QR code
            message = self.qr_printer.print_qr_code(address, number_of_prints)
            print(f"Print result: {message}")
            if message == "Success":
                self.show_snackbar(message, "success")
            else:
                print(f"Showing error snackbar: {message}")
                self.show_snackbar(message, "error")
        else:
            self.show_snackbar("No address detected, cannot print QR code", "warning")
    
    def on_print_press(self, event):
        import time
        self.print_press_time = time.time()
        self.print_long_press_timer = self.root.after(1500, self.print_qr_code_long_press)

    def on_print_release(self, event):
        import time
        if self.print_long_press_timer:
            self.root.after_cancel(self.print_long_press_timer)
            self.print_long_press_timer = None
        if self.print_press_time:
            held_time = time.time() - self.print_press_time
            if held_time < 1.5:
                self.print_qr_code()
        self.print_press_time = None

    def print_qr_code_long_press(self):
        self.print_long_press_timer = None
        self.print_qr_code(3)
        # Implement alternate action here

    def bt_test(self):
        """Test for BLE device with the given address as deviceId"""
        address_text = self.address_label.cget("text")
        if address_text.startswith("Address: "):
            device_id = address_text.split(": ", 1)[1]
            if device_id and device_id != "Not detected":
                self.bt_test_button.config(state="disabled", text="Testing...")
                self.root.update()
                def run_bt_test():
                    import asyncio
                    from bluetooth_scanner import scan_for_my_devices
                    try:
                        found, rssi = asyncio.run(scan_for_my_devices(5, device_id))
                        print(f"BT Test result: found={found}, rssi={rssi}")
                        msg = "BT Device NOT FOUND"
                        msg_type = "error"
                        if found:
                            if rssi >  -45:
                                msg = "BT Device FOUND with good signal: " + str(rssi) + "dBm"
                                msg_type = "success"
                            else:
                                msg = "BT Device FOUND with poor signal: " + str(rssi) + "dBm"
                                msg_type = "warning"
                    except Exception as e:
                        msg = f"BT Test error: {e}"
                        msg_type = "error"
                    self.root.after(0, lambda: self.bt_test_button.config(state="normal", text="BT Test"))
                    self.root.after(0, lambda: self.show_snackbar(msg, msg_type))
                threading.Thread(target=run_bt_test, daemon=True).start()
    
    def show_snackbar(self, message, message_type="info"):
        """Show a snackbar notification"""
        # Cancel any existing timer
        if self.snackbar_timer:
            self.root.after_cancel(self.snackbar_timer)
        
        # Set message and color based on type
        self.snackbar_label.config(text=message)
        
        if message_type == "success":
            self.snackbar_frame.config(style="Success.TFrame")
            self.snackbar_label.config(foreground="green")
        elif message_type == "error":
            self.snackbar_frame.config(style="Error.TFrame")
            self.snackbar_label.config(foreground="red")
        elif message_type == "warning":
            self.snackbar_frame.config(style="Warning.TFrame")
            self.snackbar_label.config(foreground="orange")
        else:
            self.snackbar_frame.config(style="TFrame")
            self.snackbar_label.config(foreground="black")
        
        # Show the snackbar
        self.snackbar_frame.grid()
        
        # Auto-hide after 5 seconds
        self.snackbar_timer = self.root.after(5000, self.hide_snackbar)
    
    def hide_snackbar(self):
        """Hide the snackbar notification"""
        self.snackbar_frame.grid_remove()
        if self.snackbar_timer:
            self.root.after_cancel(self.snackbar_timer)
            self.snackbar_timer = None
    
    def on_update_clicked(self):
        def run_update():
            try:
                self.show_snackbar("Updating firmware...", "info")
                message = update_firmware(self.folder_path)
                if message == "Success":
                    self.show_snackbar("Firmware update complete!", "success")
                    current_version, current_created_at = get_current_version_and_created_at(self.folder_path)
                    if isinstance(current_created_at, str):
                        current_created_at_str = current_created_at
                    else:
                        current_created_at_str = current_created_at.strftime("%Y-%m-%d %H:%M:%S")
                    self.version_label.config(text=f"Current Version: {current_version} ({current_created_at_str})")
                else:
                    self.show_snackbar(message, "error")
            except Exception as e:
                self.show_snackbar(f"Update failed: {str(e)}", "error")
        threading.Thread(target=run_update, daemon=True).start()

    def on_folder_clicked(self):
        """Open a folder picker dialog and set firmware directory"""
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.folder_path = Path(folder_path) 
            current_version, current_created_at = get_current_version_and_created_at(self.folder_path)
            if isinstance(current_created_at, str):
                current_created_at_str = current_created_at
            else:
                current_created_at_str = current_created_at.strftime("%Y-%m-%d %H:%M:%S")
            self.version_label.config(text=f"Current Version: {current_version} ({current_created_at_str})")
            self.flasher.set_firmware_dir(folder_path)
            self.show_snackbar(f"Firmware directory set to: {folder_path}", "success")

    def on_closing(self):
        """Handle window closing"""
        self.running = False
        # Disconnect from printer if connected
        if self.qr_printer.is_connected:
            self.qr_printer.disconnect()
        self.root.quit()

def main():
    """Main function to run the application"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='CC2 Programmer - FT232 Device Monitor')
    parser.add_argument('-no-auto-check', action='store_true', 
                       help='Disable automatic device checking and add manual refresh button')
    args = parser.parse_args()
    
    # Determine auto_check setting
    if args.no_auto_check:
        auto_check = False
    else:
        if sys.platform.startswith('win'):
            auto_check = False
        else:
            auto_check = True
    
    try:
        root = tk.Tk()
        app = FT232HMonitor(root, auto_check=auto_check)
        
        # Handle window closing
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        
        
        root.mainloop()
        
    except KeyboardInterrupt:
        print("\nApplication interrupted by user.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
