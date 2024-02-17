import logging

from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN, KEY_DEVICE

_LOGGER = logging.getLogger(__name__)


async def arm_sectors(hass: HomeAssistant, config_id: str, call: ServiceCall):
    _LOGGER.debug(f"Service | Triggered action {call.service}")
    device = hass.data[DOMAIN][config_id][KEY_DEVICE]
    sectors = [device._sectors[x.split(".")[1]] for x in call.data["entity_id"]]
    code = call.data.get("code")
    _LOGGER.debug(f"Service | Arming sectors: {sectors} with code {code})")
    await hass.async_add_executor_job(device.arm, code, sectors)


async def disarm_sectors(hass: HomeAssistant, config_id: str, call: ServiceCall):
    _LOGGER.debug(f"Service | Triggered action {call.service}")
    device = hass.data[DOMAIN][config_id][KEY_DEVICE]
    sectors = [device._sectors[x.split(".")[1]] for x in call.data["entity_id"]]
    code = call.data.get("code")
    _LOGGER.debug(f"Service | Arming sectors: {sectors} with code {code})")
    await hass.async_add_executor_job(device.disarm, code, sectors)
