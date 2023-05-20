from dataclasses import dataclass
from threading import Thread, Event, Lock
from device_manager import DeviceManager
from winotify import Notification, audio
from PIL import Image
from pathlib import Path
import pystray
import logging


PROJECT_PATH = Path(__file__).parent.resolve()
TRAY_ICON_LOGO_FILENAME = "razer-logo-tray.png"
NOTIFICATION_LOGO_FILENAME = "razer-logo.png"

BATTERY_UPDATE_INTERVAL = 120  # seconds
DEVICE_FETCH_INTERVAL = 5  # seconds

logging.basicConfig(
    filename=PROJECT_PATH / "razer_battery_checker.log",
    filemode="w",
    level=logging.DEBUG,
    format="%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(funcName)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d:%H:%M:%S",
)

logger = logging.getLogger(__name__)


@dataclass
class MemoryDevice:
    name: str
    id: int
    battery_level: int = -1
    old_battery_level: int = 50
    is_charging: bool = False


class TrayIconApp(Thread):
    _device_manager: DeviceManager
    _tray_icon: pystray.Icon
    _devices: dict[int, MemoryDevice] = {}
    _device_fetcher: Thread

    _update_lock = Lock()
    _manager_lock = Lock()
    _devices_lock = Lock()
    _exit_event = Event()

    def __init__(self):
        Thread.__init__(self)
        self._device_manager = DeviceManager()
        self._tray_icon = pystray.Icon(
            "Razer Battery Checker",
            Image.open(PROJECT_PATH / TRAY_ICON_LOGO_FILENAME),
            "Razer Battery Checker",
        )
        self._device_fetcher = Thread(target=self._device_fetching_thread_function)

    def run(self):
        self._tray_icon.run_detached()
        self._device_fetcher.start()

        while not self._exit_event.wait(BATTERY_UPDATE_INTERVAL):
            self._update(self._devices.keys())

        self._device_fetcher.join()
        self._tray_icon.stop()

    def _device_fetching_thread_function(self):
        while not self._exit_event.is_set():
            with self._manager_lock:
                removed_devices, added_devices = self._device_manager.fetch_devices()

                # update device list
                with self._devices_lock:
                    for id in removed_devices:
                        logger.info(
                            "Device removed: {:s}".format(self._devices[id].name)
                        )
                        print("Device removed: {:s}".format(self._devices[id].name))
                        del self._devices[id]

                    for id in added_devices:
                        name = self._device_manager.get_device_name(id)
                        self._devices[id] = MemoryDevice(name, id)
                        logger.info("New device: {:s}".format(name))
                        print("New device: {:s}".format(name))

            if len(removed_devices) > 0 or len(added_devices) > 0:
                self._update(added_devices)

            self._exit_event.wait(DEVICE_FETCH_INTERVAL)

    def _on_exit_pressed(self):
        self._exit_event.set()
        logger.info("Exit app")
        print("Exit")

    def _get_menu_items(self):
        menu = []

        for device in self._devices.values():
            display_name = device.name
            if device.is_charging:
                display_name += " (charging)"
            device_entry = pystray.MenuItem(
                text="{:s}\t{:d}%".format(display_name, device.battery_level),
                action=None,
                enabled=False,
            )
            menu.append(device_entry)

        menu.append(pystray.Menu.SEPARATOR)
        menu.append(pystray.MenuItem("Exit", self._on_exit_pressed))

        return menu

    def _notify(self, device_name: str, massage: str, battery_level: int):
        toast = Notification(
            icon=str(PROJECT_PATH / NOTIFICATION_LOGO_FILENAME),
            app_id="Razer Battery Checker",
            title="{:s}: {:s}".format(device_name, massage),
            msg="Battery Level: {:d}%".format(battery_level),
        )
        toast.set_audio(audio.Default, loop=False)
        toast.show()

    def _check_notify(self, devices: list[int]):
        for id in devices:
            device = self._devices[id]
            if device.battery_level == -1:
                continue
            # check for low battery level
            if device.battery_level <= 5 or (
                device.old_battery_level > 15 and device.battery_level <= 15
            ):
                self._notify(device.name, "Battery low", device.battery_level)
            # check if battery charged fully
            elif (
                device.old_battery_level <= 99
                and device.battery_level == 100
                and device.is_charging
            ):
                self._notify(device.name, "Battery fully charged", device.battery_level)

    def _update(self, devices: list[int]):
        # update battery level of given devices
        with self._manager_lock:
            with self._devices_lock:
                for id in devices:
                    battery_level = self._device_manager.get_device_battery_level(id)

                    if battery_level == -1:
                        continue

                    old_battery_level = self._devices[id].battery_level
                    self._devices[id].battery_level = battery_level

                    if old_battery_level != -1:
                        self._devices[id].old_battery_level = old_battery_level

                    self._devices[
                        id
                    ].is_charging = self._device_manager.is_device_charging(id)

                    logger.info(
                        "Updated battery level {:d}%, charging: {} for {:s}".format(
                            battery_level,
                            self._devices[id].is_charging,
                            self._devices[id].name,
                        )
                    )

        with self._update_lock:
            self._tray_icon.menu = self._get_menu_items()
            self._check_notify(devices)


def main():
    app = TrayIconApp()
    app.start()


if __name__ == "__main__":
    main()
