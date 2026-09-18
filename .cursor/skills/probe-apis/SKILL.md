---
name: probe-apis
description: Turns captured XHR/fetch or a short API description into a verification plan with happy path and negative cases. Use when the user says 接口探针, provides Swagger, or has NetworkInterceptor JSON from Baidu.
---

# 接口探针

本框架没有业务 Swagger。优先使用 `NetworkInterceptor` 在打开目标页时抓到的 XHR/fetch。

## 步骤

1. 从 `reports/api-captures/*.json` 或用户提供的 URL/Method 提取接口
2. 列出正常场景
3. 补异常：无鉴权 / 错误参数 / 空值（对公开搜索接口可能不适用，要写明）
4. 输出验证计划，不要把抓包里的 cookie 或个人信息写进仓库

## 百度样例

打开首页后常见请求含建议词、日志或搜索相关 XHR（路径随前端变化）。探针输出只保留：method、path、状态码、是否 JSON。不要提交响应正文到 git。

## 输出

| 项目 | 内容 |
|------|------|
| 来源 | baidu_home.json / 手工描述 |
| Method | GET/POST |
| Path | /sugrec 等 |
| 正常场景 | 状态码 2xx，body 可解析或允许空 |
| 异常场景 | 缺参数、非法 query |

下一步可用拦截器在 UI 步骤前后断言「至少捕获到 xhr/fetch」或特定 path。
