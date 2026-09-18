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
