from pathlib import Path

from src.yaml_runner.schema import load_cases, load_questions, load_requirements, validate_links

ROOT = Path(__file__).resolve().parents[2]


def test_baidu_hot_entry_asset_is_valid():
    cases = load_cases(ROOT / "assets" / "cases" / "baidu_hot_entry.yaml")
    requirements = load_requirements(ROOT / "assets" / "requirements" / "baidu_hot_entry.yaml")
    questions = load_questions(ROOT / "assets" / "questions" / "baidu_hot_entry.yaml")
    validate_links(cases, requirements)

    by_id = {case["case_id"]: case for case in cases}
    assert list(by_id) == ["TC-ENTRY-001", "TC-ENTRY-002", "TC-ENTRY-003"]
    assert (
        by_id["TC-ENTRY-001"]["automation"]["pytest_nodeid"]
        == "tests/examples/test_baidu_hot_entry.py::test_open_baidu_for_hot_entry"
    )
    assert by_id["TC-ENTRY-002"]["automation"]["status"] == "automated"
    assert (
        by_id["TC-ENTRY-002"]["automation"]["pytest_nodeid"]
        == "tests/examples/test_baidu_hot_entry.py::test_click_hot_entry_to_board"
    )
    assert "platform=pc" in by_id["TC-ENTRY-002"]["expected_results"][0]
    assert by_id["TC-ENTRY-003"]["automation"]["status"] == "manual"
    assert [item["question_id"] for item in questions] == [
        "Q-ENTRY-001",
        "Q-ENTRY-002",
        "Q-ENTRY-003",
        "Q-ENTRY-004",
        "Q-ENTRY-005",
    ]
    assert all(item["status"] == "closed" for item in questions)
    assert all(item["resolution"].strip() for item in questions)
