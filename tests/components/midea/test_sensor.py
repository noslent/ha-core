"""Tests for Midea sensors."""

from collections.abc import Callable

from midealocal.const import DeviceType
from midealocal.devices.ac import DeviceAttributes as ACAttributes
import pytest

from homeassistant.components.sensor import (
    ATTR_STATE_CLASS,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_UNIT_OF_MEASUREMENT,
    PERCENTAGE,
    EntityCategory,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from . import setup_integration
from .conftest import DummyDevice, entity_entries
from .const import TEST_DEVICE_ID

from tests.common import MockConfigEntry


async def test_ac_sensors(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    mock_config_entry: Callable[[DummyDevice], MockConfigEntry],
) -> None:
    """Test AC sensor values, metadata, updates, and device association."""
    device = DummyDevice(
        DeviceType.AC,
        attributes={
            ACAttributes.outdoor_temperature: 12.5,
            ACAttributes.realtime_power: 725.4,
            ACAttributes.total_energy_consumption: 103.25,
        },
    )
    config_entry = mock_config_entry(device)
    await setup_integration(hass, config_entry, device)
    entries = entity_entries(hass, config_entry)

    expected = {
        ACAttributes.outdoor_temperature: (
            "12.5",
            UnitOfTemperature.CELSIUS,
            SensorDeviceClass.TEMPERATURE,
            SensorStateClass.MEASUREMENT,
        ),
        ACAttributes.realtime_power: (
            "725.4",
            UnitOfPower.WATT,
            SensorDeviceClass.POWER,
            SensorStateClass.MEASUREMENT,
        ),
        ACAttributes.total_energy_consumption: (
            "103.25",
            UnitOfEnergy.KILO_WATT_HOUR,
            SensorDeviceClass.ENERGY,
            SensorStateClass.TOTAL_INCREASING,
        ),
    }
    for attribute, (value, unit, device_class, state_class) in expected.items():
        unique_id = f"{TEST_DEVICE_ID}_{attribute}"
        entity_entry = entries[unique_id]
        assert entity_entry.unique_id == unique_id
        assert (state := hass.states.get(entity_entry.entity_id)) is not None
        assert state.state == value
        assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == unit
        assert state.attributes[ATTR_DEVICE_CLASS] == device_class
        assert state.attributes[ATTR_STATE_CLASS] == state_class

    device_entry = device_registry.async_get_device(
        identifiers={("midea", str(TEST_DEVICE_ID))}
    )
    assert device_entry is not None
    assert entries[f"{TEST_DEVICE_ID}_{ACAttributes.realtime_power}"].device_id == (
        device_entry.id
    )

    device.attributes[ACAttributes.realtime_power] = 810.2
    device.notify_update({ACAttributes.realtime_power: 810.2})
    await hass.async_block_till_done()
    power_entity_id = entries[
        f"{TEST_DEVICE_ID}_{ACAttributes.realtime_power}"
    ].entity_id
    assert (power_state := hass.states.get(power_entity_id)) is not None
    assert power_state.state == "810.2"


async def test_unsupported_and_diagnostic_sensors(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_config_entry: Callable[[DummyDevice], MockConfigEntry],
) -> None:
    """Test unsupported telemetry and disabled diagnostic sensors."""
    device = DummyDevice(
        DeviceType.AC,
        attributes={
            ACAttributes.outdoor_temperature: None,
            ACAttributes.realtime_power: None,
            ACAttributes.total_energy_consumption: None,
        },
    )
    config_entry = mock_config_entry(device)
    diagnostic_unique_id = f"{TEST_DEVICE_ID}_{ACAttributes.compressor_frequency}"
    diagnostic_entry = entity_registry.async_get_or_create(
        "sensor",
        "midea",
        diagnostic_unique_id,
        disabled_by=None,
    )
    device.attributes[ACAttributes.compressor_frequency] = 55
    await setup_integration(hass, config_entry, device)
    entries = entity_entries(hass, config_entry)

    outdoor_entry = entries[f"{TEST_DEVICE_ID}_{ACAttributes.outdoor_temperature}"]
    assert (outdoor_state := hass.states.get(outdoor_entry.entity_id)) is not None
    assert outdoor_state.state == "unknown"
    assert outdoor_state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.TEMPERATURE

    diagnostic_entry = entries[diagnostic_unique_id]
    assert diagnostic_entry.entity_category is EntityCategory.DIAGNOSTIC
    assert (state := hass.states.get(diagnostic_entry.entity_id)) is not None
    assert state.state == "55"
    assert state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.FREQUENCY
    assert state.attributes[ATTR_STATE_CLASS] == SensorStateClass.MEASUREMENT

    disabled_entry = entries[f"{TEST_DEVICE_ID}_{ACAttributes.compressor_power}"]
    assert disabled_entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION
    assert hass.states.get(disabled_entry.entity_id) is None


async def test_additional_ac_sensors(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_config_entry: Callable[[DummyDevice], MockConfigEntry],
) -> None:
    """Test additional AC telemetry values and metadata."""
    attributes = {
        ACAttributes.indoor_temperature: 21.5,
        ACAttributes.indoor_humidity: 48,
        ACAttributes.current_energy_consumption: 1.25,
        ACAttributes.total_operating_consumption: 82.75,
        ACAttributes.electrify_time: 2000.5,
        ACAttributes.total_operating_time: 1250.25,
        ACAttributes.current_operating_time: 3.5,
        ACAttributes.error_code: 5,
    }
    device = DummyDevice(DeviceType.AC, attributes=attributes)
    config_entry = mock_config_entry(device)
    diagnostic_attributes = tuple(attributes)[2:]
    for attribute in diagnostic_attributes:
        entity_registry.async_get_or_create(
            "sensor",
            "midea",
            f"{TEST_DEVICE_ID}_{attribute}",
            disabled_by=None,
        )

    await setup_integration(hass, config_entry, device)
    entries = entity_entries(hass, config_entry)
    expected = {
        ACAttributes.indoor_temperature: (
            "21.5",
            UnitOfTemperature.CELSIUS,
            SensorDeviceClass.TEMPERATURE,
            SensorStateClass.MEASUREMENT,
        ),
        ACAttributes.indoor_humidity: (
            "48",
            PERCENTAGE,
            SensorDeviceClass.HUMIDITY,
            SensorStateClass.MEASUREMENT,
        ),
        ACAttributes.current_energy_consumption: (
            "1.25",
            UnitOfEnergy.KILO_WATT_HOUR,
            SensorDeviceClass.ENERGY,
            SensorStateClass.TOTAL,
        ),
        ACAttributes.total_operating_consumption: (
            "82.75",
            UnitOfEnergy.KILO_WATT_HOUR,
            SensorDeviceClass.ENERGY,
            SensorStateClass.TOTAL_INCREASING,
        ),
        ACAttributes.electrify_time: (
            "2000.5",
            UnitOfTime.HOURS,
            SensorDeviceClass.DURATION,
            SensorStateClass.TOTAL_INCREASING,
        ),
        ACAttributes.total_operating_time: (
            "1250.25",
            UnitOfTime.HOURS,
            SensorDeviceClass.DURATION,
            SensorStateClass.TOTAL_INCREASING,
        ),
        ACAttributes.current_operating_time: (
            "3.5",
            UnitOfTime.HOURS,
            SensorDeviceClass.DURATION,
            SensorStateClass.TOTAL,
        ),
    }
    for attribute, (value, unit, device_class, state_class) in expected.items():
        entry = entries[f"{TEST_DEVICE_ID}_{attribute}"]
        assert (state := hass.states.get(entry.entity_id)) is not None
        assert state.state == value
        assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == unit
        assert state.attributes[ATTR_DEVICE_CLASS] == device_class
        assert state.attributes[ATTR_STATE_CLASS] == state_class
        if attribute in diagnostic_attributes:
            assert entry.entity_category is EntityCategory.DIAGNOSTIC

    error_entry = entries[f"{TEST_DEVICE_ID}_{ACAttributes.error_code}"]
    assert error_entry.entity_category is EntityCategory.DIAGNOSTIC
    assert (error_state := hass.states.get(error_entry.entity_id)) is not None
    assert error_state.state == "5"
    assert ATTR_DEVICE_CLASS not in error_state.attributes
    assert ATTR_STATE_CLASS not in error_state.attributes

    device.attributes[ACAttributes.indoor_temperature] = 22.5
    device.notify_update({ACAttributes.indoor_temperature: 22.5})
    await hass.async_block_till_done()
    indoor_entry = entries[f"{TEST_DEVICE_ID}_{ACAttributes.indoor_temperature}"]
    assert (indoor_state := hass.states.get(indoor_entry.entity_id)) is not None
    assert indoor_state.state == "22.5"

    device.attributes[ACAttributes.current_energy_consumption] = None
    device.attributes[ACAttributes.error_code] = 0
    device.notify_update(
        {
            ACAttributes.current_energy_consumption: None,
            ACAttributes.error_code: 0,
        }
    )
    await hass.async_block_till_done()
    current_energy_entry = entries[
        f"{TEST_DEVICE_ID}_{ACAttributes.current_energy_consumption}"
    ]
    assert (state := hass.states.get(current_energy_entry.entity_id)) is not None
    assert state.state == "unknown"
    assert (state := hass.states.get(error_entry.entity_id)) is not None
    assert state.state == "0"


@pytest.mark.parametrize("humidity", [0, 0xFF, None])
async def test_invalid_indoor_humidity(
    hass: HomeAssistant,
    mock_config_entry: Callable[[DummyDevice], MockConfigEntry],
    humidity: int | None,
) -> None:
    """Test invalid indoor humidity values are unavailable."""
    device = DummyDevice(
        DeviceType.AC,
        attributes={ACAttributes.indoor_humidity: humidity},
    )
    config_entry = mock_config_entry(device)
    await setup_integration(hass, config_entry, device)
    entry = entity_entries(hass, config_entry)[
        f"{TEST_DEVICE_ID}_{ACAttributes.indoor_humidity}"
    ]
    assert (state := hass.states.get(entry.entity_id)) is not None
    assert state.state == "unknown"


async def test_additional_diagnostic_sensors_disabled_by_default(
    hass: HomeAssistant,
    mock_config_entry: Callable[[DummyDevice], MockConfigEntry],
) -> None:
    """Test additional diagnostic sensors are disabled by default."""
    device = DummyDevice(DeviceType.AC)
    config_entry = mock_config_entry(device)
    await setup_integration(hass, config_entry, device)
    entries = entity_entries(hass, config_entry)

    for attribute in (
        ACAttributes.current_energy_consumption,
        ACAttributes.total_operating_consumption,
        ACAttributes.electrify_time,
        ACAttributes.total_operating_time,
        ACAttributes.current_operating_time,
        ACAttributes.error_code,
    ):
        entry = entries[f"{TEST_DEVICE_ID}_{attribute}"]
        assert entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION
        assert entry.entity_category is EntityCategory.DIAGNOSTIC
