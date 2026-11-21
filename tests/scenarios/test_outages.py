import pytest

from tests.scenarios.runner import (
    ALL_ENDPOINTS,
    CONNECTION_ERROR,
    READ_TIMEOUT,
    SERVER_ERROR,
    UNAUTHORIZED,
    Expect,
    Reply,
    Scenario,
    Step,
)


@pytest.mark.parametrize(
    "outage",
    [CONNECTION_ERROR, READ_TIMEOUT, UNAUTHORIZED, SERVER_ERROR],
    ids=["connection error", "read timeout", "unauthorized", "server error"],
)
async def test_entities_go_unavailable_during_an_outage_and_recover_their_baseline(
    scenario: Scenario, outage: Reply
) -> None:
    await scenario.run(
        Step("cloud down", cycles=5, replies={ALL_ENDPOINTS: outage}, expect=Expect(unavailable=["*"])),
        Step("cloud back", cycles=5, expect=Expect(at_baseline=["*"])),
    )
