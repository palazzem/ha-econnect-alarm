import pytest

from custom_components.econnect_metronet.api.v1.exceptions import ValidationError
from custom_components.econnect_metronet.api.v1.router import Router


def test_https_is_required():
    """Should accept only HTTPS URLs."""
    with pytest.raises(ValidationError):
        Router("http://connect.elmospa.com")
