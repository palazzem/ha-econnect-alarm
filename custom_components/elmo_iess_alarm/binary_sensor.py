"""Module for e-connect binary sensors (sectors and inputs)."""
from elmo import query
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from custom_components.elmo_iess_alarm.devices import AlarmDevice

from .const import DOMAIN, KEY_COORDINATOR, KEY_DEVICE
from .helpers import generate_entity_id


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up e-connect binary sensors from a config entry."""
    device = hass.data[DOMAIN][entry.entry_id][KEY_DEVICE]
    coordinator = hass.data[DOMAIN][entry.entry_id][KEY_COORDINATOR]
    # Load all entities and register sectors and inputs
    # TODO: use a public API (change in econnect-python)
    # TODO: check why I can't use directly the device (maybe it's not loaded at this time)
    sensors = []
    inventory = await hass.async_add_executor_job(device._connection._get_descriptions)
    for sector_id, name in inventory[query.SECTORS].items():
        unique_id = f"{entry.entry_id}_{DOMAIN}_{query.SECTORS}_{sector_id}"
        sensors.append(EconnectDoorWindowSensor(unique_id, sector_id, entry, name, coordinator, device, query.SECTORS))

    for sensor_id, name in inventory[query.INPUTS].items():
        unique_id = f"{entry.entry_id}_{DOMAIN}_{query.INPUTS}_{sensor_id}"
        sensors.append(EconnectDoorWindowSensor(unique_id, sensor_id, entry, name, coordinator, device, query.INPUTS))

    async_add_entities(sensors)


class EconnectDoorWindowSensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a e-connect door window sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        unique_id: str,
        sensor_id: int,
        config: ConfigEntry,
        name: str,
        coordinator: DataUpdateCoordinator,
        device: AlarmDevice,
        sensor_type: int,
    ) -> None:
        """Construct."""
        super().__init__(coordinator)
        self.entity_id = generate_entity_id(config, name)
        self._name = name
        self._device = device
        self._unique_id = unique_id
        self._sensor_id = sensor_id
        self._sensor_type = sensor_type

    @property
    def unique_id(self) -> str:
        """Return the unique identifier."""
        return self._unique_id

    @property
    def name(self) -> str:
        """Return the name of this entity."""
        return self._name

    @property
    def icon(self) -> str:
        """Return the icon used by this entity."""
        if self._sensor_type == query.SECTORS:
            return "hass:shield-home-outline"
        elif self._sensor_type == query.INPUTS:
            return "hass:electric-switch"
        else:
            return "hass:toggle-switch-off-outline"

    @property
    def is_on(self) -> bool:
        """Return the binary sensor status (on/off)."""
        # TODO: evaluate to expose a device API to get the status of a sensor
        # instead of duplicating this sensor_type check
        if self._sensor_type == query.SECTORS:
            return self._device.sectors_armed.get(self._sensor_id) is not None
        elif self._sensor_type == query.INPUTS:
            return self._device.inputs_alerted.get(self._sensor_id) is not None
        else:
            return False
