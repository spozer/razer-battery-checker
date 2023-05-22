# Razer Battery Checker

Simple system tray icon app to show battery level of various razer devices. Should work on Linux, Windows and macOS (latter not tested). Mostly adapted from [OpenRazer](https://github.com/openrazer/openrazer) and [OpenRGB](https://github.com/CalcProgrammer1/OpenRGB).

![screenshot](/screenshot.PNG)

## Adding new devices

* add device with `name`, `pid`, `interface`, `usage_page`, `usage` to [devices.py](/devices.py)
* add `transaction_id` to switch statement in constructor of `DeviceController` in [device_controller.py](/device_controller.py)

## Linux

On Linux you also have to add a udev rule to get access to usb devices (see [here](https://github.com/libusb/hidapi/blob/master/udev/69-hid.rules)).

## Projects used

* https://github.com/trezor/cython-hidapi
* https://github.com/moses-palmer/pystray
