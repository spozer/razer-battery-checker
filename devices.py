from dataclasses import dataclass


@dataclass
class RazerDevice:
    name: str
    pid: int
    interface: int
    usage_page: int
    usage: int
    vid: int = 0x1532


RAZER_BASILISK_V3_PRO_WIRED = RazerDevice("Razer Basilisk V3 Pro", 0x00AA, 0, 1, 2)
RAZER_BASILISK_V3_PRO_WIRELESS = RazerDevice("Razer Basilisk V3 Pro", 0x00AB, 0, 1, 2)

RAZER_DEATHADDER_V2_PRO_WIRED = RazerDevice("Razer DeathAdder V2 Pro", 0x007C, 0, 1, 2)
RAZER_DEATHADDER_V2_PRO_WIRELESS = RazerDevice("Razer DeathAdder V2 Pro", 0x007D, 0, 1, 2)

RAZER_NAGA_PRO_WIRED = RazerDevice("Razer Naga Pro", 0x008F, 0, 1, 2)
RAZER_NAGA_PRO_WIRELESS = RazerDevice("Razer Naga Pro", 0x0090, 0, 1, 2)


RAZER_DEVICE_LIST = [
    RAZER_BASILISK_V3_PRO_WIRED,
    RAZER_BASILISK_V3_PRO_WIRELESS,
    RAZER_DEATHADDER_V2_PRO_WIRED,
    RAZER_DEATHADDER_V2_PRO_WIRELESS,
    RAZER_NAGA_PRO_WIRED,
    RAZER_NAGA_PRO_WIRELESS,
]
