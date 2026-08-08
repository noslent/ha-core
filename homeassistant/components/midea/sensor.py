"""Sensor entities for Midea air conditioners."""

from dataclasses import dataclass
from typing import cast, override

from midealocal.const import DeviceType
from midealocal.devices.ac import DeviceAttributes as ACAttributes, MideaACDevice

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    REVOLUTIONS_PER_MINUTE,
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import MideaConfigEntry, MideaEntity

PARALLEL_UPDATES = 0


@dataclass(kw_only=True, frozen=True)
class MideaSensorEntityDescription(SensorEntityDescription):
    """Describe a Midea sensor entity."""

    attribute: ACAttributes


AC_SENSORS: tuple[MideaSensorEntityDescription, ...] = (
    MideaSensorEntityDescription(
        key=ACAttributes.outdoor_temperature,
        attribute=ACAttributes.outdoor_temperature,
        translation_key="outdoor_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    MideaSensorEntityDescription(
        key=ACAttributes.realtime_power,
        attribute=ACAttributes.realtime_power,
        translation_key="power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    MideaSensorEntityDescription(
        key=ACAttributes.total_energy_consumption,
        attribute=ACAttributes.total_energy_consumption,
        translation_key="total_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    MideaSensorEntityDescription(
        key=ACAttributes.compressor_frequency,
        attribute=ACAttributes.compressor_frequency,
        translation_key="compressor_frequency",
        device_class=SensorDeviceClass.FREQUENCY,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    MideaSensorEntityDescription(
        key=ACAttributes.compressor_power,
        attribute=ACAttributes.compressor_power,
        translation_key="compressor_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    MideaSensorEntityDescription(
        key=ACAttributes.target_compressor_frequency,
        attribute=ACAttributes.target_compressor_frequency,
        translation_key="target_compressor_frequency",
        device_class=SensorDeviceClass.FREQUENCY,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    MideaSensorEntityDescription(
        key=ACAttributes.compressor_current,
        attribute=ACAttributes.compressor_current,
        translation_key="compressor_current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    MideaSensorEntityDescription(
        key=ACAttributes.compressor_voltage,
        attribute=ACAttributes.compressor_voltage,
        translation_key="compressor_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    *(
        MideaSensorEntityDescription(
            key=attribute,
            attribute=attribute,
            translation_key=translation_key,
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            state_class=SensorStateClass.MEASUREMENT,
            entity_category=EntityCategory.DIAGNOSTIC,
            entity_registry_enabled_default=False,
        )
        for attribute, translation_key in (
            (ACAttributes.indoor_coil_temperature, "indoor_coil_temperature"),
            (ACAttributes.evaporator_temperature, "evaporator_temperature"),
            (ACAttributes.condenser_temperature, "condenser_temperature"),
            (
                ACAttributes.outdoor_ambient_temperature,
                "outdoor_ambient_temperature",
            ),
            (ACAttributes.discharge_pipe_temperature, "discharge_pipe_temperature"),
        )
    ),
    MideaSensorEntityDescription(
        key=ACAttributes.indoor_fan_speed,
        attribute=ACAttributes.indoor_fan_speed,
        translation_key="indoor_fan_speed",
        native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    MideaSensorEntityDescription(
        key=ACAttributes.target_indoor_fan_speed,
        attribute=ACAttributes.target_indoor_fan_speed,
        translation_key="target_indoor_fan_speed",
        native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: MideaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Midea sensor entities."""
    device = config_entry.runtime_data
    if device.device_type != DeviceType.AC:
        return

    ac_device = cast(MideaACDevice, device)
    async_add_entities(
        MideaSensor(ac_device, description) for description in AC_SENSORS
    )


class MideaSensor(MideaEntity, SensorEntity):
    """Representation of Midea AC telemetry."""

    entity_description: MideaSensorEntityDescription
    _device: MideaACDevice

    def __init__(
        self,
        device: MideaACDevice,
        entity_description: MideaSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(device, entity_description)

    @property
    @override
    def native_value(self) -> float | int | None:
        """Return the sensor value."""
        value = self._device.get_attribute(self.entity_description.attribute)
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return None
        return value
