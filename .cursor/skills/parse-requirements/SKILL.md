---
name: parse-requirements
description: Parses a product requirement into a human-reviewable Markdown report with test points, open questions, and functional cases. Use when the user says 需求解析, /需求, or asks to break down requirements for the Baidu sample site or any target URL.
---

# 需求解析

把需求文档或一句话描述整理成给人评审的 Markdown（Human Doc）。不直接写自动化脚本。

样例站点：[百度首页](https://www.baidu.com/)

## 原则

1. 先让人看懂，再谈自动化
2. 测试点按正向 / 逆向 / 边界
3. 模糊点必须进「待确认问题」，不要写死
4. 功能用例只写业务步骤，不编造 selector 或接口路径
5. 结束后提示使用「用例结构化」

## 步骤

1. 识别功能点（打开页面、搜索、结果、异常）
2. 从功能 / UI / 兼容 / 性能补充测试关注点
3. 在说明里可加【维度：…】【方法：等价类|边界值|场景法|错误推测】
4. 导出到 `examples/<site>/requirement.md`

## 百度样例范围

- P0：打开 `https://www.baidu.com/`，搜索入口可见
- 可选：输入关键词后出现建议词或结果
- 不默认覆盖账号登录、广告点击

## 输出模板

见仓库 `examples/baidu/requirement.md`。写完后下一步：**用例结构化**。
