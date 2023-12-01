from elmo import query as q
from homeassistant.components import persistent_notification
from homeassistant.components.switch import SwitchEntity
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
    NOTIFICATION_IDENTIFIER,
    NOTIFICATION_MESSAGE,
    NOTIFICATION_TITLE,
)
from .devices import AlarmDevice
from .helpers import generate_entity_id


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    device = hass.data[DOMAIN][entry.entry_id][KEY_DEVICE]
    coordinator = hass.data[DOMAIN][entry.entry_id][KEY_COORDINATOR]
    outputs = []

    # Iterate through the outputs of the provided device and create OutputSwitch objects
    for output_id, name in device.outputs:
        unique_id = f"{entry.entry_id}_{DOMAIN}_{q.OUTPUTS}_{output_id}"
        outputs.append(OutputSwitch(unique_id, output_id, entry, name, coordinator, device))

    async_add_entities(outputs)


class OutputSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a e-connect output switch."""

    _attr_has_entity_name = True

    def __init__(
        self,
        unique_id: str,
        output_id: int,
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
        self._output_id = output_id

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
        return "hass:toggle-switch-variant"

    @property
    def is_on(self) -> bool:
        """Return the switch status (on/off)."""
        return bool(self._device.get_status(q.OUTPUTS, self._output_id))

    async def async_turn_off(self):
        """Turn the entity off."""
        # await self.hass.async_add_executor_job(self._device.turn_off, self._output_id)  # pragma: no cover
        if not await self.hass.async_add_executor_job(self._device.turn_off, self._output_id):
            persistent_notification.async_create(
                self.hass, NOTIFICATION_MESSAGE, NOTIFICATION_TITLE, NOTIFICATION_IDENTIFIER
            )

    async def async_turn_on(self):
        """Turn the entity off."""
        # await self.hass.async_add_executor_job(self._device.turn_on, self._output_id)  # pragma: no cover
        if not await self.hass.async_add_executor_job(self._device.turn_on, self._output_id):
            persistent_notification.async_create(
                self.hass, NOTIFICATION_MESSAGE, NOTIFICATION_TITLE, NOTIFICATION_IDENTIFIER
            )
