The files included in this folder are:

1. MQTT Subscriber Node Program: to be run on a computer (made for Windows environment) to collect incoming BLE data from Raspberry Pi scanners and write to a log

the log will be called 'LOGGING' additional data for debugging is written to 'SubLog' in the main Python workspace on the computer

2. RPI1 Scanner, RPI2 Scanner, RPI3 Scanner: Scanner programs on the Raspberry Pi's (they differ due to IP addressing)

3. ssh_putty: script to launch Putty to ssh into the Raspberry Pi BLE Scanners

Login using: pi (or 'rpi1', 'rpi2', 'rpi3' as needed)
password: raspberry

once in Putty in the Rasbian environment the following command needs to be run to launch the BLE Scanner:
$sudo python scanner1.py 