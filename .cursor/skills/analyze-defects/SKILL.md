---
name: analyze-defects
description: Analyzes a failure and writes a standard defect report with root-cause reasoning. Use when the user says 缺陷分析, or provides logs, screenshots, or interceptor JSON from a failed run.
---

# 缺陷分析

## 步骤

1. 判断类型：前端展示 / 后端接口 / 环境网络 / 测试数据 / 脚本本身
2. 写出推理，再下结论
3. 按模板提单；脚本问题走「脚本修复」，产品问题才当缺陷

## 模板

### 根因分析

【推理过程】…

### 缺陷报告

| 字段 | 内容 |
|------|------|
| 标题 | 【模块】简述 |
| 严重程度 | P0/P1/P2/P3 |
| 复现步骤 | 1. … |
| 预期 | |
| 实际 | |
| 建议修复 | |

## 百度样例

标题不含「百度」、搜索框超时：先排除网络与选择器，再判断是否首页改版。拦截器 JSON 为空不一定是缺陷，静态资源会被过滤器丢掉。
