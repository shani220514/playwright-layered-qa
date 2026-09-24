import re
from pathlib import Path

from src.yaml_runner.schema import load_cases, load_questions, load_requirements, validate_links

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_CASES = {
    "TC-BAIDU-001": "test_open_baidu_home",
    "TC-BAIDU-002": "test_click_baidu_hot_search",
    "TC-BAIDU-003": "test_get_hot_search_api",
    "TC-BAIDU-004": "test_validate_hot_search_api",
    "TC-BAIDU-005": "test_weak_network_delay",
    "TC-BAIDU-006": "test_modify_request_params",
    "TC-BAIDU-007": "test_save_request_response",
}


def test_repo_baidu_case_asset_is_valid():
    cases = load_cases(ROOT / "assets" / "cases" / "baidu_home.yaml")
    requirements = load_requirements(ROOT / "assets" / "requirements" / "baidu_home.yaml")
    questions = load_questions(ROOT / "assets" / "questions" / "baidu_home.yaml")
    validate_links(cases, requirements)

    assert cases[0]["case_id"] == "TC-BAIDU-001"
    assert "打开 BASE_URL" in cases[0]["steps"]
    assert {case["case_id"]: case["automation"]["pytest_nodeid"].split("::")[-1] for case in cases} == EXPECTED_CASES

    example = (ROOT / "tests" / "examples" / "test_baidu_home.py").read_text(encoding="utf-8")
    defined = set(re.findall(r"^def (test_\w+)", example, flags=re.M))
    assert set(EXPECTED_CASES.values()) <= defined

    assert questions[0]["question_id"] == "Q-001"
    assert questions[0]["status"] == "open"
