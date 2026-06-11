/* ===========================================================
   Mundial 2026 - Fase de grupos
   Carga los datos (grupos, partidos, tips) y arma la pagina.
   Las horas se guardan en UTC y se muestran en la hora local
   de quien abre la pagina (en Chile saldra en hora chilena).
   =========================================================== */

const PANELS = ["hoy", "calendario", "grupos", "tips"];
let DATA = { groups: {}, matches: [], tips: {}, updated: null };

// ---- utilidades de fecha (hora local del visitante) ----
function dObj(m) { return new Date(m.kickoff_utc); }
function localDateKey(d) { return d.toLocaleDateString("en-CA"); } // YYYY-MM-DD local
function todayKey() { return new Date().toLocaleDateString("en-CA"); }
function fmtTime(d) {
  return d.toLocaleTimeString("es-CL", { hour: "2-digit", minute: "2-digit" });
}
function fmtDayTitle(d) {
  const s = d.toLocaleDateString("es-CL", { weekday: "long", day: "numeric", month: "long" });
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function isFinished(m) {
  return m.status === "FINISHED" || (m.score1 !== null && m.score2 !== null && m.status !== "IN_PLAY");
}
function isLive(m) { return m.status === "IN_PLAY"; }
function hasScore(m) { return m.score1 !== null && m.score2 !== null; }

// ===========================================================
//  Tarjeta de un partido
// ===========================================================
function matchCard(m) {
  const d = dObj(m);
  const fin = isFinished(m);
  const live = isLive(m);
  const showScore = hasScore(m) || live;

  let w1 = false, w2 = false;
  if (fin && hasScore(m)) { w1 = m.score1 > m.score2; w2 = m.score2 > m.score1; }

  let mid;
  if (showScore) {
    mid = `<div class="score">${m.score1 ?? 0} - ${m.score2 ?? 0}</div>`;
  } else {
    mid = `<div class="vs">VS</div><div class="time">${fmtTime(d)} hrs</div>`;
  }

  let badge = `<span class="badge group">Grupo ${m.group}</span>`;
  if (live) badge = `<span class="badge live">● En vivo</span>`;
  else if (fin) badge = `<span class="badge fin">Final · Grupo ${m.group}</span>`;

  return `
  <div class="match">
    <div class="side ${w1 ? "winner" : ""}">
      <span class="flag">${m.team1.flag}</span>
      <span class="tname">${m.team1.name}</span>
    </div>
    <div class="mid">
      ${mid}
      <div>${badge}</div>
      <div class="meta">📍 ${m.city}</div>
    </div>
    <div class="side right ${w2 ? "winner" : ""}">
      <span class="flag">${m.team2.flag}</span>
      <span class="tname">${m.team2.name}</span>
    </div>
  </div>`;
}

// ===========================================================
//  Panel HOY
// ===========================================================
function renderHoy() {
  const el = document.getElementById("hoy");
  const tk = todayKey();
  const sorted = [...DATA.matches].sort((a, b) => dObj(a) - dObj(b));
  const hoy = sorted.filter((m) => localDateKey(dObj(m)) === tk);
  const ahora = new Date();
  const proximos = sorted.filter((m) => dObj(m) > ahora && localDateKey(dObj(m)) !== tk).slice(0, 6);

  let html = `<h2 class="section-title">⚽ Partidos de hoy</h2>`;
  html += `<h3 class="day-title">${fmtDayTitle(new Date())}</h3>`;
  html += hoy.length ? hoy.map(matchCard).join("") :
    `<div class="empty">No hay partidos hoy. ¡Pero vienen más! 👇</div>`;

  if (proximos.length) {
    html += `<h2 class="section-title" style="margin-top:26px">📅 Próximos partidos</h2>`;
    let lastDay = "";
    for (const m of proximos) {
      const dk = localDateKey(dObj(m));
      if (dk !== lastDay) { html += `<h3 class="day-title">${fmtDayTitle(dObj(m))}</h3>`; lastDay = dk; }
      html += matchCard(m);
    }
  }
  el.innerHTML = html;
}

// ===========================================================
//  Panel CALENDARIO
// ===========================================================
let calFilter = "todas";
function renderCalendario() {
  const el = document.getElementById("calendario");
  let html = `<h2 class="section-title">📅 Calendario completo</h2>`;
  html += `<div class="filters">
    ${["todas", "1", "2", "3"].map((f) =>
      `<button class="${calFilter === f ? "active" : ""}" data-jor="${f}">${f === "todas" ? "Todas" : "Jornada " + f}</button>`
    ).join("")}
  </div>`;

  let list = [...DATA.matches].sort((a, b) => dObj(a) - dObj(b));
  if (calFilter !== "todas") list = list.filter((m) => String(m.matchday) === calFilter);

  let lastDay = "";
  for (const m of list) {
    const dk = localDateKey(dObj(m));
    if (dk !== lastDay) { html += `<h3 class="day-title">${fmtDayTitle(dObj(m))}</h3>`; lastDay = dk; }
    html += matchCard(m);
  }
  el.innerHTML = html;

  el.querySelectorAll("[data-jor]").forEach((b) =>
    b.addEventListener("click", () => { calFilter = b.dataset.jor; renderCalendario(); })
  );
}

// ===========================================================
//  Panel GRUPOS (tablas + probabilidades + apuntes)
// ===========================================================
function computeStandings(letter) {
  const teams = {};
  for (const t of DATA.groups[letter]) {
    teams[t.key] = { ...t, pj: 0, g: 0, e: 0, p: 0, gf: 0, gc: 0, pts: 0 };
  }
  for (const m of DATA.matches) {
    if (m.group !== letter || !hasScore(m) || !isFinished(m)) continue;
    const a = teams[m.team1.key], b = teams[m.team2.key];
    if (!a || !b) continue;
    a.pj++; b.pj++;
    a.gf += m.score1; a.gc += m.score2;
    b.gf += m.score2; b.gc += m.score1;
    if (m.score1 > m.score2) { a.g++; a.pts += 3; b.p++; }
    else if (m.score1 < m.score2) { b.g++; b.pts += 3; a.p++; }
    else { a.e++; b.e++; a.pts++; b.pts++; }
  }
  return Object.values(teams).sort((x, y) =>
    y.pts - x.pts || (y.gf - y.gc) - (x.gf - x.gc) || y.gf - x.gf || x.name.localeCompare(y.name)
  );
}

function renderGrupos() {
  const el = document.getElementById("grupos");
  let html = `<h2 class="section-title">🏆 Grupos y tablas</h2>`;
  html += `<p class="qual-note"><span class="qual-dot"></span> Zona de clasificación: avanzan los <b>2 primeros</b> de cada grupo (y los 8 mejores terceros).</p>`;

  for (const letter of Object.keys(DATA.groups)) {
    const rows = computeStandings(letter);
    const prob = (DATA.tips.probabilidades || {})[letter] || [];
    const probName = (k) => {
      const t = DATA.groups[letter].find((x) => x.key === k);
      return t ? t : { name: k, flag: "" };
    };
    const comentario = (DATA.tips.comentarios || {})[letter];
    const apunte = (DATA.tips.apuntes || {})[letter];

    html += `<div class="group-card">
      <h3><span class="gletter">${letter}</span> Grupo ${letter}</h3>
      <table class="standings">
        <thead><tr>
          <th></th><th></th><th>PJ</th><th>G</th><th>E</th><th>P</th><th>GF</th><th>GC</th><th>DG</th><th>Pts</th>
        </tr></thead>
        <tbody>
        ${rows.map((t, i) => `
          <tr class="${i < 2 ? "qualify" : ""}">
            <td class="pos">${i + 1}</td>
            <td class="team">${t.flag} ${t.name}</td>
            <td>${t.pj}</td><td>${t.g}</td><td>${t.e}</td><td>${t.p}</td>
            <td>${t.gf}</td><td>${t.gc}</td><td>${t.gf - t.gc >= 0 ? "+" : ""}${t.gf - t.gc}</td>
            <td class="pts">${t.pts}</td>
          </tr>`).join("")}
        </tbody>
      </table>`;

    if (prob.length) {
      html += `<div class="prob-block"><div class="lbl">Probabilidad de ganar el grupo</div>`;
      for (const p of prob) {
        const t = probName(p.key);
        html += `<div class="prob-row">
          <span class="pteam">${t.flag} ${t.name}</span>
          <span class="prob-bar-bg"><span class="prob-bar" style="width:${p.pct}%"></span></span>
          <span class="ppct">${p.pct}%</span>
        </div>`;
      }
      html += `</div>`;
    }
    if (comentario) html += `<div class="comentario">💡 ${comentario}</div>`;
    if (apunte) html += `<button class="apunte-btn" data-img="${apunte}">✍️ Ver mis apuntes del grupo ${letter}</button>`;
    html += `</div>`;
  }
  el.innerHTML = html;

  el.querySelectorAll("[data-img]").forEach((b) =>
    b.addEventListener("click", () => openLightbox(b.dataset.img))
  );
}

// ===========================================================
//  Panel TIPS
// ===========================================================
function renderTips() {
  const el = document.getElementById("tips");
  const cur = DATA.tips.curiosidades || [];
  const notas = DATA.tips.notas || [];
  let html = `<h2 class="section-title">💡 Tips y datos</h2>`;

  html += `<div class="tip-card"><h3>🤓 Datos curiosos</h3><ul>`;
  html += cur.map((c) => `<li>${c}</li>`).join("");
  html += `</ul></div>`;

  html += `<div class="tip-card"><h3>📝 Mis notas</h3><ul>`;
  html += notas.map((c) => `<li>${c}</li>`).join("");
  html += `</ul></div>`;

  el.innerHTML = html;
}

// ===========================================================
//  Lightbox
// ===========================================================
function openLightbox(src) {
  const lb = document.getElementById("lightbox");
  document.getElementById("lightbox-img").src = src;
  lb.classList.add("open");
}
function closeLightbox() {
  document.getElementById("lightbox").classList.remove("open");
}

// ===========================================================
//  Tabs
// ===========================================================
function setupTabs() {
  document.querySelectorAll(".tab").forEach((t) =>
    t.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach((x) => x.classList.remove("active"));
      document.querySelectorAll(".panel").forEach((x) => x.classList.remove("active"));
      t.classList.add("active");
      document.getElementById(t.dataset.tab).classList.add("active");
      window.scrollTo({ top: 0, behavior: "smooth" });
    })
  );
}

// ===========================================================
//  Arranque
// ===========================================================
async function load() {
  try {
    const [g, m, tp] = await Promise.all([
      fetch("data/groups.json").then((r) => r.json()),
      fetch("data/matches.json").then((r) => r.json()),
      fetch("data/tips.json").then((r) => r.json()),
    ]);
    DATA.groups = g;
    DATA.matches = m.matches;
    DATA.updated = m.updated_utc;
    DATA.tips = tp;
  } catch (e) {
    document.querySelector("main").innerHTML =
      `<div class="empty">No se pudieron cargar los datos.<br>Si abriste el archivo directo, usa un servidor local (mira el LÉEME).</div>`;
    return;
  }

  // nota de zona horaria
  const tz = Intl.DateTimeFormat().resolvedOptions().timeZone || "tu zona";
  document.getElementById("tz-note").textContent =
    `🕐 Horarios mostrados en tu hora local (${tz})`;

  if (DATA.updated) {
    const u = new Date(DATA.updated);
    document.getElementById("updated").textContent =
      "Resultados actualizados: " + u.toLocaleString("es-CL");
  }

  renderHoy(); renderCalendario(); renderGrupos(); renderTips();
}

document.addEventListener("DOMContentLoaded", () => {
  setupTabs();
  document.querySelector(".lightbox-close").addEventListener("click", closeLightbox);
  document.getElementById("lightbox").addEventListener("click", (e) => {
    if (e.target.id === "lightbox") closeLightbox();
  });
  load();
});
