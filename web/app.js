const TYPE_LABEL = { positive: "正向", negative: "反向", boundary: "边界" };
const AUTO_LABEL = { automated: "已自动化", pending: "待自动化", manual: "手工" };
const QUESTION_LABEL = { open: "未关闭", closed: "已关闭" };
const REPORT_KIND = {
  pytest: "执行报告",
  daily: "测试日报",
  defect: "缺陷报告",
  fix: "修复说明",
  regression: "回归清单",
  markdown: "Markdown",
};

const DB_LABEL = {
  configured: "已配置",
  partial: "未配齐",
  absent: "未配置",
};

const ICONS = {
  doc: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 3.5h7l5 5V20a1.5 1.5 0 0 1-1.5 1.5h-10.5A1.5 1.5 0 0 1 5.5 20V5A1.5 1.5 0 0 1 7 3.5z"/><path d="M14 3.5V9h5.5M8.5 13h7M8.5 17h5"/></svg>',
  list: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="M8 7h11M8 12h11M8 17h11"/><path d="M4.5 7h.01M4.5 12h.01M4.5 17h.01"/></svg>',
  link: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="M10 13a5 5 0 0 0 7.1.1l2.1-2.1a5 5 0 0 0-7.1-7.1L10.8 5"/><path d="M14 11a5 5 0 0 0-7.1-.1L4.8 13a5 5 0 0 0 7.1 7.1L13.2 19"/></svg>',
  monitor: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/></svg>',
  wrench: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14.5 6.5a4 4 0 0 0-5.3 5.3L4 17v3h3l5.2-5.2a4 4 0 0 0 5.3-5.3L15 12l-3-3z"/></svg>',
  refresh: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 12a8 8 0 1 1-2.3-5.6"/><path d="M20 4v5h-5"/></svg>',
  message: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 17.5 3.5 20V6.5A2 2 0 0 1 5.5 4.5h13a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2z"/></svg>',
  gear: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="3"/><path d="M12 3v2.2M12 18.8V21M3 12h2.2M18.8 12H21M5.6 5.6l1.6 1.6M16.8 16.8l1.6 1.6M18.4 5.6l-1.6 1.6M7.2 16.8 5.6 18.4"/></svg>',
  report: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8 3.5h6l5 5V20a1.5 1.5 0 0 1-1.5 1.5H8A1.5 1.5 0 0 1 6.5 20V5A1.5 1.5 0 0 1 8 3.5z"/><path d="M14 3.5V9h5M9 13h6M9 17h4"/></svg>',
};

const CARDS = [
  {
    href: "#/skills/parse-requirements",
    title: "需求解析",
    summary: "把需求整理成可评审的测试点",
    tone: "tone-blue",
    icon: ICONS.doc,
  },
  {
    href: "#/assets",
    title: "用例资产",
    summary: "查看需求、用例和待确认问题",
    tone: "tone-green",
    icon: ICONS.list,
  },
  {
    href: "#/skills/probe-apis",
    title: "接口探针",
    summary: "从接口文档或抓包整理契约",
    tone: "tone-orange",
    icon: ICONS.link,
  },
  {
    href: "#/skills/weave-scripts",
    title: "UI 脚本",
    summary: "查看已编写的 pytest 脚本",
    tone: "tone-indigo",
    icon: ICONS.monitor,
  },
  {
    href: "#/failures",
    title: "修复与缺陷",
    summary: "脚本问题做修复，产品问题写缺陷",
    tone: "tone-rose",
    icon: ICONS.wrench,
  },
  {
    href: "#/skills/manage-regression",
    title: "回归清单",
    summary: "按变更模块列出要复测的范围",
    tone: "tone-cyan",
    icon: ICONS.refresh,
  },
  {
    href: "#/reports",
    title: "测试报告",
    summary: "查看 pytest 和 Markdown 报告",
    tone: "tone-violet",
    icon: ICONS.report,
  },
  {
    href: "#/config",
    title: "环境配置",
    summary: "查看地址和数据库是否已配置",
    tone: "tone-slate",
    icon: ICONS.gear,
  },
];

const SKILLS = {
  "parse-requirements": {
    title: "需求解析",
    lede: "这一步在 Cursor 里完成。页面只说明输入和输出，不读取上传文件，也不生成报告。",
    facts: [
      ["做什么", "把需求文档或一段功能说明整理成给人评审的 Markdown。"],
      ["输入", "需求文档，或一句话功能说明。"],
      ["输出", "examples/<站点>/requirement.md"],
      ["怎么说", "需求解析，或 /需求"],
    ],
  },
  "probe-apis": {
    title: "接口探针",
    lede: "探针报告仍然由 Skill 在 Cursor 里写。这里只列出本机已经留下的抓包文件名，不打开文件内容。",
    facts: [
      ["做什么", "把接口文档、OpenAPI 或抓包整理成可评审的契约、断言字段和场景。"],
      ["输入", "接口文档、抓包 JSON、HAR，或 Apifox / OpenAPI 链接。"],
      ["输出", "给人评审的接口探针报告，之后再交给用例结构化。"],
      ["怎么说", "接口探针，或 /探针"],
    ],
    captures: true,
  },
  "weave-scripts": {
    title: "UI 脚本",
    lede: "下面列出用例里已经写上 pytest_nodeid 的脚本。还没有脚本的用例单独放在后面。页面不运行这些测试。",
    facts: [
      ["怎么说", "要新写脚本时，在 Cursor 里说：脚本编织，或 /编织"],
    ],
    scripts: true,
  },
  "manage-regression": {
    title: "回归清单",
    lede: "清单由 Skill 按这次变更来写。页面不保存历史回归记录。",
    facts: [
      ["做什么", "指出这次改动后要复测的模块和用例。"],
      ["输入", "变更说明，例如首页、拦截器或 YAML。"],
      ["输出", "按优先级排列的回归清单。"],
      ["怎么说", "回归管理，或 /回归"],
    ],
  },
};

let renderToken = 0;

window.addEventListener("hashchange", () => {
  closeReport();
  render();
});

document.addEventListener("click", (event) => {
  const opener = event.target.closest("[data-report]");
  if (opener) {
    openReport(opener.dataset.report);
    return;
  }
  if (event.target.closest("[data-close-modal]")) {
    closeReport();
  }
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") closeReport();
});

render();

async function render() {
  const token = ++renderToken;
  const app = document.querySelector("#app");
  const path = decodeHash();
  let html = "";
  try {
    if (path === "/") html = renderHub();
    else if (path === "/assets") html = await renderAssets();
    else if (path.startsWith("/modules/")) html = await renderModule(path.slice("/modules/".length));
    else if (path === "/config") html = await renderConfig();
    else if (path === "/failures" || path === "/skills/fix-scripts" || path === "/skills/analyze-defects") html = renderFailures();
    else if (path === "/reports") html = await renderReports();
    else if (path.startsWith("/skills/")) html = await renderSkill(path.slice("/skills/".length));
    else html = renderMissing("没有这个页面");
  } catch (error) {
    html = renderMissing(error.message || "读取失败");
  }
  if (token !== renderToken) return;
  app.innerHTML = html;
  document.title = document.querySelector("h1")?.textContent || "分层测试台";
}

function renderHub() {
  const cards = CARDS.map((card) => `
    <a class="card" href="${esc(card.href)}">
      <span class="icon ${esc(card.tone)}">${card.icon}</span>
      <h2>${esc(card.title)}</h2>
      <p>${esc(card.summary)}</p>
    </a>`).join("");
  return shell("", `
    <header class="hero">
      <h1>分层测试台</h1>
      <p>需求、用例和脚本留在本仓库，生成仍在 Cursor 里完成</p>
    </header>
    <section class="grid">${cards}</section>
    <p class="footnote">页面不执行用例，也不调用 Skill。</p>`);
}

async function renderAssets() {
  const catalog = await getJson("/api/catalog");
  const cards = catalog.modules.map((item) => {
    const open = item.open_question_count
      ? `<li class="alert">未关闭 ${esc(item.open_question_count)}</li>`
      : "";
    return `
      <a class="module-link" href="#/modules/${encodeURIComponent(item.module)}">
        <h2>${esc(item.module)}</h2>
        <ul class="stats">
          <li>需求 ${esc(item.requirement_count)}</li>
          <li>用例 ${esc(item.case_count)}</li>
          <li>问题 ${esc(item.question_count)}</li>
          ${open}
          ${automationStats(item.automation)}
        </ul>
      </a>`;
  }).join("");
  const errors = catalog.errors.length
    ? `<div class="banner"><strong>有 YAML 没通过校验</strong><ul>${catalog.errors.map((item) => `<li>${esc(item)}</li>`).join("")}</ul></div>`
    : "";
  const body = catalog.modules.length
    ? `<div class="module-grid">${cards}</div>`
    : `<p class="notice">assets/ 里还没有模块。</p>`;
  return shell(backLink(), `
    <h1 class="page-title">用例资产</h1>
    <p class="lede">数据来自 assets/ 下的需求、用例和待确认问题。步骤只供阅读。</p>
    ${errors}
    ${body}`);
}

async function renderModule(module) {
  if (!module || module.includes("/") || module.includes("\\")) {
    return renderMissing("模块名无效");
  }
  const detail = await getJson("/api/modules/" + encodeURIComponent(module));
  const warnings = detail.link_warnings.length
    ? `<div class="banner"><strong>引用没有对上</strong><ul>${detail.link_warnings.map((item) => `<li>${esc(item)}</li>`).join("")}</ul></div>`
    : "";
  return shell(backLink("#/assets"), `
    <h1 class="page-title">${esc(detail.module)}</h1>
    <p class="lede">需求 ${esc(detail.requirements.length)} · 用例 ${esc(detail.cases.length)} · 问题 ${esc(detail.questions.length)}</p>
    ${warnings}
    <div class="columns">
      ${column("需求", detail.requirements, renderRequirement)}
      ${column("用例", detail.cases, renderCase)}
      ${column("待确认问题", detail.questions, renderQuestion)}
    </div>`, true);
}

async function renderSkill(id) {
  const skill = SKILLS[id];
  if (!skill) return renderMissing("没有这个入口");
  const facts = skill.facts.map(([name, value]) => `
    <div><dt>${esc(name)}</dt><dd>${esc(value)}</dd></div>`).join("");
  let extra = "";
  if (skill.captures) {
    const payload = await getJson("/api/captures");
    extra = payload.files.length
      ? `<h2>本机抓包</h2><ul class="file-list">${payload.files.map((name) => `<li><code>${esc(name)}</code></li>`).join("")}</ul>`
      : `<p class="muted">reports/api-captures/ 里还没有抓包文件。</p>`;
  }
  let scripts = "";
  if (skill.scripts) {
    scripts = await renderScriptList();
  }
  return shell(backLink(), `
    <h1 class="page-title">${esc(skill.title)}</h1>
    <p class="lede">${esc(skill.lede)}</p>
    <section class="panel">
      <dl class="facts">${facts}</dl>
      ${extra}
    </section>
    ${scripts}`);
}

function renderFailures() {
  return shell(backLink(), `
    <h1 class="page-title">修复与缺陷</h1>
    <p class="lede">同一次失败先分清原因。脚本写错走修复，产品行为不对才写缺陷。页面不执行修复，也不在这里生成文件。</p>
    <div class="pair">
      <section class="panel">
        <h2>脚本修复</h2>
        <p class="meta">定位器、等待、断言或环境不对时走这里。</p>
        <dl class="facts">
          <div><dt>输入</dt><dd>pytest traceback，或 test-results/ 里的失败截图。</dd></div>
          <div><dt>输出</dt><dd>最小修改。说明可存成 reports/脚本修复_时间.md。</dd></div>
          <div><dt>怎么说</dt><dd>在 Cursor 里说：脚本修复</dd></div>
        </dl>
      </section>
      <section class="panel">
        <h2>缺陷分析</h2>
        <p class="meta">排除脚本问题后，现象仍是产品问题时走这里。</p>
        <dl class="facts">
          <div><dt>输入</dt><dd>失败日志、截图，或拦截到的 JSON。</dd></div>
          <div><dt>输出</dt><dd>reports/缺陷报告_时间.md，含复现步骤、预期和实际。</dd></div>
          <div><dt>怎么说</dt><dd>在 Cursor 里说：缺陷分析</dd></div>
        </dl>
      </section>
    </div>`, true);
}

async function renderReports() {
  const payload = await getJson("/api/reports");
  const files = payload.files.length
    ? `<ul class="file-list">${payload.files.map((file) => `
        <li>
          <span class="pill">${esc(REPORT_KIND[file.kind] || "报告")}</span>
          <button type="button" class="report-open" data-report="${esc(file.name)}">${esc(file.name)}</button>
        </li>`).join("")}</ul>`
    : `<p class="notice">reports/ 里还没有 HTML 或 Markdown 报告。</p>`;
  return shell(backLink(), `
    <h1 class="page-title">测试报告</h1>
    <p class="lede">这里只列出 reports/ 根目录下的 HTML 和 Markdown。抓包文件仍在接口探针里。点击文件名在当前页弹出报告，不离开这一页，也不重新跑测试。</p>
    <section class="panel">${files}</section>`);
}

async function renderConfig() {
  const status = await getJson("/api/config");
  const dbNote = status.db === "partial"
    ? "数据库需要同时写上 DB_HOST、DB_USER、DB_NAME。"
    : status.db === "configured"
      ? "数据库三项都已写上。页面不显示主机、账号和密码。"
      : "未配置数据库时，现有用例不连库。";
  return shell(backLink(), `
    <h1 class="page-title">环境配置</h1>
    <p class="lede">只显示有没有配置。地址、账号和密码仍留在 .env，页面不展示这些值。修改 .env 后重新打开本页即可。</p>
    <section class="panel">
      <dl class="facts">
        <div><dt>BASE_URL</dt><dd>${esc(status.base_url_configured ? "已配置" : "未配置")}</dd></div>
        <div><dt>数据库</dt><dd>${esc(DB_LABEL[status.db] || "未配置")}</dd></div>
      </dl>
      <p class="meta">${esc(dbNote)} 活站点用例在缺少 BASE_URL 时不会改用默认地址。</p>
    </section>`);
}

async function renderScriptList() {
  const payload = await getJson("/api/scripts");
  const files = payload.files.map((file) => `
    <section class="script-file">
      <h2><code>${esc(file.path)}</code> <span>${file.tests.length}</span></h2>
      ${file.tests.map(renderScriptTest).join("")}
    </section>`).join("");
  const pending = payload.unscripted.length
    ? `<section class="script-file">
        <h2>还没有脚本 <span>${payload.unscripted.length}</span></h2>
        ${payload.unscripted.map(renderScriptTest).join("")}
      </section>`
    : "";
  const body = files || `<p class="notice">还没有写上 pytest_nodeid 的用例。</p>`;
  return `${body}${pending}`;
}

function renderScriptTest(item) {
  const node = item.pytest_nodeid
    ? `<code>${esc(item.test_name || item.pytest_nodeid)}</code>`
    : "";
  return `
    <article class="item">
      <div class="item-head">
        <a class="id" href="#/modules/${encodeURIComponent(item.module)}">${esc(item.case_id)}</a>
        ${pill(item.status, AUTO_LABEL)}
        <span class="muted">${esc(item.module)}</span>
      </div>
      <h3>${esc(item.title)}</h3>
      ${node}
    </article>`;
}

function renderRequirement(item) {
  const tags = Array.isArray(item.tags) && item.tags.length
    ? `<p class="muted">${item.tags.map((tag) => esc(tag)).join(" · ")}</p>`
    : "";
  const links = item.linked_case_ids.length
    ? `<p class="muted">关联用例 ${item.linked_case_ids.map((id) => esc(id)).join("、")}</p>`
    : "";
  return `
    <article class="item">
      <div class="item-head">
        <span class="id">${esc(item.req_id)}</span>
        ${pill(item.type, TYPE_LABEL)}
        ${item.priority ? `<span class="pill">${esc(item.priority)}</span>` : ""}
      </div>
      <h3>${esc(item.title)}</h3>
      <p>${esc(item.description)}</p>
      ${tags}
      ${links}
      <p class="muted">${esc(item.source_ref)}</p>
    </article>`;
}

function renderCase(item) {
  const node = item.automation.pytest_nodeid
    ? `<p class="kicker">pytest</p><code>${esc(item.automation.pytest_nodeid)}</code>`
    : "";
  return `
    <article class="item">
      <div class="item-head">
        <span class="id">${esc(item.case_id)}</span>
        ${pill(item.type, TYPE_LABEL)}
        ${pill(item.automation.status, AUTO_LABEL)}
      </div>
      <h3>${esc(item.title)}</h3>
      ${block("前置", item.preconditions)}
      ${block("步骤", item.steps)}
      ${block("预期", item.expected_results)}
      <p class="muted">需求 ${item.requirement_ids.map((id) => esc(id)).join("、")}</p>
      ${node}
      <p class="muted">${esc(item.source_ref)}</p>
    </article>`;
}

function renderQuestion(item) {
  const resolution = item.resolution
    ? `<p><span class="kicker">结论</span><br>${esc(item.resolution)}</p>`
    : "";
  return `
    <article class="item">
      <div class="item-head">
        <span class="id">${esc(item.question_id)}</span>
        ${pill(item.status, QUESTION_LABEL)}
      </div>
      <h3>${esc(item.description)}</h3>
      <p><span class="kicker">建议确认</span><br>${esc(item.suggested_confirmation)}</p>
      ${resolution}
      <p class="muted">${esc(item.source_ref)}</p>
    </article>`;
}

function automationStats(automation) {
  return [
    ["已自动化", automation.automated],
    ["待自动化", automation.pending],
    ["手工", automation.manual],
  ].filter(([, count]) => count > 0)
    .map(([label, count]) => `<li>${esc(label)} ${esc(count)}</li>`)
    .join("");
}

function column(title, items, renderItem) {
  const body = items.length
    ? items.map(renderItem).join("")
    : `<p class="notice">没有记录</p>`;
  return `<section class="column"><h2>${esc(title)} <span>${items.length}</span></h2>${body}</section>`;
}

function block(title, items) {
  if (!items || !items.length) return "";
  return `<p class="kicker">${esc(title)}</p><ol>${items.map((item) => `<li>${esc(item)}</li>`).join("")}</ol>`;
}

function pill(value, labels) {
  const label = labels[value] || value;
  return `<span class="pill ${esc(value)}">${esc(label)}</span>`;
}

function shell(leading, body, wide) {
  return `<main class="wrap${wide ? " wide" : ""}">
    <div class="topbar">${leading}<span class="local-badge">本机</span></div>
    ${body}
  </main>`;
}

function backLink(href = "#/") {
  const label = href === "#/" ? "返回首页" : "返回用例资产";
  return `<a class="back" href="${href}">${label}</a>`;
}

function renderMissing(message) {
  const hint = message === "Failed to fetch"
    ? "请先在仓库根目录运行 python -m src.web.server，再打开 http://127.0.0.1:8765"
    : message;
  return shell(backLink(), `<h1 class="page-title">分层测试台</h1><p class="notice">${esc(hint)}</p>`);
}

function decodeHash() {
  const raw = location.hash.replace(/^#/, "") || "/";
  try {
    return decodeURIComponent(raw);
  } catch (_error) {
    return "/";
  }
}

async function getJson(url) {
  const response = await fetch(url);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.error || "读取失败");
  }
  return payload;
}

function openReport(name) {
  if (!name) return;
  let modal = document.querySelector("#report-modal");
  if (!modal) {
    modal = document.createElement("div");
    modal.id = "report-modal";
    modal.className = "modal";
    modal.hidden = true;
    modal.innerHTML = `
      <button type="button" class="modal-backdrop" data-close-modal aria-label="关闭报告"></button>
      <div class="modal-dialog" role="dialog" aria-modal="true" aria-labelledby="report-modal-title">
        <header class="modal-bar">
          <h2 id="report-modal-title"></h2>
          <button type="button" class="modal-close" data-close-modal>关闭</button>
        </header>
        <iframe class="modal-frame" title="测试报告"></iframe>
      </div>`;
    document.body.appendChild(modal);
  }
  modal.querySelector("#report-modal-title").textContent = name;
  modal.querySelector("iframe").src = "/reports/" + encodeURIComponent(name);
  modal.hidden = false;
  document.body.classList.add("modal-open");
  modal.querySelector(".modal-close").focus();
}

function closeReport() {
  const modal = document.querySelector("#report-modal");
  if (!modal || modal.hidden) return;
  modal.hidden = true;
  modal.querySelector("iframe").src = "about:blank";
  document.body.classList.remove("modal-open");
}

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[char]));
}
