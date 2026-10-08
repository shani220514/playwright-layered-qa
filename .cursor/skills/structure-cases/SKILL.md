---
name: structure-cases
description: Converts a requirement Markdown report into YAML schema under assets/ (requirements, cases, questions). Use when the user says 用例结构化, /结构化, or asks to turn a Human Doc into machine-readable cases.
---

# 用例结构化

把 `examples/*/` 下的需求 Markdown 转成程序可消费的 YAML，包括 `requirement.md` 与 `requirement_<YYYYMMDD_HHMMSS>.md`。不直接生成 pytest 脚本。

## 输出

同一次结构化共用同一个本地时间戳。同一目录、同一秒内重名时，在时间戳后追加 `_2`、`_3`。

```text
assets/requirements/<module>_<YYYYMMDD_HHMMSS>.yaml
assets/cases/<module>_<YYYYMMDD_HHMMSS>.yaml
assets/questions/<module>_<YYYYMMDD_HHMMSS>.yaml   # 若有待确认问题
```

## 规则

1. 保留 `source_ref` 追溯到 Markdown
2. 不要编造 CSS selector 或 API path
3. 待确认问题单独进 questions。Markdown 中该条为 closed 且人工结论非空时，status 为 closed，resolution 等于人工结论。其余为 open，resolution 为 `""`。没有「状态」「人工结论」列的旧文档，全部 open。不要把建议确认写进 resolution，除非人工结论原文就是采纳该建议
4. 标签：`【维度：安全】` → `dimension:security`，`【方法：边界值】` → `method:boundary`

### requirements 必填

`req_id`, `module`, `title`, `type` (positive/negative/boundary), `description`, `source_ref`

命名：`REQ-BAIDU-001`

### cases 必填

`case_id`, `module`, `title`, `type`, `preconditions`, `steps`, `expected_results`, `source_ref`, `requirement_ids`, `automation`

`automation.status`：`manual` / `pending` / `automated`；未自动化时 `pytest_nodeid` 为 `null`

命名：`TC-BAIDU-001`

### questions 必填

`question_id`, `module`, `description`, `suggested_confirmation`, `status`, `source_ref`

可选 `resolution`：人工结论。`open` 时可为 `""`；`closed` 时必须是非空字符串。不要把结论写进 `suggested_confirmation`。

## 百度样例

已提交样例不改名：`examples/baidu/requirement.md` → `assets/cases/baidu_home.yaml`。新生成的 YAML 仍按上面的时间戳文件名保存。

校验：`python -m pytest tests/unit/test_yaml_schema.py tests/unit/test_baidu_case_asset.py`

下一步：**脚本编织**。
