from homeassistant.config_entries import ConfigEntryState

from tests.scenarios.runner import (
    ALL_ENDPOINTS,
    CONNECTION_ERROR,
    IDS_RESET,
    NORMAL,
    PANEL_DISCONNECTED,
    Endpoint,
    Expect,
    Scenario,
    Step,
)

PANEL_OFFLINE = {ALL_ENDPOINTS: PANEL_DISCONNECTED, Endpoint.LOGIN: NORMAL}


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


async def test_entities_recover_after_a_restart_while_the_panel_is_offline(scenario: Scenario) -> None:
    await scenario.run(
        Step("panel offline", cycles=2, replies=PANEL_OFFLINE),
        Step(
            "restart while the panel is offline",
            cycles=2,
            reload=True,
            replies=PANEL_OFFLINE,
            expect=Expect(unavailable=["*"], entry_state=ConfigEntryState.SETUP_RETRY),
        ),
        Step("panel back", cycles=5, expect=Expect(at_baseline=["*"], entry_state=ConfigEntryState.LOADED)),
    )


async def test_entities_recover_after_a_restart_while_the_cloud_reports_reset_ids(scenario: Scenario) -> None:
    await scenario.run(
        Step(
            "restart with reset ids",
            cycles=2,
            reload=True,
            replies={Endpoint.AREAS: IDS_RESET, Endpoint.INPUTS: IDS_RESET, Endpoint.OUTPUTS: IDS_RESET},
            expect=Expect(unavailable=["*"], entry_state=ConfigEntryState.SETUP_RETRY),
        ),
        Step("ids grow again", cycles=5, expect=Expect(at_baseline=["*"], entry_state=ConfigEntryState.LOADED)),
    )
