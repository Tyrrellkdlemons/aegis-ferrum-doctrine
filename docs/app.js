const STATUS_LABELS = {
  ready_local_not_published: "READY · LOCAL",
  ready_text_not_published: "READY · TEXT",
  review_rules_before_posting: "RULES REVIEW",
  script_complete_media_rework: "SCRIPT READY · MEDIA HOLD",
  outline_complete_media_rework: "OUTLINE · MEDIA HOLD",
  qa_hold: "QA HOLD",
  review: "REVIEW",
  published: "PUBLISHED"
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
  return element("span", `status status--${status}`, STATUS_LABELS[status] || status.replaceAll("_", " "));
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

function renderContent(items) {
  const target = document.getElementById("contentGrid");
  target.replaceChildren();
  for (const item of items) {
    const card = element("article", "content-card");
    const top = element("div", "content-card__top");
    top.append(element("span", "content-id", item.id), statusPill(item.status));
    card.append(top, element("h3", "", item.title), element("p", "", item.detail));
    const source = element("code", "", item.source);
    card.append(source);
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

function renderMetrics(performance) {
  const target = document.getElementById("metrics");
  target.replaceChildren();
  for (const [key, label] of Object.entries(METRIC_LABELS)) {
    const row = element("div", "metric-row");
    row.append(element("dt", "", label), element("dd", "", performance[key] ?? "—"));
    target.append(row);
  }
  document.getElementById("performanceNote").textContent = performance.note;
}

function render(data) {
  document.getElementById("channelName").textContent = data.channel.name;
  document.getElementById("lastUpdated").textContent = `verified ${formatDate(data.updated_at, data.timezone)}`;

  const intensity = data.editorial_intensity;
  document.getElementById("brutalityScore").textContent = intensity.score;
  document.getElementById("brutalityLabel").textContent = intensity.label;
  document.getElementById("brutalityMethod").textContent = intensity.method;
  const fill = document.getElementById("brutalityFill");
  fill.style.width = `${intensity.score}%`;
  fill.parentElement.setAttribute("aria-valuenow", String(intensity.score));

  document.getElementById("readyCount").textContent = data.summary.ready;
  document.getElementById("reviewCount").textContent = data.summary.review;
  document.getElementById("publishedCount").textContent = data.summary.published;
  document.getElementById("visualScore").textContent = data.prometheus.visual_score;
  document.getElementById("sealDecision").textContent = data.prometheus.decision;
  document.getElementById("sealDetail").textContent =
    `Visual ${data.prometheus.visual_score}/${data.prometheus.threshold} gate · thumbnail ${data.prometheus.thumbnail_score}/${data.prometheus.thumbnail_threshold} gate · ${data.prometheus.seal}`;

  renderContent(data.content);
  renderCalendar(data.posts, data.timezone);
  renderMetrics(data.performance);
}

async function boot() {
  try {
    const response = await fetch("./data/schedule.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`schedule request failed: ${response.status}`);
    render(await response.json());
  } catch (error) {
    document.body.classList.add("data-error");
    document.getElementById("lastUpdated").textContent = "data load failed";
    document.getElementById("contentGrid").append(
      element("p", "error-message", `Dashboard data could not be loaded. ${error.message}`)
    );
  }
}

boot();
