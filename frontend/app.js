const API_BASE_URL = "https://grader-b4h0azdvage4a5a5.southeastasia-01.azurewebsites.net/";
/* ═══════════════════════════════════════════════════
   SCREEN HELPERS
═══════════════════════════════════════════════════ */
function showScreen(id) {
  document.querySelectorAll(".screen").forEach(s => {
    s.classList.remove("active");
    s.style.display = "none";
  });
  const el = document.getElementById(id);
  el.style.display = "flex";
  // small tick so CSS transition fires
  requestAnimationFrame(() => requestAnimationFrame(() => el.classList.add("active")));
}

/* ═══════════════════════════════════════════════════
   SCREEN 1 — LOAD DATA ON PAGE START
═══════════════════════════════════════════════════ */
async function loadData() {
  try {
    
    const res = await fetch(`${API_BASE_URL}/load`);
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();

    // ── Question ──────────────────────────────────
    const qEl = document.getElementById("question-text");
    qEl.classList.remove("skeleton-line");
    qEl.textContent = data.question;

    // ── Rubric ────────────────────────────────────
    const rEl = document.getElementById("rubric-text");
    rEl.classList.remove("skeleton-block");
    rEl.textContent = data.rubric;

    // ── Student table ─────────────────────────────
    const tbody = document.getElementById("student-tbody");
    tbody.innerHTML = "";
    data.students.forEach(s => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${s.stdno}</td>
        <td><div class="answer-cell">${s.answer}</div></td>
      `;
      tbody.appendChild(tr);
    });

    // ── Update badge & count ──────────────────────
    const badge = document.getElementById("load-badge");
    badge.className = "badge ready";
    badge.innerHTML = `<span class="dot"></span> ${data.students.length} students loaded`;

    document.getElementById("student-count").textContent =
      `${data.students.length} students`;

    // ── Enable start button ───────────────────────
    document.getElementById("btn-grade").disabled = false;

  } catch (err) {
    const badge = document.getElementById("load-badge");
    badge.className = "badge loading";
    badge.innerHTML = `<span class="dot"></span> Error: ${err.message}`;
    console.error(err);
  }
}

/* ═══════════════════════════════════════════════════
   STEP HELPERS — SCREEN 2
═══════════════════════════════════════════════════ */
function setStep(num, state) {
  // state: 'pending' | 'running' | 'done'
  const icon   = document.querySelector(`#step-${num} .step-icon`);
  const status = document.getElementById(`s${num}-status`);

  icon.className = `step-icon ${state}`;

  const labels = { pending: "—", running: "Running…", done: "✓ Done" };
  status.textContent = labels[state];
  status.className   = `step-status ${state === "pending" ? "" : state}`;

  if (state === "done") icon.textContent = "✓";
}

function setFooter(msg) {
  document.getElementById("progress-footer").textContent = msg;
}

/* ═══════════════════════════════════════════════════
   SCREEN 2 — START GRADING
═══════════════════════════════════════════════════ */
async function startGrading() {
  showScreen("screen-grading");

  // Step 1 — data already loaded
  await delay(600);
  setStep(1, "done");
  setFooter("Calling AI grading agents…");

  // Step 2 — call the API (this is the long part)
  setStep(2, "running");

  let gradeData;
  try {
    const res = await fetch(`${API_BASE_URL}/grade`, { method: "POST" });
    if (!res.ok) throw new Error(await res.text());
    gradeData = await res.json();
  } catch (err) {
    setFooter(`Error: ${err.message}`);
    setStep(2, "pending");
    return;
  }

  setStep(2, "done");
  setFooter("Saving results to dataset folder…");

  // Step 3 — saving (already done server-side, show briefly)
  setStep(3, "running");
  await delay(900);
  setStep(3, "done");
  setFooter("All done! Loading results…");

  await delay(700);
  showResults(gradeData.results);
}

/* ═══════════════════════════════════════════════════
   SCREEN 3 — SHOW RESULTS
═══════════════════════════════════════════════════ */
function showResults(results) {
  showScreen("screen-results");

  // Meta info
  const avg = (results.reduce((s, r) => s + r.mark, 0) / results.length).toFixed(1);
  document.getElementById("results-meta").textContent =
    `${results.length} students · Average mark: ${avg} / 10`;

  // Table rows
  const tbody = document.getElementById("results-tbody");
  tbody.innerHTML = "";

  results.forEach((r, i) => {
    const markClass = r.mark >= 8 ? "mark-high" : r.mark >= 5 ? "mark-mid" : "mark-low";
    const reasons   = r.lost_marks_reason || [];
    const reasonsHtml = reasons.length
      ? `<ul class="reasons-list">${reasons.map(x => `<li class="reason-tag">${x}</li>`).join("")}</ul>`
      : `<span class="no-reason">No deductions</span>`;

    const tr = document.createElement("tr");
    tr.style.animationDelay = `${i * 60}ms`;
    tr.innerHTML = `
      <td>${r.stdno}</td>
      <td><span class="${markClass}">${r.mark}</span></td>
      <td>${reasonsHtml}</td>
    `;
    tbody.appendChild(tr);
  });
}

/* ═══════════════════════════════════════════════════
   UTILITY
═══════════════════════════════════════════════════ */
function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/* ═══════════════════════════════════════════════════
   INIT
═══════════════════════════════════════════════════ */
document.addEventListener("DOMContentLoaded", () => {
  showScreen("screen-data");
  loadData();
});