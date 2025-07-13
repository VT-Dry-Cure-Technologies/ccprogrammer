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
from print_qr import print_qr_code

# Import flash module
from flash import ESP32Flasher

class FT232HMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("FT232H Device Monitor")
        self.root.geometry("800x480")
        self.root.resizable(False, False)
        self.center_window()
        
        # Initialize USB detector and flasher
        self.usb_detector = USBDeviceDetector()
        self.flasher = ESP32Flasher()
        
        # Configure root grid
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        root.rowconfigure(1, weight=0)  # For snackbar
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="20")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
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
        self.show_snackbar(f"Selected port: {selected_port}")
    
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
    
    def print_qr_code(self):
        """Print the device's QR code"""
        selected_port = self.device_var.get()
        if selected_port:
            self.show_snackbar(f"Printing QR code for device on port: {selected_port}")
            print_qr_code("E4B13797BACC")
        else:
            self.show_snackbar("No device selected for printing", "warning")
    
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
        
        
        root.mainloop()
        
    except KeyboardInterrupt:
        print("\nApplication interrupted by user.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 