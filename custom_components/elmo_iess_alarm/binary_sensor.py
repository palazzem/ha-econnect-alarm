"""Module for e-connect binary sensors (sectors and inputs)."""
from elmo import query
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_USERNAME, CONF_ALIAS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from custom_components.elmo_iess_alarm.devices import AlarmDevice

from .const import DOMAIN, KEY_COORDINATOR, KEY_DEVICE


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
        
    # Check if there is an alias in configuration flow and use it for naming
        if "alias" in entry.data:
            name_alias = f"{entry.data[CONF_ALIAS]} {name}"
        else:
            name_alias = f"{entry.data[CONF_USERNAME]} {name}"
            
        sensors.append(EconnectDoorWindowSensor(coordinator, device, unique_id, sector_id, query.SECTORS, name_alias))

    for sensor_id, name in inventory[query.INPUTS].items():
        unique_id = f"{entry.entry_id}_{DOMAIN}_{query.INPUTS}_{sensor_id}"
        
    # Check if there is an alias in configuration flow and use it for naming
        if "alias" in entry.data:
            name_alias = f"{entry.data[CONF_ALIAS]} {name}"
        else:
            name_alias = f"{entry.data[CONF_USERNAME]} {name}"
            
        sensors.append(EconnectDoorWindowSensor(coordinator, device, unique_id, sensor_id, query.INPUTS, name_alias))

    # Retrieve alarm system global status
    alerts = await hass.async_add_executor_job(device._connection.get_status)
    for name, value in alerts.items():
        unique_id = f"{entry.entry_id}_{name}"
        
    # Check if there is an alias in configuration flow and use it for naming
        if "alias" in entry.data:
            name_alias = f"{entry.data[CONF_ALIAS]} {name}"
        else:
            name_alias = f"{entry.data[CONF_USERNAME]} {name}"
            
        sensors.append(EconnectAlertSensor(coordinator, unique_id, name_alias, value))

    async_add_entities(sensors)


class EconnectDoorWindowSensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a e-connect door window sensor."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        device: AlarmDevice,
        unique_id: str,
        sensor_id: int,
        sensor_type: int,
        name: str,
    ) -> None:
        """Construct."""
        super().__init__(coordinator)
        self._device = device
        self._unique_id = unique_id
        self._sensor_id = sensor_id
        self._sensor_type = sensor_type
        self._name = name

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
