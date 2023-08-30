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

from .const import (
    CONF_AREAS_ARM_HOME,
    CONF_AREAS_ARM_NIGHT,
    DOMAIN,
    KEY_COORDINATOR,
    KEY_DEVICE,
)
from .decorators import set_device_state
from .helpers import parse_areas_config

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_devices):
    """Platform setup with the forwarded config entry."""
    device = hass.data[DOMAIN][entry.entry_id][KEY_DEVICE]
    coordinator = hass.data[DOMAIN][entry.entry_id][KEY_COORDINATOR]
    unique_id = entry.entry_id
    # Optional arming areas
    areas_home = parse_areas_config(entry.options.get(CONF_AREAS_ARM_HOME))
    areas_night = parse_areas_config(entry.options.get(CONF_AREAS_ARM_NIGHT))
    async_add_devices(
        [
            EconnectAlarm(
                "Alarm Panel",
                device,
                coordinator,
                unique_id,
                areas_home=areas_home,
                areas_night=areas_night,
            )
        ]
    )


class EconnectAlarm(CoordinatorEntity, AlarmControlPanelEntity):
    """E-connect alarm entity."""

    def __init__(
        self, name, device, coordinator, unique_id, areas_home=None, areas_night=None
    ):
        """Construct."""
        super().__init__(coordinator)
        self._name = name
        self._device = device
        self._unique_id = unique_id
        self._areas_home = areas_home
        self._areas_night = areas_night

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

    @set_device_state(STATE_ALARM_DISARMING)
    async def async_alarm_disarm(self, code=None):
        """Send disarm command."""
        await self.hass.async_add_executor_job(self._device.disarm, code)

    @set_device_state(STATE_ALARM_ARMING)
    async def async_alarm_arm_away(self, code=None):
        """Send arm away command."""
        await self.hass.async_add_executor_job(self._device.arm, code)

    @set_device_state(STATE_ALARM_ARMING)
    async def async_alarm_arm_home(self, code=None):
        """Send arm home command."""
        if not self._areas_home:
            _LOGGER.warning(
                "Triggering ARM HOME without configuration. Use integration Options to configure it."
            )
            return

        await self.hass.async_add_executor_job(self._device.arm, code, self._areas_home)

    @set_device_state(STATE_ALARM_ARMING)
    async def async_alarm_arm_night(self, code=None):
        """Send arm night command."""
        if not self._areas_night:
            _LOGGER.warning(
                "Triggering ARM NIGHT without configuration. Use integration Options to configure it."
            )
            return

        await self.hass.async_add_executor_job(
            self._device.arm, code, self._areas_night
        )
