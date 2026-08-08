"""Tests for Midea binary sensors."""

from collections.abc import Callable

from midealocal.const import DeviceType
from midealocal.devices.ac import DeviceAttributes as ACAttributes

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.const import ATTR_DEVICE_CLASS, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from . import setup_integration
from .conftest import DummyDevice, entity_entries
from .const import TEST_DEVICE_ID

from tests.common import MockConfigEntry


async def test_ac_binary_sensors(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
    mock_config_entry: Callable[[DummyDevice], MockConfigEntry],
) -> None:
    """Test AC binary sensor values, metadata, updates, and association."""
    device = DummyDevice(
        DeviceType.AC,
        attributes={
            ACAttributes.water_pump_running: True,
            ACAttributes.full_dust: False,
        },
    )
    config_entry = mock_config_entry(device)
    pump_unique_id = f"{TEST_DEVICE_ID}_{ACAttributes.water_pump_running}"
    entity_registry.async_get_or_create(
        "binary_sensor", "midea", pump_unique_id, disabled_by=None
    )
    await setup_integration(hass, config_entry, device)
    entries = entity_entries(hass, config_entry)

    pump_entry = entries[pump_unique_id]
    assert pump_entry.unique_id == pump_unique_id
    assert pump_entry.entity_category is EntityCategory.DIAGNOSTIC
    assert (pump_state := hass.states.get(pump_entry.entity_id)) is not None
    assert pump_state.state == "on"
    assert ATTR_DEVICE_CLASS not in pump_state.attributes

    filter_unique_id = f"{TEST_DEVICE_ID}_{ACAttributes.full_dust}"
    filter_entry = entries[filter_unique_id]
    assert filter_entry.unique_id == filter_unique_id
    assert filter_entry.entity_category is EntityCategory.DIAGNOSTIC
    assert (filter_state := hass.states.get(filter_entry.entity_id)) is not None
    assert filter_state.state == "off"
    assert filter_state.attributes[ATTR_DEVICE_CLASS] == BinarySensorDeviceClass.PROBLEM

    device_entry = device_registry.async_get_device(
        identifiers={("midea", str(TEST_DEVICE_ID))}
    )
    assert device_entry is not None
    assert pump_entry.device_id == device_entry.id

    device.attributes[ACAttributes.water_pump_running] = False
    device.attributes[ACAttributes.full_dust] = True
    device.notify_update(
        {
            ACAttributes.water_pump_running: False,
            ACAttributes.full_dust: True,
        }
    )
    await hass.async_block_till_done()
    assert (pump_state := hass.states.get(pump_entry.entity_id)) is not None
    assert pump_state.state == "off"
    assert (filter_state := hass.states.get(filter_entry.entity_id)) is not None
    assert filter_state.state == "on"


async def test_binary_sensor_unavailable_and_disabled_default(
    hass: HomeAssistant,
    mock_config_entry: Callable[[DummyDevice], MockConfigEntry],
) -> None:
    """Test unsupported binary telemetry and default enablement."""
    device = DummyDevice(
        DeviceType.AC,
        attributes={
            ACAttributes.water_pump_running: None,
            ACAttributes.full_dust: None,
        },
    )
    config_entry = mock_config_entry(device)
    await setup_integration(hass, config_entry, device)
    entries = entity_entries(hass, config_entry)

    pump_entry = entries[f"{TEST_DEVICE_ID}_{ACAttributes.water_pump_running}"]
    assert pump_entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION
    assert pump_entry.entity_category is EntityCategory.DIAGNOSTIC

    filter_entry = entries[f"{TEST_DEVICE_ID}_{ACAttributes.full_dust}"]
    assert filter_entry.disabled_by is None
    assert (state := hass.states.get(filter_entry.entity_id)) is not None
    assert state.state == "unknown"
