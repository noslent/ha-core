"""Binary sensor entities for Midea air conditioners."""

from dataclasses import dataclass
from typing import cast, override

from midealocal.const import DeviceType
from midealocal.devices.ac import DeviceAttributes as ACAttributes, MideaACDevice

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import MideaConfigEntry, MideaEntity

PARALLEL_UPDATES = 0


@dataclass(kw_only=True, frozen=True)
class MideaBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describe a Midea binary sensor entity."""

    attribute: ACAttributes


AC_BINARY_SENSORS: tuple[MideaBinarySensorEntityDescription, ...] = (
    MideaBinarySensorEntityDescription(
        key=ACAttributes.water_pump_running,
        attribute=ACAttributes.water_pump_running,
        translation_key="water_pump",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    MideaBinarySensorEntityDescription(
        key=ACAttributes.full_dust,
        attribute=ACAttributes.full_dust,
        translation_key="filter_warning",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: MideaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Midea binary sensor entities."""
    device = config_entry.runtime_data
    if device.device_type != DeviceType.AC:
        return

    ac_device = cast(MideaACDevice, device)
    async_add_entities(
        MideaBinarySensor(ac_device, description) for description in AC_BINARY_SENSORS
    )


class MideaBinarySensor(MideaEntity, BinarySensorEntity):
    """Representation of Midea AC binary telemetry."""

    entity_description: MideaBinarySensorEntityDescription
    _device: MideaACDevice

    def __init__(
        self,
        device: MideaACDevice,
        entity_description: MideaBinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(device, entity_description)

    @property
    @override
    def is_on(self) -> bool | None:
        """Return the binary sensor state."""
        value = self._device.get_attribute(self.entity_description.attribute)
        return value if isinstance(value, bool) else None
