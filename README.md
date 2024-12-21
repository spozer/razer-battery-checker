# Razer Battery Checker

Simple system tray icon app to show battery level of various razer devices. Should work on Linux, Windows and macOS (latter not tested). Mostly adapted from [OpenRazer](https://github.com/openrazer/openrazer) and [OpenRGB](https://github.com/CalcProgrammer1/OpenRGB).

![screenshot](/screenshot.png)

## Adding new devices

* add device with `name`, `pid`, `interface`, `usage_page`, `usage` to [devices.py](src/devices.py)
* add `transaction_id` to switch statement in constructor of `DeviceController` in [device_controller.py](src/device_controller.py)

## Linux

On Linux you also have to add a udev rule to get access to usb devices (see [here](https://github.com/libusb/hidapi/blob/master/udev/69-hid.rules)).

## Build executables

Building with [PyInstaller](https://pyinstaller.org/en/stable/)

For Linux:
``` bash
pyinstaller --onefile --noconsole --add-data "images/*:images" src/app.pyw
```

For Windows:
``` bash
pyinstaller --onefile --noconsole --add-data "images/*;images" src/app.pyw
```
You can also use wine to build an .exe under Linux.

## Projects used

* https://github.com/trezor/cython-hidapi
* https://github.com/moses-palmer/pystray
