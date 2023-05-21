# Razer Battery Checker

Simple Windows system tray applet to show battery level of razer devices.

Mostly adapted from:
* https://github.com/openrazer/openrazer
* https://github.com/CalcProgrammer1/OpenRGB

## To add new devices:

* add device with NAME, PID, INTERFACE, USAGE PAGE, USAGE to devices.py
* add TRANSACTION ID to constructor of DeviceController in device_controller.py