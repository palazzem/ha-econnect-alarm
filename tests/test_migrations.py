from custom_components.econnect_metronet import async_migrate_entry
from custom_components.econnect_metronet.const import DOMAIN

from .hass.fixtures import MockConfigEntry


async def test_async_no_migrations(mocker, hass, config_entry):
    spy = mocker.spy(hass.config_entries, "async_update_entry")
    # Test
    result = await async_migrate_entry(hass, config_entry)
    assert result is True
    assert spy.call_count == 0


async def test_async_migrate_from_v1(hass):
    config_entry = MockConfigEntry(
        version=1,
        domain=DOMAIN,
        entry_id="test_entry_id",
        options={},
        data={
            "username": "test_user",
            "password": "test_password",
            "domain": "econnect_metronet",
        },
    )
    config_entry.add_to_hass(hass)
    # Test
    result = await async_migrate_entry(hass, config_entry)
    assert result is True
    assert config_entry.version == 3
    assert config_entry.options == {}
    assert config_entry.data == {
        "username": "test_user",
        "password": "test_password",
        "domain": "econnect_metronet",
        "system_base_url": "https://connect.elmospa.com",
    }


async def test_async_migrate_from_v2(hass):
    config_entry = MockConfigEntry(
        version=2,
        domain=DOMAIN,
        entry_id="test_entry_id",
        options={
            "areas_arm_home": "1,2",
            "areas_arm_night": "1,2",
            "areas_arm_vacation": "1,2",
            "scan_interval": 60,
        },
        data={
            "username": "test_user",
            "password": "test_password",
            "domain": "econnect_metronet",
            "system_base_url": "https://example.com",
        },
    )
    config_entry.add_to_hass(hass)
    # Test
    result = await async_migrate_entry(hass, config_entry)
    assert result is True
    assert config_entry.version == 3
    assert config_entry.options == {
        "areas_arm_home": [1, 2],
        "areas_arm_night": [1, 2],
        "areas_arm_vacation": [1, 2],
        "scan_interval": 60,
    }
