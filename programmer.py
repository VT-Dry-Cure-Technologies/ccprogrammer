#!/usr/bin/env python3
"""
Raspberry Pi FT232H Device Monitor
Monitors FT232H devices and displays connection status every second.
"""

import tkinter as tk
from tkinter import ttk
import sys
import threading
import time
from datetime import datetime

# Import USB detection module
from usb import USBDeviceDetector, scan_all_devices

class FT232HMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("FT232H Device Monitor")
        self.root.geometry("800x480")
        self.root.resizable(False, False)
        self.center_window()
        
        # Initialize USB detector
        self.usb_detector = USBDeviceDetector()
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="20")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(1, weight=1)
        
        # Create title
        title_label = ttk.Label(self.main_frame, text="FT232H Device Monitor", font=('Arial', 20, 'bold'))
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # Create status frame
        self.status_frame = ttk.Frame(self.main_frame)
        self.status_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.status_frame.columnconfigure(0, weight=1)
        
        # Device connection status
        self.status_label = ttk.Label(self.status_frame, text="Device not connected", font=('Arial', 16))
        self.status_label.grid(row=0, column=0, pady=10)
        
        # Dropdown for FT232H TTY ports (only shown when connected)
        self.device_var = tk.StringVar()
        self.device_dropdown = ttk.Combobox(self.status_frame, textvariable=self.device_var, state="readonly", font=('Arial', 12), width=25)
        self.device_dropdown.grid(row=1, column=0, pady=(10, 10))
        self.device_dropdown.bind("<<ComboboxSelected>>", self.on_device_selected)
        self.device_dropdown.grid_remove()  # Hidden by default
        
        # ESP32 Device Info (only shown when connected)
        self.device_info_frame = ttk.Frame(self.status_frame)
        self.device_info_frame.grid(row=2, column=0, pady=(10, 10))
        self.device_info_frame.grid_remove()  # Hidden by default
        
        # ESP32 Address
        self.address_label = ttk.Label(self.device_info_frame, text="Address: E4B13797BACC", font=('Arial', 12))
        self.address_label.grid(row=0, column=0, pady=(0, 5))
        
        # ESP32 Firmware Version
        self.firmware_label = ttk.Label(self.device_info_frame, text="Firmware: 1.12", font=('Arial', 12))
        self.firmware_label.grid(row=1, column=0, pady=(0, 10))
        
        # Action buttons (only shown when connected)
        self.button_frame = ttk.Frame(self.status_frame)
        self.button_frame.grid(row=3, column=0, pady=(10, 10))
        self.button_frame.grid_remove()  # Hidden by default
        
        # Flash button
        self.flash_button = ttk.Button(self.button_frame, text="Flash", command=self.flash_device, width=15)
        self.flash_button.grid(row=0, column=0, padx=(0, 10))
        
        # Print button
        self.print_button = ttk.Button(self.button_frame, text="Print", command=self.print_qr_code, width=15)
        self.print_button.grid(row=0, column=1, padx=(10, 0))
        
        # Exit button
        exit_button = ttk.Button(self.main_frame, text="Exit", command=self.root.quit)
        exit_button.grid(row=2, column=0, pady=(20, 0))
        
        # Bind escape key
        self.root.bind('<Escape>', lambda e: self.root.quit())
        
        # Start monitoring thread
        self.running = True
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
        if error:
            self.status_label.config(text="Device not connected", foreground="red")
            self.hide_connected_elements()
        elif ft232h_devices:
            self.status_label.config(text="Device connected", foreground="green")
            self.show_connected_elements(tty_devices)
        else:
            self.status_label.config(text="Device not connected", foreground="red")
            self.hide_connected_elements()
    
    def show_connected_elements(self, tty_devices):
        """Show elements when device is connected"""
        # Show dropdown
        self.device_dropdown['values'] = tty_devices
        if tty_devices:
            if not self.device_var.get() or self.device_var.get() not in tty_devices:
                self.device_var.set(tty_devices[0])
        self.device_dropdown.grid()
        
        # Show device info
        self.device_info_frame.grid()
        
        # Show action buttons
        self.button_frame.grid()
    
    def hide_connected_elements(self):
        """Hide elements when device is not connected"""
        self.device_dropdown.grid_remove()
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
        print(f"Selected port: {selected_port}")
    
    def flash_device(self):
        """Flash the connected device"""
        selected_port = self.device_var.get()
        if selected_port:
            print(f"Flashing device on port: {selected_port}")
            # TODO: Implement actual flashing logic
        else:
            print("No device selected for flashing")
    
    def print_qr_code(self):
        """Print the device's QR code"""
        selected_port = self.device_var.get()
        if selected_port:
            print(f"Printing QR code for device on port: {selected_port}")
            # TODO: Implement actual QR code printing logic
        else:
            print("No device selected for printing")
    
    def on_closing(self):
        """Handle window closing"""
        self.running = False
        self.root.quit()

def main():
    """Main function to run the application"""
    try:
        root = tk.Tk()
        app = FT232HMonitor(root)
        
        # Handle window closing
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        
        print("FT232H Device Monitor started. Checking devices every second...")
        print("Press ESC or click Exit to close.")
        sys.stdout.flush()
        
        root.mainloop()
        
    except KeyboardInterrupt:
        print("\nApplication interrupted by user.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 