from devices import *
import hid
import time
import logging

MAX_TRIES_SEND = 10
TIME_BETWEEN_SEND = 0.5  # seconds


logger = logging.getLogger(__name__)


class RazerReport:
    """
    Request Report - 90 bytes

    status                  0x00\n
    transaction id          0x3f\n
    remaining packets       0x00\n
    remaining packets       0x00\n
    protocol type           0x00\n
    data size               0x02\n
    command class           0x07\n
    command id              0x80\n
    argument 0              ____\n
    argument 1              ____\n
    ...\n
    argument 79             ____\n
    crc                     0x85\n
    reserved                0x00\n
    """

    STATUS_NEW_COMMAND = 0x00
    STATUS_BUSY = 0x01
    STATUS_SUCCESSFUL = 0x02
    STATUS_FAILURE = 0x03
    STATUS_NO_RESPONSE = 0x04
    STATUS_NOT_SUPPORTED = 0x05

    status = 0x00
    transaction_id = 0x00
    remaining_packets = 0x0000
    protocol_type = 0x00
    data_size = 0x00
    command_class = 0x00
    command_id = 0x00
    arguments = [0x00] * 80
    crc = 0x00
    reserved = 0x00

    def __init__(self):
        pass

    def from_bytes(data):
        if len(data) != 90:
            logger.error(
                "Expected 90 bytes of data as razer raport but got {:d} bytes: {}".format(
                    len(data), data
                ),
            )
            raise ValueError("Expected 90 bytes of data as razer raport")

        report = RazerReport()

        report.status = data[0]
        report.transaction_id = data[1]
        # Big Endian
        report.remaining_packets = data[2] << 8 | data[3]
        report.protocol_type = data[4]
        report.data_size = data[5]
        report.command_class = data[6]
        report.command_id = data[7]
        report.arguments = data[8:88]
        report.crc = data[88]
        report.reserved = data[89]

        return report

    def pack(self):
        data = [
            self.status,
            self.transaction_id,
            # Big Endian
            self.remaining_packets & 0x1100,
            self.remaining_packets & 0x0011,
            self.protocol_type,
            self.data_size,
            self.command_class,
            self.command_id,
        ]

        data += self.arguments

        data += [self.crc, self.reserved]

        return data

    def calculate_crc(self):
        data = self.pack()
        crc = 0

        for i in range(2, 88):
            crc ^= data[i]

        return crc

    def is_valid(self):
        return self.calculate_crc() == self.crc


class DeviceController:
    _handle: hid.device
    _name: str
    _pid: int
    _path: str
    _report_id: int
    _transaction_id: int

    def __init__(self, name: str, pid: int, path: str) -> None:
        self._handle = hid.device()
        self._name = name
        self._pid = pid
        self._path = path
        self._report_id = 0x00

        match pid:
            case (
                RAZER_NAGA_PRO_WIRED.pid
                | RAZER_NAGA_PRO_WIRELESS.pid
                | RAZER_BASILISK_V3_PRO_WIRED.pid
                | RAZER_BASILISK_V3_PRO_WIRELESS.pid
            ):
                self._transaction_id = 0x1F
            case (
                RAZER_DEATHADDER_V2_PRO_WIRED.pid
                | RAZER_DEATHADDER_V2_PRO_WIRELESS.pid
                | _
            ):
                self._transaction_id = 0x3F

    def __del__(self) -> None:
        self.close()

    @property
    def name(self) -> str:
        return self._name

    @property
    def id(self) -> int:
        return self._pid

    def open(self) -> None:
        try:
            self._handle.open_path(self._path)
        except OSError as e:
            logger.error(
                "Failed to open device: {:s} with error message: {:s}".format(
                    self._name, e
                )
            )
            raise ValueError("Failed to open device: " + self._name) from e

        # enable non-blocking mode
        self._handle.set_nonblocking(1.0)

    def close(self) -> None:
        if self._handle is not None:
            self._handle.close()

    def get_battery_level(self) -> int:
        battery_level = -1.0

        request = self._create_command(0x07, 0x80, 0x02)

        try:
            response = self._send_payload(request)
            battery_level = (response.arguments[1] / 255) * 100.0
        except ValueError as e:
            print(e)
            print("Could not get battery level, setting it to -1")

        print("{:s}\t battery level: {:.2f}%".format(self._name, battery_level))

        return round(battery_level)

    def get_charging_status(self) -> bool:
        charging_status = 0

        request = self._create_command(0x07, 0x84, 0x02)

        try:
            response = self._send_payload(request)
            charging_status = response.arguments[1]
        except ValueError as e:
            print(e)
            print("Could not get charging status, setting it to 0")

        print("{:s}\t charging status: {:d}".format(self._name, charging_status))

        return charging_status

    def _send_payload(self, request: RazerReport) -> RazerReport:
        request.crc = request.calculate_crc()
        response = None

        # try to resend report if device is busy or non responsive
        for i in range(MAX_TRIES_SEND):
            # TODO exception handling
            self._usb_send(request)

            # TODO exception handling
            response = self._usb_receive()

            # check if response matches request
            if (
                response.remaining_packets != request.remaining_packets
                or response.command_class != request.command_class
                or response.command_id != request.command_id
            ):
                logger.error("Response doesn't match request")
                raise ValueError("Response doesn't match request")

            match response.status:
                case RazerReport.STATUS_SUCCESSFUL:
                    logger.info("Command successful")
                    break
                case RazerReport.STATUS_BUSY:
                    logger.info("Device is busy")
                    print("Device is busy")
                case RazerReport.STATUS_NO_RESPONSE:
                    logger.info("Command timed out")
                    print("Command timed out")
                case RazerReport.STATUS_NOT_SUPPORTED:
                    logger.error("Command not supported")
                    raise ValueError("Command not supported")
                case RazerReport.STATUS_FAILURE:
                    logger.error("Command failed")
                    raise ValueError("Command failed")
                case _:
                    logger.error("Error unknown report status")
                    raise ValueError("Error unknown report status")

            if i == MAX_TRIES_SEND - 1:
                logger.error("Abort command after {:d} tries".format(MAX_TRIES_SEND))
                raise ValueError("Abort command (tries: {:d})".format(MAX_TRIES_SEND))

            time.sleep(TIME_BETWEEN_SEND)
            print("Trying to resend command")

        return response

    def _create_command(
        self, command_class: int, command_id: int, data_size: int
    ) -> RazerReport:
        assert command_class < 0xFF
        assert command_id < 0xFF
        assert data_size < 0xFF

        report = RazerReport()

        report.status = RazerReport.STATUS_NEW_COMMAND
        report.transaction_id = self._transaction_id
        report.remaining_packets = 0x00
        report.protocol_type = 0x00
        report.command_class = command_class
        report.command_id = command_id
        report.data_size = data_size

        return report

    def _usb_send(self, report: RazerReport) -> None:
        data = report.pack()

        # windows expects report id as first entry of report
        bytes_sent = self._handle.send_feature_report([self._report_id] + data)
        time.sleep(0.06)

        if bytes_sent != len(data) + 1:
            logger.error("Error while sending feature report")
            raise ValueError("Error while sending feature report")

    def _usb_receive(self) -> RazerReport:
        # windows expects report id as first entry of report (90 bytes)
        expected_length = 91

        data = self._handle.get_feature_report(self._report_id, expected_length)
        # time.sleep(0.1)

        if len(data) != expected_length:
            logger.error("Error while getting feature report")
            raise ValueError("Error while getting feature report")

        # omit first byte (report id)
        report = RazerReport.from_bytes(data[1:])

        if not report.is_valid():
            logger.error("CRC failed {}".format(report))
            raise ValueError("Get report has no valid crc")

        return report
