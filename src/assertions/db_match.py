from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any


def assert_response_matches_db(
    response_json: Any,
    db_row: dict,
    field_map: dict[str, str] | None = None,
) -> None:
    response = _as_mapping(response_json)
    if not isinstance(db_row, dict):
        raise AssertionError(f"db_row must be a dict (got {type(db_row).__name__})")

    if field_map:
        pairs = []
        for response_path, column in field_map.items():
            actual = _dig(response, response_path)
            if column not in db_row:
                raise AssertionError(f"db column missing: {column}")
            pairs.append((response_path, column, actual, db_row[column]))
    else:
        shared = sorted(set(response) & set(db_row))
        if not shared:
            raise AssertionError(
                "No shared keys between response and db_row "
                f"(response keys={sorted(response)}, db keys={sorted(db_row)}); "
                "intersection is empty"
            )
        pairs = [(key, key, response[key], db_row[key]) for key in shared]

    mismatches = []
    for label, column, actual, expected in pairs:
        norm_actual = _normalize(actual)
        norm_expected = _normalize(expected)
        if norm_actual != norm_expected:
            mismatches.append(
                f"{label} (column {column}): expected {norm_expected!r} from db, "
                f"got {norm_actual!r} from response"
            )
    if mismatches:
        raise AssertionError("response/db mismatch:\n" + "\n".join(mismatches))


def _as_mapping(value: Any) -> dict:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            raise AssertionError(f"response body is not valid JSON: {exc}") from exc
        if not isinstance(parsed, dict):
            raise AssertionError(
                f"response JSON must be an object (got {type(parsed).__name__})"
            )
        return parsed
    raise AssertionError(
        f"response_json must be a dict or JSON object string (got {type(value).__name__})"
    )


def _dig(data: dict, path: str) -> Any:
    current: Any = data
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            raise AssertionError(f"response path missing: {path}")
        current = current[part]
    return current


def _normalize(value: Any) -> Any:
    if isinstance(value, Decimal):
        if value == value.to_integral_value():
            return int(value)
        return float(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value
