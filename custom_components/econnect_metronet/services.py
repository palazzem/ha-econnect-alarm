"""Services that arm, disarm and refresh the alarm panel of a config entry."""

import logging

from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN, KEY_COORDINATOR, KEY_DEVICE
from .decorators import retry_refresh_token_service

_LOGGER = logging.getLogger(__name__)


@retry_refresh_token_service
async def arm_sectors(hass: HomeAssistant, config_id: str, call: ServiceCall):
    """Arm the sectors of the sector entities named in `call`, with the code it carries."""
    _LOGGER.debug(f"Service | Triggered action {call.service}")
    device = hass.data[DOMAIN][config_id][KEY_DEVICE]
    sectors = [device._sectors[x.split(".")[1]] for x in call.data["entity_id"]]
    code = call.data.get("code")
    _LOGGER.debug(f"Service | Arming sectors: {sectors}")
    await hass.async_add_executor_job(device.arm, code, sectors)


@retry_refresh_token_service
async def disarm_sectors(hass: HomeAssistant, config_id: str, call: ServiceCall):
    """Disarm the sectors of the sector entities named in `call`, with the code it carries."""
    _LOGGER.debug(f"Service | Triggered action {call.service}")
    device = hass.data[DOMAIN][config_id][KEY_DEVICE]
    sectors = [device._sectors[x.split(".")[1]] for x in call.data["entity_id"]]
    code = call.data.get("code")
    _LOGGER.debug(f"Service | Disarming sectors: {sectors}")
    await hass.async_add_executor_job(device.disarm, code, sectors)


@retry_refresh_token_service
async def update_state(hass: HomeAssistant, config_id: str, call: ServiceCall):
    """Refresh the panel state of `config_id` now, without waiting for the next poll."""
    _LOGGER.debug(f"Service | Triggered action {call.service}")
    coordinator = hass.data[DOMAIN][config_id][KEY_COORDINATOR]
    _LOGGER.debug("Service | Updating alarm state...")
    await coordinator.async_refresh()
