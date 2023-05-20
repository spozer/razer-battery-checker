from dataclasses import dataclass


@dataclass
class RazerDevice:
    name: str
    pid: int
    interface: int
    usage_page: int
    usage: int
    vid: int = 0x1532


RAZER_DEATHADDER_V2_PRO_WIRELESS = RazerDevice(
    "Razer DeathAdder V2 Pro", 0x007D, 0, 1, 2
)

RAZER_DEATHADDER_V2_PRO_WIRED = RazerDevice(
    "Razer DeathAdder V2 Pro", 0x007C, 0, 1, 2
)

RAZER_DEVICE_LIST = [RAZER_DEATHADDER_V2_PRO_WIRELESS, RAZER_DEATHADDER_V2_PRO_WIRED]
