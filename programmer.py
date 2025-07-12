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
        title_label = ttk.Label(self.main_frame, text="FT232H Device Monitor", font=('Arial', 24, 'bold'))
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # Create status frame
        self.status_frame = ttk.Frame(self.main_frame)
        self.status_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.status_frame.columnconfigure(0, weight=1)
        
        # Status display
        self.status_label = ttk.Label(self.status_frame, text="Checking devices...", font=('Arial', 16))
        self.status_label.grid(row=0, column=0, pady=10)
        
        # Dropdown for FT232H TTY ports
        self.device_label = ttk.Label(self.status_frame, text="Select FT232H Port:", font=('Arial', 14))
        self.device_label.grid(row=1, column=0, pady=(10, 0))
        self.device_var = tk.StringVar()
        self.device_dropdown = ttk.Combobox(self.status_frame, textvariable=self.device_var, state="readonly", font=('Arial', 14), width=30)
        self.device_dropdown.grid(row=2, column=0, pady=(5, 10))
        self.device_dropdown.bind("<<ComboboxSelected>>", self.on_device_selected)
        
        # Selected port display
        self.selected_port = None
        self.selected_label = ttk.Label(self.status_frame, text="Selected port: None", font=('Arial', 12))
        self.selected_label.grid(row=3, column=0, pady=(5, 10))
        
        # Last update time
        self.update_time_label = ttk.Label(self.status_frame, text="", font=('Arial', 10))
        self.update_time_label.grid(row=4, column=0, pady=(10, 0))
        
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
            status_text = f"❌ {error}"
            self.status_label.config(text=status_text, foreground="red")
            self.device_dropdown['values'] = []
            self.device_var.set('')
        elif ft232h_devices:
            status_text = f"✅ FT232H Device Connected ({len(ft232h_devices)} found)"
            self.status_label.config(text=status_text, foreground="green")
            self.device_dropdown['values'] = tty_devices
            if tty_devices:
                if self.selected_port not in tty_devices:
                    self.selected_port = tty_devices[0]
                    self.device_var.set(self.selected_port)
            else:
                self.selected_port = None
                self.device_var.set('')
        else:
            status_text = "❌ No FT232H Device Connected"
            self.status_label.config(text=status_text, foreground="red")
            self.device_dropdown['values'] = []
            self.device_var.set('')
            self.selected_port = None
        
        # Update selected port display
        self.selected_label.config(text=f"Selected port: {self.selected_port if self.selected_port else 'None'}")
        
        # Update timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.update_time_label.config(text=f"Last updated: {timestamp}")
    
    def monitor_devices(self):
        """Monitor devices every second in a separate thread"""
        while self.running:
            time.sleep(1)
            # Use after() to update GUI from main thread
            self.root.after(0, self.check_devices)
    
    def on_device_selected(self, event):
        """Handle device selection from dropdown"""
        self.selected_port = self.device_var.get()
        self.selected_label.config(text=f"Selected port: {self.selected_port}")
    
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