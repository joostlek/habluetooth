"""Models for bluetooth."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Final, TypeVar

from bleak import BaseBleakClient
from bleak.backends import device, scanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

if TYPE_CHECKING:
    from .manager import BluetoothManager

_BluetoothServiceInfoSelfT = TypeVar(
    "_BluetoothServiceInfoSelfT", bound="BluetoothServiceInfo"
)

_BluetoothServiceInfoBleakSelfT = TypeVar(
    "_BluetoothServiceInfoBleakSelfT", bound="BluetoothServiceInfoBleak"
)
SOURCE_LOCAL: Final = "local"

_float = float  # avoid cython conversion since we always want a pyfloat
_str = str  # avoid cython conversion since we always want a pystr
_int = int  # avoid cython conversion since we always want a pyint


class CentralBluetoothManager:
    """Central Bluetooth Manager."""

    manager: BluetoothManager | None = None


def get_manager() -> BluetoothManager:
    """Get the BluetoothManager."""
    if TYPE_CHECKING:
        assert CentralBluetoothManager.manager is not None
    return CentralBluetoothManager.manager


def set_manager(manager: BluetoothManager) -> None:
    """Set the BluetoothManager."""
    CentralBluetoothManager.manager = manager


@dataclass(slots=True)
class HaBluetoothConnector:
    """Data for how to connect a BLEDevice from a given scanner."""

    client: type[BaseBleakClient]
    source: str
    can_connect: Callable[[], bool]


class BluetoothScanningMode(Enum):
    """The mode of scanning for bluetooth devices."""

    PASSIVE = "passive"
    ACTIVE = "active"


class BluetoothServiceInfo:
    """Prepared info from bluetooth entries."""

    __slots__ = (
        "name",
        "address",
        "rssi",
        "manufacturer_data",
        "service_data",
        "service_uuids",
        "source",
    )

    def __init__(
        self,
        name: _str,  # may be a pyobjc object
        address: _str,  # may be a pyobjc object
        rssi: _int,  # may be a pyobjc object
        manufacturer_data: dict[_int, bytes],
        service_data: dict[_str, bytes],
        service_uuids: list[_str],
        source: _str,
    ) -> None:
        """Initialize a bluetooth service info."""
        self.name = name
        self.address = address
        self.rssi = rssi
        self.manufacturer_data = manufacturer_data
        self.service_data = service_data
        self.service_uuids = service_uuids
        self.source = source

    @classmethod
    def from_advertisement(
        cls: type[_BluetoothServiceInfoSelfT],
        device: BLEDevice,
        advertisement_data: AdvertisementData,
        source: str,
    ) -> _BluetoothServiceInfoSelfT:
        """Create a BluetoothServiceInfo from an advertisement."""
        return cls(
            advertisement_data.local_name or device.name or device.address,
            device.address,
            advertisement_data.rssi,
            advertisement_data.manufacturer_data,
            advertisement_data.service_data,
            advertisement_data.service_uuids,
            source,
        )

    @property
    def manufacturer(self) -> str | None:
        """Convert manufacturer data to a string."""
        from bleak.backends._manufacturers import (
            MANUFACTURERS,  # pylint: disable=import-outside-toplevel
        )

        for manufacturer in self.manufacturer_data:
            if manufacturer in MANUFACTURERS:
                name: str = MANUFACTURERS[manufacturer]
                return name
        return None

    @property
    def manufacturer_id(self) -> int | None:
        """Get the first manufacturer id."""
        for manufacturer in self.manufacturer_data:
            return manufacturer
        return None


class BluetoothServiceInfoBleak(BluetoothServiceInfo):
    """
    BluetoothServiceInfo with bleak data.

    Integrations may need BLEDevice and AdvertisementData
    to connect to the device without having bleak trigger
    another scan to translate the address to the system's
    internal details.
    """

    __slots__ = ("device", "advertisement", "connectable", "time")

    def __init__(
        self,
        name: _str,  # may be a pyobjc object
        address: _str,  # may be a pyobjc object
        rssi: _int,  # may be a pyobjc object
        manufacturer_data: dict[_int, bytes],
        service_data: dict[_str, bytes],
        service_uuids: list[_str],
        source: _str,
        device: BLEDevice,
        advertisement: AdvertisementData,
        connectable: bool,
        time: _float,
    ) -> None:
        self.name = name
        self.address = address
        self.rssi = rssi
        self.manufacturer_data = manufacturer_data
        self.service_data = service_data
        self.service_uuids = service_uuids
        self.source = source
        self.device = device
        self.advertisement = advertisement
        self.connectable = connectable
        self.time = time

    def as_dict(self) -> dict[str, Any]:
        """
        Return as dict.

        The dataclass asdict method is not used because
        it will try to deepcopy pyobjc data which will fail.
        """
        return {
            "name": self.name,
            "address": self.address,
            "rssi": self.rssi,
            "manufacturer_data": self.manufacturer_data,
            "service_data": self.service_data,
            "service_uuids": self.service_uuids,
            "source": self.source,
            "advertisement": self.advertisement,
            "device": self.device,
            "connectable": self.connectable,
            "time": self.time,
        }

    @classmethod
    def from_scan(
        cls: type[_BluetoothServiceInfoBleakSelfT],
        source: str,
        device: BLEDevice,
        advertisement_data: AdvertisementData,
        monotonic_time: _float,
        connectable: bool,
    ) -> _BluetoothServiceInfoBleakSelfT:
        """Create a BluetoothServiceInfoBleak from a scanner."""
        return cls(
            advertisement_data.local_name or device.name or device.address,
            device.address,
            advertisement_data.rssi,
            advertisement_data.manufacturer_data,
            advertisement_data.service_data,
            advertisement_data.service_uuids,
            source,
            device,
            advertisement_data,
            connectable,
            monotonic_time,
        )

    @classmethod
    def from_device_and_advertisement_data(
        cls: type[_BluetoothServiceInfoBleakSelfT],
        device: BLEDevice,
        advertisement_data: AdvertisementData,
        source: str,
        time: _float,
        connectable: bool,
    ) -> _BluetoothServiceInfoBleakSelfT:
        """Create a BluetoothServiceInfoBleak from a device and advertisement."""
        return cls(
            advertisement_data.local_name or device.name or device.address,
            device.address,
            advertisement_data.rssi,
            advertisement_data.manufacturer_data,
            advertisement_data.service_data,
            advertisement_data.service_uuids,
            source,
            device,
            advertisement_data,
            connectable,
            time,
        )


KEY_MAP = {
    0: "local_name",
    1: "manufacturer_data",
    2: "service_data",
    3: "service_uuids",
    4: "tx_power",
    5: "rssi",
    6: "platform_data",
}


class _AdvertisementData:
    """Wrapper around the advertisement data upon discovery."""

    __slots__ = (
        "local_name",
        "manufacturer_data",
        "service_data",
        "service_uuids",
        "tx_power",
        "rssi",
        "platform_data",
    )

    def __init__(
        self,
        local_name: str | None,
        manufacturer_data: dict[int, bytes],
        service_data: dict[str, bytes],
        service_uuids: list[str],
        tx_power: int | None,
        rssi: int,
        platform_data: tuple[Any, ...],
    ) -> None:
        """Initialize the advertisement data."""
        self.local_name = local_name
        self.manufacturer_data = manufacturer_data
        self.service_data = service_data
        self.service_uuids = service_uuids
        self.tx_power = tx_power
        self.rssi = rssi
        self.platform_data = platform_data

    def __getitem__(self, index: int) -> Any:
        """Get by index."""
        if not (name := KEY_MAP.get(index)):
            raise IndexError(index)
        return getattr(self, name)

    def __repr__(self) -> str:
        """Return a string representation of the advertisement data."""
        kwargs = []
        if self.local_name:
            kwargs.append(f"local_name={self.local_name!r}")
        if self.manufacturer_data:
            kwargs.append(f"manufacturer_data={self.manufacturer_data!r}")
        if self.service_data:
            kwargs.append(f"service_data={self.service_data!r}")
        if self.service_uuids:
            kwargs.append(f"service_uuids={self.service_uuids!r}")
        if self.tx_power is not None:
            kwargs.append(f"tx_power={self.tx_power!r}")
        kwargs.append(f"rssi={self.rssi!r}")
        return f"AdvertisementData({', '.join(kwargs)})"


class _BLEDevice:
    """A simple wrapper class representing a BLE server detected during scanning."""

    __slots__ = ("address", "name", "details", "_rssi", "_metadata")

    def __init__(
        self, address: str, name: str | None, details: Any, rssi: int, **kwargs: Any
    ) -> None:
        self.address = address
        self.name = name
        self.details = details
        self._rssi = rssi
        self._metadata = kwargs

    @property
    def rssi(self) -> int:
        """Gets the RSSI of the last received advertisement."""
        return self._rssi

    @property
    def metadata(self) -> dict[Any, Any]:
        """Gets the metadata of the device."""
        return self._metadata

    def __str__(self) -> str:
        return f"{self.address}: {self.name}"

    def __repr__(self) -> str:
        return f"BLEDevice({self.address}, {self.name})"


scanner.AdvertisementData = _AdvertisementData
device.BLEDevice = _BLEDevice
