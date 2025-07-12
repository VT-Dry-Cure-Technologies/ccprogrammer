from escpos.printer import Usb
from escpos.printer.profile import DefaultProfile

VENDOR_ID = 0x0483
PRODUCT_ID = 0x5743

try:
    # Create a custom profile with media width
    profile = DefaultProfile()
    profile.set_width(384)  # Set media width in pixels (adjust based on printer manual)
    printer = Usb(VENDOR_ID, PRODUCT_ID, profile=profile)
    printer.text("QR Code Test\n")
    printer.qr("https://example.com", center=True)
    printer.text("\nScan Me\n")
    printer.cut()
    print("QR code sent to printer.")
except Exception as e:
    print(f"Error: {e}")
