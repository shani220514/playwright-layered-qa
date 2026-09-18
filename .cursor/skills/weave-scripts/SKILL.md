---
name: weave-scripts
description: Weaves YAML cases into pytest + Playwright script skeletons using BasePage, Config, and NetworkInterceptor. Use when the user says 脚本编织, 用例编织, /编织, or asks to generate UI tests from assets/cases.
---

# 脚本编织

从 `assets/cases/*.yaml` 生成 pytest 骨架。不要从自由文本猜 URL、账号或 locator。

## 输入

- 必选：`assets/cases/*.yaml`
- 可选：`assets/requirements/*.yaml`、`assets/questions/*.yaml`
- 复用：`src/core/base_page.py`、`src/core/config.py`、`src/interceptors/network_interceptor.py`、`tests/conftest.py`

## 输出

```text
src/pages/<page>.py
tests/examples/test_<feature>.py
```

## 原则

1. URL 只来自 `Config.from_env()` / `BASE_URL`
2. docstring 写明 `case_id` 与 `requirement_ids`
3. open question 未关闭时只生成 skip 或注释风险，不补业务
4. 需要观察接口时：`NetworkInterceptor().start_capture(page)`，goto 之前启动
5. 示例测试打上 `@pytest.mark.example`，默认 CI 不跑活站点

## 百度样例

`TC-BAIDU-001` → `tests/examples/test_baidu_home.py`：

1. 启动拦截器
2. `BaiduHomePage.open(config.base_url)`
3. 断言标题含「百度」
4. `interceptor.save("baidu_home.json")`

运行：

```bash
copy env.example .env
python -m pytest tests/examples/test_baidu_home.py -m example --headed
```
