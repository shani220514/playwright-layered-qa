from datetime import date, datetime
from decimal import Decimal

import pytest

from src.assertions.db_match import assert_response_matches_db


def test_same_name_keys_match():
    assert_response_matches_db({"id": 1, "name": "a"}, {"id": 1, "name": "a", "extra": 9})


def test_same_name_empty_intersection_fails():
    with pytest.raises(AssertionError, match="intersection"):
        assert_response_matches_db({"a": 1}, {"b": 2})


def test_field_map_matches_nested_path():
    assert_response_matches_db(
        {"data": {"user": {"name": "Ada"}}},
        {"user_name": "Ada"},
        {"data.user.name": "user_name"},
    )


def test_field_map_missing_path_fails():
    with pytest.raises(AssertionError, match="data.missing"):
        assert_response_matches_db({"data": {}}, {"x": 1}, {"data.missing": "x"})


def test_value_mismatch_message_includes_expected_and_actual():
    with pytest.raises(AssertionError, match="name") as exc:
        assert_response_matches_db({"name": "a"}, {"name": "b"})
    message = str(exc.value)
    assert "b" in message
    assert "a" in message


def test_json_string_body_is_parsed():
    assert_response_matches_db('{"id": 1}', {"id": 1})


def test_invalid_json_string_fails():
    with pytest.raises(AssertionError, match="JSON"):
        assert_response_matches_db("{bad", {"id": 1})


def test_normalize_decimal_and_date():
    assert_response_matches_db(
        {"amount": 10, "day": "2026-09-24", "ts": "2026-09-24T12:00:00"},
        {
            "amount": Decimal("10"),
            "day": date(2026, 9, 24),
            "ts": datetime(2026, 9, 24, 12, 0, 0),
        },
    )


def test_no_loose_string_number_coercion():
    with pytest.raises(AssertionError):
        assert_response_matches_db({"id": "1"}, {"id": 1})
