from tests.scenarios.runner import ALL_ENDPOINTS, NORMAL, PANEL_DISCONNECTED, Endpoint, Expect, Scenario, Step

EVERY_ENTITY_BUT_CONNECTION_STATUS = [
    "alarm_control_panel.*",
    "sensor.*",
    "switch.*",
    "binary_sensor.*_anomalies_led",
    "binary_sensor.*_device_*",
    "binary_sensor.*_entryway_sensor",
    "binary_sensor.*_gsm_*",
    "binary_sensor.*_has_anomaly",
    "binary_sensor.*_input_*",
    "binary_sensor.*_module_registration",
    "binary_sensor.*_outdoor_sensor_*",
    "binary_sensor.*_panel_*",
    "binary_sensor.*_pstn_anomaly",
    "binary_sensor.*_rf_interference",
    "binary_sensor.*_s[0-9]_*",
    "binary_sensor.*_system_test",
]


async def test_entities_keep_their_state_while_the_panel_is_offline_and_recover_when_it_reconnects(
    scenario: Scenario,
) -> None:
    await scenario.run(
        Step(
            "panel offline",
            cycles=5,
            replies={ALL_ENDPOINTS: PANEL_DISCONNECTED, Endpoint.LOGIN: NORMAL},
            expect=Expect(at_baseline=EVERY_ENTITY_BUT_CONNECTION_STATUS),
        ),
        Step("panel back", cycles=5, expect=Expect(at_baseline=["*"])),
    )
