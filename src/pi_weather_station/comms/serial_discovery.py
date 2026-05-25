from dataclasses import dataclass

from serial.tools import list_ports


@dataclass(frozen=True)
class SerialDevice:
    device: str
    description: str
    hwid: str
    manufacturer: str | None = None
    product: str | None = None


def discover_usb_serial_devices() -> list[SerialDevice]:
    devices: list[SerialDevice] = []

    for port in list_ports.comports():
        # Ignore built-in UARTs and only keep USB-ish serial devices.
        if not _looks_like_usb_serial(port.device, port.hwid):
            continue

        devices.append(
            SerialDevice(
                device=port.device,
                description=port.description,
                hwid=port.hwid,
                manufacturer=port.manufacturer,
                product=port.product,
            )
        )

    return devices


def _looks_like_usb_serial(device: str, hwid: str) -> bool:
    device_lower = device.lower()
    hwid_lower = hwid.lower()

    if "usb" in hwid_lower:
        return True

    if device_lower.startswith("/dev/ttyusb"):
        return True

    if device_lower.startswith("/dev/ttyacm"):
        return True

    # Windows-friendly fallback for early testing.
    if device_lower.startswith("com"):
        return True

    return False