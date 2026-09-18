from pathlib import Path

from src.yaml_runner.schema import load_cases


def test_repo_baidu_case_asset_is_valid():
    path = Path(__file__).resolve().parents[2] / "assets" / "cases" / "baidu_home.yaml"
    cases = load_cases(path)
    assert cases[0]["case_id"] == "TC-BAIDU-001"
    assert "打开 BASE_URL" in cases[0]["steps"]
