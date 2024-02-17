import logging

from elmo import query as q
from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN, KEY_DEVICE

_LOGGER = logging.getLogger(__name__)


async def arm_sectors(hass: HomeAssistant, config_id: str, call: ServiceCall):
    _LOGGER.debug(f"Service | Triggered action {call.service}")
    device = hass.data[DOMAIN][config_id][KEY_DEVICE]
    registry = hass.data["binary_sensor"].entities.mapping
    code = call.data.get("code")
    # Retrieve sectors identifier (element) from provided entity ids
    # NOTE: this step can be avoided if the entity_id mapping is stored in the device object
    entities = [registry[entity] for entity in call.data["entity_id"]]
    sectors = [
        [item["element"] for id, item in device.items(q.SECTORS) if id == entity._sector_id] for entity in entities
    ]
    _LOGGER.debug(f"Service | Arming sectors: {sectors} with code {code})")
    await hass.async_add_executor_job(device.arm, code, sectors)


async def disarm_sectors(hass: HomeAssistant, config_id: str, call: ServiceCall):
    _LOGGER.debug(f"Service | Triggered action {call.service}")
    device = hass.data[DOMAIN][config_id][KEY_DEVICE]
    registry = hass.data["binary_sensor"].entities.mapping
    code = call.data.get("code")
    # Retrieve sectors identifier (element) from provided entity ids
    # NOTE: this step can be avoided if the entity_id mapping is stored in the device object
    entities = [registry[entity] for entity in call.data["entity_id"]]
    sectors = [
        [item["element"] for id, item in device.items(q.SECTORS) if id == entity._sector_id] for entity in entities
    ]
    _LOGGER.debug(f"Service | Arming sectors: {sectors} with code {code})")
    await hass.async_add_executor_job(device.disarm, code, sectors)
