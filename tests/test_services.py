from homeassistant.core import ServiceCall

from custom_components.econnect_metronet import services
from custom_components.econnect_metronet.binary_sensor import SectorBinarySensor
from custom_components.econnect_metronet.const import DOMAIN


async def test_service_arm_sectors(hass, config_entry, alarm_device, coordinator, mocker):
    # Ensure `arm_sectors` activates the correct sectors
    arm = mocker.patch.object(alarm_device, "arm")
    SectorBinarySensor("test_id", 0, config_entry, "S1 Living Room", coordinator, alarm_device)
    SectorBinarySensor("test_id", 2, config_entry, "S3 Outdoor", coordinator, alarm_device)
    hass.data[DOMAIN][config_entry.entry_id] = {
        "device": alarm_device,
        "coordinator": coordinator,
    }
    call = ServiceCall(
        domain=DOMAIN,
        service="arm_sectors",
        data={
            "entity_id": [
                "binary_sensor.econnect_metronet_test_user_s1_living_room",
                "binary_sensor.econnect_metronet_test_user_s3_outdoor",
            ],
            "code": "1234",
        },
    )
    # Test
    await services.arm_sectors(hass, config_entry.entry_id, call)
    assert arm.call_count == 1
    assert arm.call_args[0][0] == "1234"
    assert arm.call_args[0][1] == [1, 3]


async def test_service_disarm_sectors(hass, config_entry, alarm_device, coordinator, mocker):
    # Ensure `disarm_sectors` activates the correct sectors
    disarm = mocker.patch.object(alarm_device, "disarm")
    SectorBinarySensor("test_id", 0, config_entry, "S1 Living Room", coordinator, alarm_device)
    SectorBinarySensor("test_id", 2, config_entry, "S3 Outdoor", coordinator, alarm_device)
    hass.data[DOMAIN][config_entry.entry_id] = {
        "device": alarm_device,
        "coordinator": coordinator,
    }
    call = ServiceCall(
        domain=DOMAIN,
        service="disarm_sectors",
        data={
            "entity_id": [
                "binary_sensor.econnect_metronet_test_user_s1_living_room",
                "binary_sensor.econnect_metronet_test_user_s3_outdoor",
            ],
            "code": "1234",
        },
    )
    # Test
    await services.disarm_sectors(hass, config_entry.entry_id, call)
    assert disarm.call_count == 1
    assert disarm.call_args[0][0] == "1234"
    assert disarm.call_args[0][1] == [1, 3]
