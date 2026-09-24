from pathlib import Path

import pytest

from src.yaml_runner.schema import CaseSchemaError, load_cases


def test_load_cases_reads_required_fields(tmp_path):
    yaml_path = tmp_path / "baidu.yaml"
    yaml_path.write_text(
        """
cases:
  - case_id: TC-BAIDU-001
    module: baidu_home
    title: 打开百度首页
    type: positive
    preconditions: []
    steps:
      - 打开 BASE_URL
    expected_results:
      - 标题包含百度
    source_ref: examples/baidu/requirement.md
    requirement_ids:
      - REQ-BAIDU-001
    automation:
      status: automated
      pytest_nodeid: tests/examples/test_baidu_home.py::test_open_baidu_home
""".strip(),
        encoding="utf-8",
    )

    cases = load_cases(yaml_path)
    assert cases[0]["case_id"] == "TC-BAIDU-001"
    assert cases[0]["steps"] == ["打开 BASE_URL"]
    assert cases[0]["automation"]["status"] == "automated"


def test_load_cases_rejects_missing_case_id(tmp_path):
    yaml_path = tmp_path / "bad.yaml"
    yaml_path.write_text(
        """
cases:
  - module: baidu_home
    title: 缺 id
    type: positive
    preconditions: []
    steps: []
    expected_results: []
    source_ref: x
    requirement_ids: []
    automation:
      status: manual
      pytest_nodeid: null
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(CaseSchemaError, match="case_id"):
        load_cases(yaml_path)


def test_load_cases_missing_file_raises():
    with pytest.raises(CaseSchemaError, match="not found"):
        load_cases(Path("missing.yaml"))


def test_load_cases_rejects_bad_type_and_duplicate_id(tmp_path):
    yaml_path = tmp_path / "bad.yaml"
    yaml_path.write_text(
        """
cases:
  - case_id: TC-1
    module: m
    title: 甲
    type: unknown
    preconditions: []
    steps: ["打开"]
    expected_results: ["可见"]
    source_ref: x
    requirement_ids: []
    automation:
      status: automated
      pytest_nodeid: tests/examples/test_baidu_home.py::test_open_baidu_home
  - case_id: TC-1
    module: m
    title: 乙
    type: positive
    preconditions: []
    steps: ["打开"]
    expected_results: ["可见"]
    source_ref: x
    requirement_ids: []
    automation:
      status: manual
      pytest_nodeid: null
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(CaseSchemaError, match="type"):
        load_cases(yaml_path)


def test_load_cases_rejects_automated_without_nodeid(tmp_path):
    yaml_path = tmp_path / "bad.yaml"
    yaml_path.write_text(
        """
cases:
  - case_id: TC-1
    module: m
    title: 甲
    type: positive
    preconditions: []
    steps: ["打开"]
    expected_results: ["可见"]
    source_ref: x
    requirement_ids: [REQ-1]
    automation:
      status: automated
      pytest_nodeid: null
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(CaseSchemaError, match="pytest_nodeid"):
        load_cases(yaml_path)


def test_load_cases_rejects_unknown_requirement_id(tmp_path):
    cases_path = tmp_path / "cases.yaml"
    req_path = tmp_path / "requirements.yaml"
    cases_path.write_text(
        """
cases:
  - case_id: TC-1
    module: m
    title: 甲
    type: positive
    preconditions: []
    steps: ["打开"]
    expected_results: ["可见"]
    source_ref: x
    requirement_ids: [REQ-MISSING]
    automation:
      status: manual
      pytest_nodeid: null
""".strip(),
        encoding="utf-8",
    )
    req_path.write_text(
        """
requirements:
  - req_id: REQ-1
    module: m
    title: 需求
    type: positive
    description: 说明
    source_ref: x
""".strip(),
        encoding="utf-8",
    )

    from src.yaml_runner.schema import load_requirements, validate_links

    cases = load_cases(cases_path)
    requirements = load_requirements(req_path)
    with pytest.raises(CaseSchemaError, match="REQ-MISSING"):
        validate_links(cases, requirements)
