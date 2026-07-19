async function loadSchedule() {
  try {
    const res = await fetch("./data/schedule.json", { cache: "no-store" });
    if (res.ok) return await res.json();
  } catch (_) {}
  return {
    content_id: "ferrum-doctrine-pipeline",
    brutality_score: 96,
    posts: []
  };
}

function boot(SCHEDULE) {
  const score = SCHEDULE.brutality_score || 96;
  document.getElementById("brutalityScore").textContent = String(score);
  document.getElementById("brutalityFill").style.width = `${score}%`;

  const tbody = document.querySelector("#contentTable tbody");
  tbody.innerHTML = (SCHEDULE.posts || []).map((p) => `
    <tr>
      <td>${p.piece?.includes("buffer") ? p.piece.split(" ")[0] : (SCHEDULE.content_id || "FD")}</td>
      <td>${p.piece}<div style="color:#8b949e;margin-top:0.25rem">${p.file || ""}</div></td>
      <td>${p.platform}</td>
      <td>${String(p.when || "").replace("T", " ").replace("Z", " UTC")}</td>
      <td><span class="status ${p.status}">${p.status}</span></td>
    </tr>
  `).join("");

  const cal = document.getElementById("calendar");
  cal.innerHTML = (SCHEDULE.posts || []).map((p) => `
    <article class="cal-card">
      <time datetime="${p.when}">${p.when}</time>
      <strong>${String(p.platform || "").toUpperCase()}</strong>
      <span>${p.piece} · ${p.status}</span>
    </article>
  `).join("");
}

loadSchedule().then(boot);
