from custom_components.econnect_metronet.binary_sensor import AlertSensor
from custom_components.econnect_metronet.const import DOMAIN


class TestExperiments:
    def test_sensor_force_update_default(self, coordinator, config_entry, alarm_device):
        # Ensure the default is to not force any update
        entity = AlertSensor("device_tamper", 7, config_entry, "device_tamper", coordinator, alarm_device)
        assert entity._attr_force_update is False

    def test_sensor_force_update_on(self, hass, coordinator, config_entry, alarm_device):
        # Ensure you can force the entity update
        hass.data[DOMAIN] = {"force_update": True}
        entity = AlertSensor("device_tamper", 7, config_entry, "device_tamper", coordinator, alarm_device)
        assert entity._attr_force_update is True
