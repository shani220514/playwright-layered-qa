---
name: write-daily-report
description: Writes a concise test daily report from the day's work notes. Use when the user says 日报生成, asks for a 测试日报, or wants a summary of requirement parsing, YAML, scripts, and Baidu example runs.
---

# 日报生成

根据当日记录生成简短日报。不要编造未执行的数量。

```markdown
# 测试日报 - YYYY-MM-DD

## 今日完成
- [x] 需求：…
- [x] 结构化 YAML：…
- [x] 脚本：…
- [x] 执行：离线单测 / 百度 example

## 发现问题
| ID | 模块 | 描述 | 严重程度 | 状态 |
|----|------|------|----------|------|
|    |      |      |          |      |

## 风险
- 

## 明日计划
- [ ]

## 数据
- 单测：x passed
- example：通过 / 未跑 / 失败
```

## 百度样例填写

- 需求：百度首页访问拆解
- 结构化：`assets/cases/baidu_home.yaml`
- 执行：`pytest tests/unit`；可选 `pytest tests/examples -m example`
