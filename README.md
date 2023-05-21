# Razer Battery Checker

Simple system tray applet to show battery level of razer devices. Should work on Linux, Windows and MacOS (latter not tested). Mostly adapted from [OpenRazer](https://github.com/openrazer/openrazer) and [OpenRGB](https://github.com/CalcProgrammer1/OpenRGB).

## Adding new devices

* add device with NAME, PID, INTERFACE, USAGE PAGE, USAGE to [devices.py](/devices.py)
* add TRANSACTION ID to constructor of DeviceController in [device_controller.py](/device_controller.py)

## Linux

Under Linux you also have to add a udev rule to get access to usb devices (see [here](https://github.com/libusb/hidapi/blob/master/udev/69-hid.rules)).

## Projects used

* https://github.com/trezor/cython-hidapi
* https://github.com/moses-palmer/pystray
