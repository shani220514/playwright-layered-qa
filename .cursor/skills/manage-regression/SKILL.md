---
name: manage-regression
description: Builds a prioritized regression checklist and execution plan in Markdown. Use when the user says 回归管理, /回归, or asks what to retest after a homepage or interceptor change.
---

# 回归管理

## 步骤

1. 识别变更模块（框架内核 / 拦截器 / YAML / 页面对象）
2. 按 P0/P1 列回归项
3. 标明自动化还是手工
4. 用任务列表跟踪

## 输出模板

```markdown
# 回归测试方案

## 变更分析
| 项目 | 内容 |
|------|------|
| 变更类型 | 功能新增 / 修复 / 重构 |
| 模块 | |
| 影响范围 | |

## P0
- [ ] REG-001 离线单测 `tests/unit`
- [ ] REG-002 打开百度首页 example（本地）
- [ ] REG-003 拦截器仍能导出 JSON

## P1
- [ ] YAML schema 样例仍能 load_cases
```

## 百度样例

改了 `BaiduHomePage` 或 `NetworkInterceptor` 后：先 `pytest tests/unit`，再本地 `-m example` 打开 https://www.baidu.com/ 。
