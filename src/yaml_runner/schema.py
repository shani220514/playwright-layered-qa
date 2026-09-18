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

    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            raise CaseSchemaError(f"cases[{index}] must be a mapping")
        missing = [field for field in REQUIRED_CASE_FIELDS if field not in case]
        if missing:
            raise CaseSchemaError(
                f"cases[{index}] missing required fields: {', '.join(missing)}"
            )
    return cases
