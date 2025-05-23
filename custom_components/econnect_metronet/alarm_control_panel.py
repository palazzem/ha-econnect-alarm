"""The E-connect Alarm Entity."""

import logging

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelState,
    CodeFormat,
)
from homeassistant.components.alarm_control_panel.const import (
    AlarmControlPanelEntityFeature as AlarmFeatures,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_SYSTEM_NAME, DOMAIN, KEY_COORDINATOR, KEY_DEVICE
from .decorators import retry_refresh_token, set_device_state
from .helpers import generate_entity_id

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_devices):
    """Platform setup with the forwarded config entry."""
    device = hass.data[DOMAIN][entry.entry_id][KEY_DEVICE]
    coordinator = hass.data[DOMAIN][entry.entry_id][KEY_COORDINATOR]
    unique_id = f"{DOMAIN}_{entry.entry_id}"
    async_add_devices(
        [
            EconnectAlarm(
                unique_id,
                entry,
                device,
                coordinator,
            )
        ]
    )


class EconnectAlarm(CoordinatorEntity, AlarmControlPanelEntity):
    """E-connect alarm entity."""

    _attr_has_entity_name = True

    def __init__(self, unique_id, config, device, coordinator):
        """Construct."""
        super().__init__(coordinator)
        self.entity_id = generate_entity_id(config)
        self._config = config
        self._unique_id = unique_id
        self._name = f"Alarm Panel {config.data.get(CONF_SYSTEM_NAME) or config.data.get(CONF_USERNAME)}"
        self._device = device

    @property
    def unique_id(self):
        """Return the unique identifier."""
        return self._unique_id

    @property
    def name(self):
        """Return the name of this entity."""
        return self._name

    @property
    def icon(self):
        """Return the icon used by this entity."""
        return "hass:shield-home"

    @property
    def alarm_state(self):
        """Return the state of the device."""
        return self._device.state

    @property
    def code_format(self):
        """Define a number code format."""
        return CodeFormat.NUMBER

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return AlarmFeatures.ARM_HOME | AlarmFeatures.ARM_AWAY | AlarmFeatures.ARM_NIGHT | AlarmFeatures.ARM_VACATION

    @set_device_state(AlarmControlPanelState.DISARMED, AlarmControlPanelState.DISARMING)
    @retry_refresh_token
    async def async_alarm_disarm(self, code=None):
        """Send disarm command."""
        await self.hass.async_add_executor_job(self._device.disarm, code)

    @set_device_state(AlarmControlPanelState.ARMED_AWAY, AlarmControlPanelState.ARMING)
    @retry_refresh_token
    async def async_alarm_arm_away(self, code=None):
        """Send arm away command."""
        await self.hass.async_add_executor_job(self._device.arm, code, self._device._sectors_away)

    @set_device_state(AlarmControlPanelState.ARMED_HOME, AlarmControlPanelState.ARMING)
    @retry_refresh_token
    async def async_alarm_arm_home(self, code=None):
        """Send arm home command."""
        if not self._device._sectors_home:
            _LOGGER.warning("Triggering ARM HOME without configuration. Use integration Options to configure it.")
            return

        await self.hass.async_add_executor_job(self._device.arm, code, self._device._sectors_home)

    @set_device_state(AlarmControlPanelState.ARMED_NIGHT, AlarmControlPanelState.ARMING)
    @retry_refresh_token
    async def async_alarm_arm_night(self, code=None):
        """Send arm night command."""
        if not self._device._sectors_night:
            _LOGGER.warning("Triggering ARM NIGHT without configuration. Use integration Options to configure it.")
            return

        await self.hass.async_add_executor_job(self._device.arm, code, self._device._sectors_night)

    @set_device_state(AlarmControlPanelState.ARMED_VACATION, AlarmControlPanelState.ARMING)
    @retry_refresh_token
    async def async_alarm_arm_vacation(self, code=None):
        """Send arm vacation command."""
        if not self._device._sectors_vacation:
            _LOGGER.warning("Triggering ARM VACATION without configuration. Use integration Options to configure it.")
            return

        await self.hass.async_add_executor_job(self._device.arm, code, self._device._sectors_vacation)
