import pytest

from custom_components.econnect_metronet.api.v1.exceptions import ParseError
from custom_components.econnect_metronet.api.v1.utils import (
    _camel_to_snake_case,
    _sanitize_session_id,
    extract_session_id_from_html,
)
from tests.fixtures.responses import STATUS_PAGE


def test_sanitize_identifier():
    """Ensure session ID are obfuscated for debug purposes."""
    assert _sanitize_session_id("0fb182e9-474c-ca1c-f60c-ed203dbb26aa") == "0fb182e9-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
    assert _sanitize_session_id("abcdefgh-ijkl-mnop-qrst-uvwxyz012345") == "abcdefgh-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
    assert _sanitize_session_id("12345678-90ab-cdef-ghij-klmnopqrstuv") == "12345678-XXXX-XXXX-XXXX-XXXXXXXXXXXX"


def test_camel_to_snake_case_single_word():
    """Test conversion of a single capitalized word."""
    assert _camel_to_snake_case("Camel") == "camel"


def test_camel_to_snake_case_multiple_words():
    """Test conversion of a camel-cased string with multiple words."""
    assert _camel_to_snake_case("CamelCaseString") == "camel_case_string"


def test_camel_to_snake_case_multiple_words_alt():
    """Test conversion of a camel-cased string with multiple words (alternative)."""
    assert _camel_to_snake_case("camelCaseString") == "camel_case_string"


def test_camel_to_snake_case_single_letter():
    """Test conversion of a single capitalized letter."""
    assert _camel_to_snake_case("C") == "c"


def test_camel_to_snake_case_empty_string():
    """Test conversion of an empty string."""
    assert _camel_to_snake_case("") == ""


def test_camel_to_snake_case_already_snake_case():
    """Test conversion of a string already in snake case."""
    assert _camel_to_snake_case("already_snake_case") == "already_snake_case"


def test_camel_to_snake_case_mixed_casing():
    """Test conversion of a string with mixed casing."""
    assert _camel_to_snake_case("mixedCasing_isHERE") == "mixed_casing_is_here"


def test_camel_to_snake_case_with_numbers():
    """Test conversion of a camel-cased string with numbers."""
    assert _camel_to_snake_case("CamelCase1With2Numbers") == "camel_case_1_with_2_numbers"


def test_camel_to_snake_case_with_symbols():
    """Test conversion of a camel-cased string with numbers."""
    assert _camel_to_snake_case("CamelCase-With-symbols") == "camel_case_with_symbols"


def test_camel_to_snake_case_all_uppercase():
    """Test conversion of an all-uppercase string."""
    assert _camel_to_snake_case("UPPERCASE") == "uppercase"


def test_camel_to_snake_case_cache(mocker):
    """Test that cached values don't call regex twice."""
    mocked_sub = mocker.patch("re.sub")
    _camel_to_snake_case("camelCase")
    _camel_to_snake_case("camelCase")
    assert mocked_sub.call_count == 4


def test_extract_session_id_from_html():
    """Ensure the session ID is extracted from e-Connect status page."""
    html_content = STATUS_PAGE
    assert extract_session_id_from_html(html_content) == "f8h23b4e-7a9f-4d3f-9b08-2769263ee33c"


def test_extract_session_id_from_html_no_session_id():
    """Ensure an error is raised when the session ID is not found in the HTML content."""
    html_content = STATUS_PAGE.replace("var sessionId = 'f8h23b4e-7a9f-4d3f-9b08-2769263ee33c';", "")
    with pytest.raises(ParseError):
        extract_session_id_from_html(html_content)
