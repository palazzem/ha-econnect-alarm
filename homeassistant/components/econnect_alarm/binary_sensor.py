"""Module for e-connect binary sensors (sectors and inputs)."""
import logging

from elmo import query

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN, KEY_COORDINATOR, KEY_DEVICE

_LOGGER = logging.getLogger(__name__)


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
    sensors = []
    inventory = device._connection._get_descriptions()
    for sector_id, name in inventory[query.SECTORS].items():
        unique_id = f"{entry.entry_id}_{query.SECTORS}_{sector_id}"
        sensors.append(
            EconnectDoorWindowSensor(
                coordinator, unique_id, sector_id, query.SECTORS, name
            )
        )

    for sensor_id, name in inventory[query.INPUTS].items():
        unique_id = f"{entry.entry_id}_{query.INPUTS}_{sensor_id}"
        sensors.append(
            EconnectDoorWindowSensor(
                coordinator, unique_id, sensor_id, query.INPUTS, name
            )
        )

    async_add_entities(sensors)


class EconnectDoorWindowSensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a e-connect door window sensor."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        unique_id: str,
        sensor_id: int,
        sensor_type: int,
        name: str,
    ) -> None:
        """Construct."""
        super().__init__(coordinator)
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
        # TODO: retrieve the real status
        return True
