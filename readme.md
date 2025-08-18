
Download archive:
curl https://edlquuxypulyedwgweai.supabase.co/storage/v1/object/public/programmer/v1.zip --output programmer.zip
unzip programmer.zip
cd ccprogrammer/


On linux and mac create venve first
python3 -m venv ~/ccprog_venv
source ~/ccprog_venv/bin/activate

Then install the requirements
pip install -r requirements.txt

To create desktop shortcut copy this into ~/Desktop/programmer.desktop 
[Desktop Entry]
Version=1.0
Type=Application
Name=CC2 Programmer
Comment=FT232H Device Monitor and Programmer
Exec=/home/pi/ccprog_venv/bin/python /home/pi/ccprogrammer/programmer.py
Icon=applications-system
Terminal=false
Categories=Utility;System;

Copy this into /etc/systemd/system/programmer.service
[Unit]
Description=FT232H Monitor GUI
After=network.target graphical-session.target

[Service]
Type=simple
ExecStart=/home/pi/ccprog_venv/bin/python /home/pi/ccprogrammer/programmer.py
WorkingDirectory=/home/pi/ccprogrammer
User=pi
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/pi/.Xauthority
Restart=on-failure
RestartSec=5

[Install]
WantedBy=graphical.target
EOF

# run this after to enable service
sudo systemctl daemon-reload && sudo systemctl enable programmer.service

# to remotely run the programmer to pi display
export DISPLAY=:0

# To build windows executable
pyinstaller -F programmer.py --clean --hidden-import=usb.backend.libusb1 --hidden-import=usb.backend --add-data "C:\Python313\Lib\site-packages\esptool\targets\stub_flasher;esptool\targets\stub_flasher"       

pyinstaller -F programmer.py --clean   --hidden-import=usb.backend.libusb1   --hidden-import=usb.backend   --add-data "/home/coolcure2/ccprog_venv/lib/python3.11/site-packages/esptool/targets/stub_flasher:esptool/targets/stub_flasher"
