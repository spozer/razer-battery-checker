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
    __device_manager: DeviceManager
    __tray_icon: pystray.Icon
    __devices: dict[int, MemoryDevice] = {}
    __device_fetcher: Thread

    __update_lock = Lock()
    __manager_lock = Lock()
    __devices_lock = Lock()
    __exit_event = Event()

    def __init__(self):
        Thread.__init__(self)
        self.__device_manager = DeviceManager()
        self.__tray_icon = pystray.Icon(
            "Razer Battery Checker",
            Image.open(PROJECT_PATH / TRAY_ICON_LOGO_FILENAME),
            "Razer Battery Checker",
        )
        self.__device_fetcher = Thread(target=self.__device_fetching_thread_function)

    def run(self):
        self.__tray_icon.run_detached()
        self.__device_fetcher.start()

        while not self.__exit_event.wait(BATTERY_UPDATE_INTERVAL):
            self.__update(self.__devices.keys())

        self.__device_fetcher.join()
        self.__tray_icon.stop()

    def __device_fetching_thread_function(self):
        while not self.__exit_event.is_set():
            with self.__manager_lock:
                removed_devices, added_devices = self.__device_manager.fetch_devices()

                # update device list
                with self.__devices_lock:
                    for id in removed_devices:
                        logger.info(
                            "Device removed: {:s}".format(self.__devices[id].name)
                        )
                        print("Device removed: {:s}".format(self.__devices[id].name))
                        del self.__devices[id]

                    for id in added_devices:
                        name = self.__device_manager.get_device_name(id)
                        self.__devices[id] = MemoryDevice(name, id)
                        logger.info("New device: {:s}".format(name))
                        print("New device: {:s}".format(name))

            if len(removed_devices) > 0 or len(added_devices) > 0:
                self.__update(added_devices)

            self.__exit_event.wait(DEVICE_FETCH_INTERVAL)

    def __on_exit_pressed(self):
        self.__exit_event.set()
        logger.info("Exit app")
        print("Exit")

    def __get_menu_items(self):
        menu = []

        for device in self.__devices.values():
            display_name = device.name
            battery_text = "{:d}%".format(device.battery_level)

            if device.is_charging:
                display_name += " (charging)"

            if device.battery_level == -1:
                battery_text = "err."

            device_entry = pystray.MenuItem(
                text=display_name + "\t" + battery_text,
                action=None,
                enabled=False,
            )
            menu.append(device_entry)

        menu.append(pystray.Menu.SEPARATOR)
        menu.append(pystray.MenuItem("Exit", self.__on_exit_pressed))

        return menu

    def __notify(self, device_name: str, massage: str, battery_level: int):
        toast = Notification(
            icon=str(PROJECT_PATH / NOTIFICATION_LOGO_FILENAME),
            app_id="Razer Battery Checker",
            title="{:s}: {:s}".format(device_name, massage),
            msg="Battery Level: {:d}%".format(battery_level),
        )
        toast.set_audio(audio.Default, loop=False)
        toast.show()

    def __check_notify(self, devices: list[int]):
        for id in devices:
            device = self.__devices[id]
            if device.battery_level == -1:
                continue
            # check for low battery level
            if device.battery_level <= 5 or (
                device.old_battery_level > 15 and device.battery_level <= 15
            ):
                self.__notify(device.name, "Battery low", device.battery_level)
            # check if battery charged fully
            elif (
                device.old_battery_level <= 99
                and device.battery_level == 100
                and device.is_charging
            ):
                self.__notify(
                    device.name, "Battery fully charged", device.battery_level
                )

    def __update(self, devices: list[int]):
        # update battery level of given devices
        with self.__manager_lock:
            with self.__devices_lock:
                for id in devices:
                    battery_level = self.__device_manager.get_device_battery_level(id)

                    if battery_level == -1:
                        continue

                    device = self.__devices[id]

                    old_battery_level = device.battery_level
                    device.battery_level = battery_level

                    if old_battery_level != -1:
                        device.old_battery_level = old_battery_level

                    device.is_charging = self.__device_manager.is_device_charging(id)

                    logger.info(
                        "Updated battery level {:d}%, charging: {} for {:s}".format(
                            battery_level,
                            device.is_charging,
                            device.name,
                        )
                    )

        with self.__update_lock:
            self.__tray_icon.menu = self.__get_menu_items()
            self.__check_notify(devices)


def main():
    app = TrayIconApp()
    app.start()


if __name__ == "__main__":
    main()
