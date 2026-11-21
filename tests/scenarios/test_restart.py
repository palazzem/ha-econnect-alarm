from homeassistant.config_entries import ConfigEntryState

from tests.scenarios.runner import ALL_ENDPOINTS, CONNECTION_ERROR, Expect, Scenario, Step


async def test_entities_recover_after_a_restart_while_the_network_is_down(scenario: Scenario) -> None:
    await scenario.run(
        Step(
            "restart while offline",
            cycles=2,
            reload=True,
            replies={ALL_ENDPOINTS: CONNECTION_ERROR},
            expect=Expect(entry_state=ConfigEntryState.SETUP_RETRY),
        ),
        Step("network back", cycles=5, expect=Expect(at_baseline=["*"], entry_state=ConfigEntryState.LOADED)),
    )
