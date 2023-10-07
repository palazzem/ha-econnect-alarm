"""Module for e-connect binary sensors (sectors, inputs and alert)."""
from elmo import query
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN, KEY_COORDINATOR, KEY_DEVICE
from .devices import AlarmDevice
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
        sensors.append(SectorSensor(unique_id, sector_id, entry, name, coordinator, device))

    for sensor_id, name in inventory[query.INPUTS].items():
        unique_id = f"{entry.entry_id}_{DOMAIN}_{query.INPUTS}_{sensor_id}"
        sensors.append(InputSensor(unique_id, sensor_id, entry, name, coordinator, device))

    # Retrieve alarm system global status
    alerts = await hass.async_add_executor_job(device._connection.get_status)
    for alert_id, _ in alerts.items():
        unique_id = f"{entry.entry_id}_{DOMAIN}_{alert_id}"
        sensors.append(AlertSensor(unique_id, alert_id, entry, coordinator, device))

    async_add_entities(sensors)


class AlertSensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a e-Connect alert binary sensor"""

    _attr_has_entity_name = True

    def __init__(
        self,
        unique_id: str,
        alert_id: str,
        config: ConfigEntry,
        coordinator: DataUpdateCoordinator,
        device: AlarmDevice,
    ) -> None:
        """Construct."""
        super().__init__(coordinator)
        self.entity_id = generate_entity_id(config, alert_id)
        self._unique_id = unique_id
        self._alert_id = alert_id
        self._device = device

    @property
    def unique_id(self) -> str:
        """Return the unique identifier."""
        return self._unique_id

    @property
    def translation_key(self) -> str:
        """Return the translation key to translate the entity's name and states."""
        return self._alert_id

    @property
    def icon(self) -> str:
        """Return the icon used by this entity."""
        return "hass:alarm-light"

    @property
    def device_class(self) -> str:
        """Return the device class."""
        return BinarySensorDeviceClass.PROBLEM

    @property
    def is_on(self) -> bool:
        """Return the sensor status (on/off)."""
        state = self._device.alerts.get(self._alert_id)
        return state > 1 if self._alert_id == "anomalies_led" else state > 0


class InputSensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a e-connect input binary sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        unique_id: str,
        sensor_id: int,
        config: ConfigEntry,
        name: str,
        coordinator: DataUpdateCoordinator,
        device: AlarmDevice,
    ) -> None:
        """Construct."""
        super().__init__(coordinator)
        self.entity_id = generate_entity_id(config, name)
        self._name = name
        self._device = device
        self._unique_id = unique_id
        self._sensor_id = sensor_id

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
        return "hass:electric-switch"

    @property
    def is_on(self) -> bool:
        """Return the binary sensor status (on/off)."""
        return self._device.inputs_alerted.get(self._sensor_id) is not None


class SectorSensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a e-connect sector binary sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        unique_id: str,
        sector_id: int,
        config: ConfigEntry,
        name: str,
        coordinator: DataUpdateCoordinator,
        device: AlarmDevice,
    ) -> None:
        """Construct."""
        super().__init__(coordinator)
        self.entity_id = generate_entity_id(config, name)
        self._name = name
        self._device = device
        self._unique_id = unique_id
        self._sector_id = sector_id

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
        return "hass:shield-home-outline"

    @property
    def is_on(self) -> bool:
        """Return the binary sensor status (on/off)."""
        return self._device.sectors_armed.get(self._sector_id) is not None
