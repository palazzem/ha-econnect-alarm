import json

import pytest

from tests.scenarios.runner import Edited

LIST_BODY = json.dumps(
    [
        {"Id": 7, "Index": 0, "InUse": True},
        {"Id": 8, "Index": 1, "InUse": True},
        {"Id": 9, "Index": 2, "InUse": True},
    ]
)
OBJECT_BODY = json.dumps({"HasChanges": True, "Areas": True, "Inputs": True})


def test_edited_sets_fields_on_every_entry_without_a_predicate() -> None:
    status, body = Edited({"Id": 1}).answer(LIST_BODY)

    assert status == 200
    assert json.loads(body) == [
        {"Id": 1, "Index": 0, "InUse": True},
        {"Id": 1, "Index": 1, "InUse": True},
        {"Id": 1, "Index": 2, "InUse": True},
    ]


def test_edited_sets_fields_only_on_the_entries_its_predicate_selects() -> None:
    reply = Edited({"InUse": False}, where=lambda entry: entry["Index"] == 1)

    status, body = reply.answer(LIST_BODY)

    assert status == 200
    assert json.loads(body) == [
        {"Id": 7, "Index": 0, "InUse": True},
        {"Id": 8, "Index": 1, "InUse": False},
        {"Id": 9, "Index": 2, "InUse": True},
    ]


def test_edited_sets_only_the_named_keys_on_an_object_body() -> None:
    status, body = Edited({"Areas": False}).answer(OBJECT_BODY)

    assert status == 200
    assert json.loads(body) == {"HasChanges": True, "Areas": False, "Inputs": True}


def test_edited_rejects_a_predicate_on_an_object_body() -> None:
    reply = Edited({"Areas": False}, where=lambda entry: True)

    with pytest.raises(TypeError):
        reply.answer(OBJECT_BODY)
