"""The E-connect Alarm Entity."""
import logging

from homeassistant.components.alarm_control_panel import (
    FORMAT_NUMBER,
    AlarmControlPanelEntity,
)
from homeassistant.components.alarm_control_panel.const import (
    SUPPORT_ALARM_ARM_AWAY,
    SUPPORT_ALARM_ARM_HOME,
    SUPPORT_ALARM_ARM_NIGHT,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_ALARM_ARMING, STATE_ALARM_DISARMING
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_ALARM_CODE, DOMAIN, KEY_COORDINATOR, KEY_DEVICE

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_devices):
    """Platform setup with the forwarded config entry."""
    device = hass.data[DOMAIN][entry.entry_id][KEY_DEVICE]
    coordinator = hass.data[DOMAIN][entry.entry_id][KEY_COORDINATOR]
    async_add_devices([EconnectAlarm("Alarm Panel", device, coordinator, entry)])


class EconnectAlarm(CoordinatorEntity, AlarmControlPanelEntity):
    """E-connect alarm entity."""

    def __init__(self, name, device, coordinator, config):
        """Construct."""
        super().__init__(coordinator)
        self._name = name
        self._device = device
        self._config = config

    @property
    def name(self):
        """Return the name of this entity."""
        return self._name

    @property
    def state(self):
        """Return the state of the device."""
        return self._device.state

    @property
    def code_format(self):
        """Define a number code format."""
        return FORMAT_NUMBER

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_ALARM_ARM_HOME | SUPPORT_ALARM_ARM_AWAY | SUPPORT_ALARM_ARM_NIGHT

    async def async_alarm_disarm(self, code=None):
        """Send disarm command."""
        code = code or self._config.data.get(CONF_ALARM_CODE)
        self._device.state = STATE_ALARM_DISARMING
        self.async_write_ha_state()
        await self.hass.async_add_executor_job(self._device.disarm, code)

    async def async_alarm_arm_home(self, code=None):
        """Send arm home command."""
        code = code or self._config.data.get(CONF_ALARM_CODE)
        self._device.state = STATE_ALARM_ARMING
        self.async_write_ha_state()
        await self.hass.async_add_executor_job(self._device.arm, code, [4])

    async def async_alarm_arm_away(self, code=None):
        """Send arm away command."""
        _LOGGER.warning("Not implemented!")

    async def async_alarm_arm_night(self, code=None):
        """Send arm night command."""
        _LOGGER.warning("Not implemented!")

    async def async_alarm_trigger(self, code=None):
        """Send alarm trigger command."""
        _LOGGER.warning("Not implemented!")
