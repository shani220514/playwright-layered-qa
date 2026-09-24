from __future__ import annotations

from pathlib import Path

import yaml

REQUIRED_CASE_FIELDS = (
    "case_id",
    "module",
    "title",
    "type",
    "preconditions",
    "steps",
    "expected_results",
    "source_ref",
    "requirement_ids",
    "automation",
)

REQUIRED_REQUIREMENT_FIELDS = (
    "req_id",
    "module",
    "title",
    "type",
    "description",
    "source_ref",
)

REQUIRED_QUESTION_FIELDS = (
    "question_id",
    "module",
    "description",
    "suggested_confirmation",
    "status",
    "source_ref",
)

CASE_TYPES = {"positive", "negative", "boundary"}
AUTOMATION_STATUSES = {"manual", "pending", "automated"}
QUESTION_STATUSES = {"open", "closed"}


class CaseSchemaError(ValueError):
    """Raised when a YAML case file is missing or invalid."""


def load_cases(path: str | Path) -> list[dict]:
    yaml_path = Path(path)
    if not yaml_path.is_file():
        raise CaseSchemaError(f"YAML case file not found: {yaml_path}")

    payload = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
    cases = payload.get("cases")
    if not isinstance(cases, list):
        raise CaseSchemaError("YAML must contain a top-level 'cases' list")

    seen: set[str] = set()
    for index, case in enumerate(cases):
        label = f"cases[{index}]"
        if not isinstance(case, dict):
            raise CaseSchemaError(f"{label} must be a mapping")
        missing = [field for field in REQUIRED_CASE_FIELDS if field not in case]
        if missing:
            raise CaseSchemaError(f"{label} missing required fields: {', '.join(missing)}")
        _require_text(case["case_id"], f"{label}.case_id")
        if case["case_id"] in seen:
            raise CaseSchemaError(f"duplicate case_id: {case['case_id']}")
        seen.add(case["case_id"])
        for field in ("module", "title", "source_ref"):
            _require_text(case[field], f"{label}.{field}")
        if case["type"] not in CASE_TYPES:
            raise CaseSchemaError(f"{label}.type must be one of: {', '.join(sorted(CASE_TYPES))}")
        for field in ("preconditions", "steps", "expected_results", "requirement_ids"):
            _require_str_list(case[field], f"{label}.{field}")
        _validate_automation(case["automation"], f"{label}.automation")
    return cases


def load_requirements(path: str | Path) -> list[dict]:
    payload = _read_yaml(path)
    items = payload.get("requirements")
    if not isinstance(items, list):
        raise CaseSchemaError("YAML must contain a top-level 'requirements' list")

    seen: set[str] = set()
    for index, item in enumerate(items):
        label = f"requirements[{index}]"
        if not isinstance(item, dict):
            raise CaseSchemaError(f"{label} must be a mapping")
        missing = [field for field in REQUIRED_REQUIREMENT_FIELDS if field not in item]
        if missing:
            raise CaseSchemaError(f"{label} missing required fields: {', '.join(missing)}")
        _require_text(item["req_id"], f"{label}.req_id")
        if item["req_id"] in seen:
            raise CaseSchemaError(f"duplicate req_id: {item['req_id']}")
        seen.add(item["req_id"])
        for field in ("module", "title", "description", "source_ref"):
            _require_text(item[field], f"{label}.{field}")
        if item["type"] not in CASE_TYPES:
            raise CaseSchemaError(f"{label}.type must be one of: {', '.join(sorted(CASE_TYPES))}")
        if "linked_case_ids" in item and item["linked_case_ids"] is not None:
            _require_str_list(item["linked_case_ids"], f"{label}.linked_case_ids")
    return items


def load_questions(path: str | Path) -> list[dict]:
    payload = _read_yaml(path)
    items = payload.get("questions")
    if not isinstance(items, list):
        raise CaseSchemaError("YAML must contain a top-level 'questions' list")

    seen: set[str] = set()
    for index, item in enumerate(items):
        label = f"questions[{index}]"
        if not isinstance(item, dict):
            raise CaseSchemaError(f"{label} must be a mapping")
        missing = [field for field in REQUIRED_QUESTION_FIELDS if field not in item]
        if missing:
            raise CaseSchemaError(f"{label} missing required fields: {', '.join(missing)}")
        _require_text(item["question_id"], f"{label}.question_id")
        if item["question_id"] in seen:
            raise CaseSchemaError(f"duplicate question_id: {item['question_id']}")
        seen.add(item["question_id"])
        for field in ("module", "description", "suggested_confirmation", "source_ref"):
            _require_text(item[field], f"{label}.{field}")
        if item["status"] not in QUESTION_STATUSES:
            raise CaseSchemaError(
                f"{label}.status must be one of: {', '.join(sorted(QUESTION_STATUSES))}"
            )
        _validate_resolution(item, label)
    return items


def validate_links(cases: list[dict], requirements: list[dict]) -> None:
    known = {item["req_id"] for item in requirements}
    case_ids = {case["case_id"] for case in cases}
    for index, case in enumerate(cases):
        for req_id in case["requirement_ids"]:
            if req_id not in known:
                raise CaseSchemaError(
                    f"cases[{index}] requirement_ids references unknown id: {req_id}"
                )
    for index, item in enumerate(requirements):
        for case_id in item.get("linked_case_ids") or []:
            if case_id not in case_ids:
                raise CaseSchemaError(
                    f"requirements[{index}] linked_case_ids references unknown id: {case_id}"
                )


def _read_yaml(path: str | Path) -> dict:
    yaml_path = Path(path)
    if not yaml_path.is_file():
        raise CaseSchemaError(f"YAML file not found: {yaml_path}")
    payload = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise CaseSchemaError(f"YAML root must be a mapping: {yaml_path}")
    return payload


def _validate_resolution(item: dict, label: str) -> None:
    if "resolution" not in item or item["resolution"] is None:
        if item["status"] == "closed":
            raise CaseSchemaError(f"{label}.resolution is required when status is closed")
        return
    if not isinstance(item["resolution"], str):
        raise CaseSchemaError(f"{label}.resolution must be a string")
    if item["status"] == "closed" and not item["resolution"].strip():
        raise CaseSchemaError(f"{label}.resolution is required when status is closed")


def _require_text(value: object, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise CaseSchemaError(f"{label} must be a non-empty string")


def _require_str_list(value: object, label: str) -> None:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise CaseSchemaError(f"{label} must be a list of strings")


def _validate_automation(value: object, label: str) -> None:
    if not isinstance(value, dict):
        raise CaseSchemaError(f"{label} must be a mapping")
    status = value.get("status")
    if status not in AUTOMATION_STATUSES:
        raise CaseSchemaError(
            f"{label}.status must be one of: {', '.join(sorted(AUTOMATION_STATUSES))}"
        )
    nodeid = value.get("pytest_nodeid")
    if status == "automated":
        if not isinstance(nodeid, str) or not nodeid.strip():
            raise CaseSchemaError(f"{label}.pytest_nodeid is required when status is automated")
        return
    if nodeid not in (None, ""):
        raise CaseSchemaError(f"{label}.pytest_nodeid must be null unless status is automated")
