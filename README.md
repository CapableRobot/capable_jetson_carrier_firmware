# Capable Jetson Carrier : MCU Firmware

## Installation Instructions

Install system dependencies and configure host:

```
sudo apt-get update
sudo apt-get install -y python3.7

wget https://bootstrap.pypa.io/get-pip.py -O get-pip.py
sudo python3.7 get-pip.py
rm get-pip.py

sudo python3.7 -m pip install esptool
sudo python3.7 -m pip install sh
sudo python3.7 -m pip install Jetson.GPIO
sudo python3.7 -m pip install mpremote

sudo adduser $USER dialout i2c gpio
sudo systemctl disable nvgetty.service
sudo systemctl set-default multi-user.target

wget https://raw.githubusercontent.com/CapableRobot/capable_jetson_carrier_firmware/main/mcutool
chmod +x mcutool
sudo mv mcutool /usr/local/bin

wget https://raw.githubusercontent.com/CapableRobot/capable_jetson_carrier_firmware/main/mcupower.service
sudo mv mcupower.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable mcupower
sudo reboot
```

Download and flash firmware onto MCU:

```
mcutool flashos

mkdir firmware
cd firmware

wget https://raw.githubusercontent.com/CapableRobot/capable_jetson_carrier_firmware/main/neotimer.py
wget https://raw.githubusercontent.com/CapableRobot/capable_jetson_carrier_firmware/main/statemachine.py
wget https://raw.githubusercontent.com/CapableRobot/capable_jetson_carrier_firmware/main/main.py
wget https://raw.githubusercontent.com/CapableRobot/capable_jetson_carrier_firmware/main/boot.py

mcutool flashcode
mcutool reboot
```
