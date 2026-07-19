const SCHEDULE = {
  content_id: "ferrum-doctrine-001",
  brutality_score: 93,
  posts: [
    { platform: "youtube", piece: "Long-form + Short", when: "2026-07-19T12:00:00Z", status: "ready", file: "final_long.mp4" },
    { platform: "x", piece: "8-tweet thread", when: "2026-07-19T13:00:00Z", status: "ready", file: "thread.txt" },
    { platform: "instagram", piece: "Reel + carousel", when: "2026-07-19T17:00:00Z", status: "ready", file: "final_reel.mp4" },
    { platform: "tiktok", piece: "Vertical short", when: "2026-07-19T18:30:00Z", status: "ready", file: "final_tiktok.mp4" },
    { platform: "reddit", piece: "Value post", when: "2026-07-20T15:00:00Z", status: "ready", file: "post.md" }
  ]
};

function boot() {
  const score = SCHEDULE.brutality_score;
  document.getElementById("brutalityScore").textContent = String(score);
  document.getElementById("brutalityFill").style.width = `${score}%`;

  const tbody = document.querySelector("#contentTable tbody");
  tbody.innerHTML = SCHEDULE.posts.map((p) => `
    <tr>
      <td>${SCHEDULE.content_id}</td>
      <td>${p.piece}<div style="color:#8b949e;margin-top:0.25rem">${p.file}</div></td>
      <td>${p.platform}</td>
      <td>${p.when.replace("T", " ").replace("Z", " UTC")}</td>
      <td><span class="status ${p.status}">${p.status}</span></td>
    </tr>
  `).join("");

  const cal = document.getElementById("calendar");
  cal.innerHTML = SCHEDULE.posts.map((p) => `
    <article class="cal-card">
      <time datetime="${p.when}">${p.when}</time>
      <strong>${p.platform.toUpperCase()}</strong>
      <span>${p.piece} · ${p.status}</span>
    </article>
  `).join("");
}

boot();
