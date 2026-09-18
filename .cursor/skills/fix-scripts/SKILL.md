---
name: fix-scripts
description: Diagnoses and repairs failing pytest or Playwright scripts. Use when the user says 脚本修复, pastes a traceback, or a Baidu example test fails on locators, waits, or assertions.
---

# 脚本修复

## 失败分类

1. 定位器失效：百度首页可能是 `#kw` 或对话 `textarea`，用逗号组合 locator
2. 断言不匹配：标题文案、语言包
3. 时序：等搜索框 visible，禁止固定 sleep 作为主策略
4. 环境：缺 `BASE_URL`、公网被拦、浏览器未安装

## 步骤

1. 读完整 traceback 与失败截图（`test-results/`）
2. 判断类型并给最小修复
3. 只改失败用例相关代码
4. 说明改点

## 百度样例

首页当前可见搜索入口是 `#chat-textarea`（经典 `#kw` 往往在 DOM 里但不可见）。等待时用 Playwright `locator.or_()`，不要用逗号 CSS + `.first`。

先跑离线单测，再按需跑 example：

```bash
python -m pytest tests/unit -q
python -m pytest tests/examples/test_baidu_home.py -m example
```
