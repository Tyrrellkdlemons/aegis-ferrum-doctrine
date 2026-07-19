const STATUS_LABELS = {
  ready_local_not_published: "READY · LOCAL",
  ready_local_awaiting_operator_sign_in: "READY · AWAITING UPLOAD",
  ready_text_not_published: "READY · TEXT",
  review_rules_before_posting: "RULES REVIEW",
  script_complete_media_rework: "SCRIPT READY · MEDIA HOLD",
  outline_complete_media_rework: "OUTLINE · MEDIA HOLD",
  qa_hold: "QA HOLD",
  review: "REVIEW",
  rework: "REWORK",
  complete: "COMPLETE",
  published: "PUBLISHED",
  blocked_needs_google_session: "BLOCKED · SIGN-IN",
  executing_upload: "UPLOADING",
  idle: "IDLE",
  awaiting_publication: "AWAITING PUBLISH",
  blocked_no_verified_offers: "BLOCKED · NO OFFERS"
};

const METRIC_LABELS = {
  views_24h: "Views · 24h",
  ctr_percent: "Click-through rate",
  average_retention_percent: "Average retention",
  subscriber_delta: "Subscriber delta",
  revenue_usd: "Revenue"
};

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function statusPill(status) {
  const key = status || "unknown";
  return element("span", `status status--${key}`, STATUS_LABELS[key] || key.replaceAll("_", " "));
}

function formatDate(value, timezone) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("en-US", {
    timeZone: timezone,
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZoneName: "short"
  }).format(date);
}

function toast(message) {
  const node = document.getElementById("toast");
  node.textContent = message;
  node.hidden = false;
  clearTimeout(toast._t);
  toast._t = setTimeout(() => {
    node.hidden = true;
  }, 1600);
}

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text);
    toast("Copied to clipboard");
  } catch {
    toast("Copy failed — select manually");
  }
}

function bindNav() {
  const buttons = [...document.querySelectorAll(".cmd-nav__btn")];
  const views = [...document.querySelectorAll(".panel-view")];
  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.dataset.panel;
      buttons.forEach((b) => b.classList.toggle("is-active", b === btn));
      views.forEach((view) => {
        const active = view.dataset.view === id;
        view.classList.toggle("is-active", active);
        view.hidden = !active;
      });
      history.replaceState(null, "", `#${id}`);
    });
  });
  const hash = (location.hash || "#overview").slice(1);
  const match = buttons.find((b) => b.dataset.panel === hash);
  if (match) match.click();
}

function renderContent(items, targetId) {
  const target = document.getElementById(targetId);
  target.replaceChildren();
  for (const item of items) {
    const card = element("article", "content-card");
    const top = element("div", "content-card__top");
    top.append(element("span", "content-id", item.id), statusPill(item.status));
    card.append(top, element("h3", "", item.title), element("p", "", item.detail || item.engine || ""));
    if (item.source) card.append(element("code", "", item.source));
    if (item.file) card.append(element("code", "", item.file));
    target.append(card);
  }
}

function renderCalendar(posts, timezone) {
  const target = document.getElementById("calendar");
  target.replaceChildren();
  for (const post of posts) {
    const card = element("article", "calendar-card");
    const rail = element("span", "calendar-card__rail");
    const body = element("div", "calendar-card__body");
    const row = element("div", "calendar-card__row");
    row.append(element("strong", "", post.platform.toUpperCase()), statusPill(post.status));
    body.append(
      element("time", "", formatDate(post.when, timezone)),
      row,
      element("h3", "", post.piece),
      element("code", "", post.file)
    );
    card.append(rail, body);
    target.append(card);
  }
}

function renderMetrics(performance = {}) {
  const target = document.getElementById("metrics");
  target.replaceChildren();
  for (const [key, label] of Object.entries(METRIC_LABELS)) {
    const row = element("div", "metric-row");
    row.append(element("dt", "", label), element("dd", "", performance[key] ?? "—"));
    target.append(row);
  }
  document.getElementById("performanceNote").textContent = performance.note || "";
}

function renderProgress(data) {
  const p = data.progress || {};
  document.getElementById("progressSummary").textContent =
    `${p.complete || 0} complete · ${p.ready || 0} ready · ${p.review || 0} review · ${p.blocked || 0} blocked · ${p.total || 0} total`;

  const bars = document.getElementById("progressBars");
  bars.replaceChildren();
  const total = Math.max(p.total || 1, 1);
  for (const [label, value, cls] of [
    ["Complete", p.complete || 0, "bar--green"],
    ["Ready", p.ready || 0, "bar--green"],
    ["Review", p.review || 0, "bar--amber"],
    ["Blocked", p.blocked || 0, "bar--red"]
  ]) {
    const row = element("div", "bar-row");
    row.append(element("span", "", label), element("strong", "", String(value)));
    const track = element("div", "bar-track");
    const fill = element("span", cls);
    fill.style.width = `${Math.round((value / total) * 100)}%`;
    track.append(fill);
    row.append(track);
    bars.append(row);
  }

  const grid = document.getElementById("taskGrid");
  grid.replaceChildren();
  for (const task of data.tasks || []) {
    const card = element("article", "task-card");
    const top = element("div", "content-card__top");
    top.append(element("span", "content-id", task.id), statusPill(task.status));
    card.append(top, element("h3", "", task.type || task.id), element("p", "", task.details || ""));
    if (task.assigned) card.append(element("code", "", `assigned: ${task.assigned}`));
    grid.append(card);
  }

  const roles = document.getElementById("roleGrid");
  roles.replaceChildren();
  for (const [name, role] of Object.entries(data.roles || {})) {
    const card = element("article", "role-card");
    const top = element("div", "content-card__top");
    top.append(element("span", "content-id", name), statusPill(role.status));
    card.append(top, element("p", "", role.note || "—"));
    if (role.assignee) card.append(element("code", "", role.assignee));
    roles.append(card);
  }
}

function renderCommands(commands) {
  const grid = document.getElementById("commandGrid");
  grid.replaceChildren();
  for (const cmd of commands) {
    const card = element("article", "command-card");
    card.tabIndex = 0;
    card.append(element("span", "content-id", cmd.id), element("h3", "", cmd.label), element("p", "", cmd.purpose));
    const code = element("code", "command-shell", cmd.shell);
    card.append(code);
    const copy = () => copyText(cmd.shell);
    card.addEventListener("click", copy);
    card.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        copy();
      }
    });
    grid.append(card);
  }
}

function renderUpload(helper) {
  if (!helper) return;
  const files = document.getElementById("uploadFiles");
  files.replaceChildren();
  for (const file of helper.files || []) {
    const li = element("li", "");
    li.append(element("code", "", file));
    files.append(li);
  }
  const checks = document.getElementById("uploadChecks");
  checks.replaceChildren();
  for (const check of helper.checks || []) {
    checks.append(element("li", "", check));
  }
  document.getElementById("uploadTitle").value = helper.title || "";
  document.getElementById("uploadDescription").value = helper.description || "";
  document.getElementById("uploadTags").value = (helper.tags || []).join(", ");
  document.getElementById("uploadMeta").textContent =
    `${helper.channel} · ${helper.channel_id} · ${helper.handle} · pack ${helper.pack}`;
  const studio = document.getElementById("studioLink");
  studio.href = helper.studio_url || "#";

  document.querySelectorAll("[data-copy-target]").forEach((btn) => {
    btn.onclick = () => {
      const id = btn.getAttribute("data-copy-target");
      copyText(document.getElementById(id).value);
    };
  });
}

function renderLinks(links, overviewHost) {
  const cards = document.getElementById("linkCards");
  cards.replaceChildren();
  overviewHost.replaceChildren();
  const entries = [
    ["GitHub Pages", links.github_pages, "Primary Pages URL (/docs)"],
    ["Netlify", links.netlify, "Unique Netlify production URL"],
    ["Netlify Admin", links.netlify_admin, "Deploy settings in your Netlify account"],
    ["GitHub Repo", links.github_repo, "Source of truth repository"],
    ["YouTube Studio", links.youtube_studio, "FD-001 upload entry"]
  ];
  for (const [label, href, detail] of entries) {
    if (!href) continue;
    const card = element("a", "link-card", "");
    card.href = href;
    card.target = "_blank";
    card.rel = "noopener";
    card.append(element("span", "content-id", label), element("strong", "", href), element("p", "", detail));
    cards.append(card);

    const chip = element("a", "link-chip", label);
    chip.href = href;
    chip.target = "_blank";
    chip.rel = "noopener";
    overviewHost.append(chip);
  }
}

function renderGates(data) {
  const clearance = data.clearance || {};
  const list = document.getElementById("gateList");
  list.replaceChildren();
  const rows = [
    ["Channel", data.identity?.channel || "The Tyrrell Codex"],
    ["Series", data.identity?.series || "Ferrum Doctrine"],
    ["Local cleared", clearance.local_release_cleared ? "YES" : "NO"],
    ["External publish", clearance.external_publish_executed ? "YES" : "Not executed"],
    ["Publish URLs", (clearance.external_publish_urls || []).join(", ") || "none yet"],
    ["GitHub Pages", data.links?.github_pages || "—"],
    ["Netlify", data.links?.netlify || "—"]
  ];
  for (const [label, value] of rows) {
    const li = element("li", "");
    li.append(element("span", "", label), element("strong", "", value));
    list.append(li);
  }
}

function render(data) {
  document.getElementById("channelName").textContent = data.identity?.channel || data.channel?.name || "The Tyrrell Codex";
  document.getElementById("seriesName").textContent = `${data.identity?.series || "Ferrum Doctrine"} series`;
  document.getElementById("lastUpdated").textContent = `verified ${formatDate(data.updated_at || data.generated_at, data.timezone || "America/Los_Angeles")}`;

  const intensity = data.editorial_intensity || {};
  document.getElementById("brutalityScore").textContent = intensity.score ?? "—";
  document.getElementById("brutalityLabel").textContent = intensity.label || "—";
  document.getElementById("brutalityMethod").textContent = intensity.method || "";
  const fill = document.getElementById("brutalityFill");
  fill.style.width = `${intensity.score || 0}%`;
  fill.parentElement.setAttribute("aria-valuenow", String(intensity.score || 0));

  const summary = data.summary || {};
  document.getElementById("readyCount").textContent = summary.ready ?? "—";
  document.getElementById("reviewCount").textContent = summary.review ?? "—";
  document.getElementById("publishedCount").textContent = summary.published ?? "—";
  document.getElementById("visualScore").textContent = data.prometheus?.visual_score ?? "—";
  document.getElementById("sealDecision").textContent = data.prometheus?.decision ?? "—";
  document.getElementById("sealDetail").textContent =
    `Visual ${data.prometheus?.visual_score}/${data.prometheus?.threshold} · thumbnail ${data.prometheus?.thumbnail_score}/${data.prometheus?.thumbnail_threshold} · ${data.prometheus?.seal || ""}`;

  renderContent(data.content || [], "contentGrid");
  const stickmanItems = (data.stickman?.lessons || []).map((lesson) => ({
    id: lesson.id,
    title: lesson.title,
    status: data.stickman?.status || "review",
    detail: `engine ${lesson.engine || "v2"} · ${Math.round((lesson.bytes || 0) / 1024)} KB`,
    file: lesson.file
  }));
  renderContent(stickmanItems, "stickmanGrid");
  renderCalendar(data.posts || [], data.timezone || "America/Los_Angeles");
  renderMetrics(data.performance || {});
  renderProgress(data);
  renderCommands(data.commands || []);
  renderUpload(data.upload_helper);
  renderLinks(data.links || {}, document.getElementById("overviewLinks"));
  renderGates(data);
}

async function boot() {
  bindNav();
  try {
    const response = await fetch("./data/command_center.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`command_center request failed: ${response.status}`);
    render(await response.json());
  } catch (error) {
    // Fallback to legacy schedule.json so Pages never goes blank
    try {
      const response = await fetch("./data/schedule.json", { cache: "no-store" });
      if (!response.ok) throw error;
      const schedule = await response.json();
      render({
        identity: { channel: schedule.channel?.name, series: schedule.series },
        ...schedule,
        links: schedule.deploy || {
          github_pages: "https://tyrrellkdlemons.github.io/aegis-ferrum-doctrine/",
          netlify: "https://tyrrell-codex-aegis-command.netlify.app/"
        },
        tasks: [],
        roles: {},
        commands: [],
        upload_helper: null,
        stickman: null,
        progress: { complete: 0, ready: schedule.summary?.ready || 0, review: schedule.summary?.review || 0, blocked: 0, total: 0 }
      });
      toast("Loaded schedule fallback");
    } catch (fallbackError) {
      document.body.classList.add("data-error");
      document.getElementById("lastUpdated").textContent = "data load failed";
      document.getElementById("contentGrid").append(
        element("p", "error-message", `Dashboard data could not be loaded. ${fallbackError.message}`)
      );
    }
  }
}

boot();
