from devices import RAZER_DEVICE_LIST
from device_controller import DeviceController
import hid
import logging

logger = logging.getLogger(__name__)


# Expect not many connected devices -> List instead of Dict
class DeviceManager:
    _device_controllers: list[DeviceController] = []

    def __init__(self) -> None:
        pass

    def fetch_devices(self) -> tuple[list[int], list[int]]:
        old_ids = [controller.id for controller in self._device_controllers]
        self._device_controllers = self._get_connected_devices()
        new_ids = [controller.id for controller in self._device_controllers]

        removed_devices = [id for id in old_ids if id not in new_ids]
        added_devices = [id for id in new_ids if id not in old_ids]

        return (removed_devices, added_devices)

    def get_device_name(self, id: int) -> str:
        controller = self._get_controller_from_id(id)

        return controller.name

    def get_device_battery_level(self, id: int) -> int:
        controller = self._get_controller_from_id(id)

        controller.open()
        battery_level = controller.get_battery_level()
        controller.close()

        return battery_level
    
    def is_device_charging(self, id: int) -> bool:
        controller = self._get_controller_from_id(id)

        controller.open()
        charging_status = controller.get_charging_status()
        controller.close()

        return bool(charging_status)

    def _get_controller_from_id(self, id: int) -> DeviceController:
        for controller in self._device_controllers:
            if controller.id == id:
                return controller

    def _get_connected_devices(self) -> list[DeviceController]:
        connected_devices = []

        # TODO exception handling for hid calls

        # get HID collection for each connected razer device
        for device in RAZER_DEVICE_LIST:
            hid_collection = hid.enumerate(device.vid, device.pid)

            # device probably not connected
            if len(hid_collection) == 0:
                continue

            # find matching HID control for each device
            for hid_control in hid_collection:
                if (
                    hid_control["interface_number"] == device.interface
                    and hid_control["usage_page"] == device.usage_page
                    and hid_control["usage"] == device.usage
                ):
                    controller = DeviceController(
                        device.name, device.pid, hid_control["path"]
                    )
                    connected_devices.append(controller)

        return connected_devices
