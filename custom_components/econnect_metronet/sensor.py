"""Module for e-connect sensors (alert) """

from elmo import query as q
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import (
    CONF_EXPERIMENTAL,
    CONF_FORCE_UPDATE,
    DOMAIN,
    KEY_COORDINATOR,
    KEY_DEVICE,
)
from .devices import AlarmDevice
from .helpers import generate_entity_id


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up e-connect sensors from a config entry."""
    device = hass.data[DOMAIN][entry.entry_id][KEY_DEVICE]
    coordinator = hass.data[DOMAIN][entry.entry_id][KEY_COORDINATOR]
    # Load all entities and register sectors and inputs

    sensors = []

    # Iterate through the alerts of the provided device and create AlertSensor objects
    # only for alarm_led, inputs_led and tamper_led
    for alert_id, name in device.alerts:
        if name in ["alarm_led", "inputs_led", "tamper_led"]:
            unique_id = f"{entry.entry_id}_{DOMAIN}_{q.ALERTS}_{alert_id}"
            sensors.append(AlertSensor(unique_id, alert_id, entry, name, coordinator, device))

    async_add_entities(sensors)


class AlertSensor(CoordinatorEntity, SensorEntity):
    """Representation of a e-Connect alert sensor"""

    _attr_has_entity_name = True

    def __init__(
        self,
        unique_id: str,
        alert_id: int,
        config: ConfigEntry,
        name: str,
        coordinator: DataUpdateCoordinator,
        device: AlarmDevice,
    ) -> None:
        """Construct."""
        # Enable experimental settings from the configuration file
        experimental = coordinator.hass.data[DOMAIN].get(CONF_EXPERIMENTAL, {})
        self._attr_force_update = experimental.get(CONF_FORCE_UPDATE, False)

        super().__init__(coordinator)
        self.entity_id = generate_entity_id(config, name)
        self._name = name
        self._device = device
        self._unique_id = unique_id
        self._alert_id = alert_id

    @property
    def unique_id(self) -> str:
        """Return the unique identifier."""
        return self._unique_id

    @property
    def translation_key(self) -> str:
        """Return the translation key to translate the entity's name and states."""
        return self._name

    @property
    def icon(self) -> str:
        """Return the icon used by this entity."""
        return "hass:alarm-light"

    @property
    def native_value(self) -> int | None:
        return self._device.get_status(q.ALERTS, self._alert_id)
