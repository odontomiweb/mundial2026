/* ===========================================================
   Mundial 2026 - Fase de grupos + Bracket
   Carga los datos y arma la pagina. Las horas se guardan en UTC
   y se muestran en la hora local de quien abre la pagina.
   =========================================================== */

let DATA = { groups: {}, matches: [], tips: {}, teams: {}, champion: {}, bracket: {}, updated: null };

// ---- banderas como imagen (Windows no dibuja los emoji de banderas) ----
const CODES = {
  "Mexico": "mx", "South Africa": "za", "South Korea": "kr", "Czechia": "cz",
  "Canada": "ca", "Bosnia and Herzegovina": "ba", "Qatar": "qa", "Switzerland": "ch",
  "Brazil": "br", "Morocco": "ma", "Haiti": "ht", "Scotland": "gb-sct",
  "United States": "us", "Paraguay": "py", "Australia": "au", "Turkiye": "tr",
  "Germany": "de", "Curacao": "cw", "Ivory Coast": "ci", "Ecuador": "ec",
  "Netherlands": "nl", "Japan": "jp", "Sweden": "se", "Tunisia": "tn",
  "Belgium": "be", "Egypt": "eg", "Iran": "ir", "New Zealand": "nz",
  "Spain": "es", "Cape Verde": "cv", "Saudi Arabia": "sa", "Uruguay": "uy",
  "France": "fr", "Senegal": "sn", "Iraq": "iq", "Norway": "no",
  "Argentina": "ar", "Algeria": "dz", "Austria": "at", "Jordan": "jo",
  "Portugal": "pt", "DR Congo": "cd", "Uzbekistan": "uz", "Colombia": "co",
  "England": "gb-eng", "Croatia": "hr", "Ghana": "gh", "Panama": "pa",
};
function flagImg(key) {
  const c = CODES[key];
  if (!c) return "";
  return `<img class="flag-img" src="https://flagcdn.com/32x24/${c}.png" srcset="https://flagcdn.com/64x48/${c}.png 2x" alt="" loading="lazy">`;
}

// ---- utilidades de fecha (hora local del visitante) ----
function dObj(m) { return new Date(m.kickoff_utc); }
function localDateKey(d) { return d.toLocaleDateString("en-CA"); }
function todayKey() { return new Date().toLocaleDateString("en-CA"); }
function fmtTime(d) { return d.toLocaleTimeString("es-CL", { hour: "2-digit", minute: "2-digit" }); }
function fmtDayTitle(d) {
  const s = d.toLocaleDateString("es-CL", { weekday: "long", day: "numeric", month: "long" });
  return s.charAt(0).toUpperCase() + s.slice(1);
}
function isFinished(m) { return m.status === "FINISHED" || (m.score1 !== null && m.score2 !== null && m.status !== "IN_PLAY"); }
function isLive(m) { return m.status === "IN_PLAY"; }
function hasScore(m) { return m.score1 !== null && m.score2 !== null; }

// ---- modelo de probabilidad por partido (estimado con ranking FIFA) ----
function winProbs(r1, r2) {
  const dr = (r1 || 1500) - (r2 || 1500);
  const We1 = 1 / (1 + Math.pow(10, -dr / 600));
  let pD = 0.30 - 0.0007 * Math.abs(dr);
  pD = Math.max(0.08, Math.min(0.30, pD));
  let p1 = Math.max(0.01, We1 - pD / 2);
  let p2 = Math.max(0.01, (1 - We1) - pD / 2);
  const s = p1 + p2 + pD;
  // redondeo que suma 100
  let a = Math.round((p1 / s) * 100);
  let d = Math.round((pD / s) * 100);
  let b = 100 - a - d;
  return { p1: a, pD: d, p2: b };
}

// ---- forma del equipo en el Mundial (resultados ya jugados) ----
function teamForma(key) {
  const ms = DATA.matches
    .filter((m) => (m.team1.key === key || m.team2.key === key) && isFinished(m) && hasScore(m))
    .sort((a, b) => dObj(a) - dObj(b));
  return ms.map((m) => {
    const me = m.team1.key === key ? m.score1 : m.score2;
    const ot = m.team1.key === key ? m.score2 : m.score1;
    return me > ot ? "G" : me < ot ? "P" : "E";
  });
}
function formaHtml(key) {
  const f = teamForma(key);
  if (!f.length) return `<span class="forma-empty">Aún sin jugar</span>`;
  const cls = { G: "g", E: "e", P: "p" };
  return f.map((r) => `<span class="forma-dot ${cls[r]}">${r}</span>`).join("");
}

// ===========================================================
//  Tarjeta de un partido (con detalle desplegable)
// ===========================================================
function teamMini(t) {
  const info = DATA.teams[t.key] || {};
  return `
  <div class="tm">
    <div class="tm-head">${flagImg(t.key)} <b>${t.name}</b></div>
    <div class="tm-row">🌐 Ranking FIFA: <b>#${info.rank ?? "?"}</b></div>
    <div class="tm-row">⭐ Figura: <b>${info.figura ?? "—"}</b></div>
    <div class="tm-row forma">📈 Forma: ${formaHtml(t.key)}</div>
    <div class="tm-note">${info.nota ?? ""}</div>
  </div>`;
}

function matchDetail(m) {
  const r1 = (DATA.teams[m.team1.key] || {}).rating;
  const r2 = (DATA.teams[m.team2.key] || {}).rating;
  const wp = winProbs(r1, r2);
  return `
  <div class="detail">
    <div class="winprob">
      <div class="wp-lbl">Probabilidad estimada (según ranking FIFA)</div>
      <div class="wp-bar">
        <span class="wp-seg s1" style="width:${wp.p1}%" title="Gana ${m.team1.name}"></span>
        <span class="wp-seg sd" style="width:${wp.pD}%" title="Empate"></span>
        <span class="wp-seg s2" style="width:${wp.p2}%" title="Gana ${m.team2.name}"></span>
      </div>
      <div class="wp-legend">
        <span><i class="dot s1"></i> ${m.team1.name} ${wp.p1}%</span>
        <span><i class="dot sd"></i> Empate ${wp.pD}%</span>
        <span><i class="dot s2"></i> ${m.team2.name} ${wp.p2}%</span>
      </div>
    </div>
    <div class="tm-grid">
      ${teamMini(m.team1)}
      ${teamMini(m.team2)}
    </div>
  </div>`;
}

function matchCard(m) {
  const d = dObj(m);
  const fin = isFinished(m);
  const live = isLive(m);
  const showScore = hasScore(m) || live;
  let w1 = false, w2 = false;
  if (fin && hasScore(m)) { w1 = m.score1 > m.score2; w2 = m.score2 > m.score1; }

  let mid;
  if (showScore) mid = `<div class="score">${m.score1 ?? 0} - ${m.score2 ?? 0}</div>`;
  else mid = `<div class="vs">VS</div><div class="time">${fmtTime(d)} hrs</div>`;

  let badge = `<span class="badge group">Grupo ${m.group}</span>`;
  if (live) badge = `<span class="badge live">● En vivo</span>`;
  else if (fin) badge = `<span class="badge fin">Final · Grupo ${m.group}</span>`;

  return `
  <details class="match-d">
    <summary class="match">
      <div class="side ${w1 ? "winner" : ""}">
        <span class="flag">${flagImg(m.team1.key)}</span>
        <span class="tname">${m.team1.name}</span>
      </div>
      <div class="mid">
        ${mid}
        <div>${badge}</div>
        <div class="meta">📍 ${m.city} · ver datos ▾</div>
      </div>
      <div class="side right ${w2 ? "winner" : ""}">
        <span class="flag">${flagImg(m.team2.key)}</span>
        <span class="tname">${m.team2.name}</span>
      </div>
    </summary>
    ${matchDetail(m)}
  </details>`;
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
  html += `<p class="hint">Toca un partido para ver datos de cada equipo y el % estimado.</p>`;
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
//  Panel GRUPOS
// ===========================================================
function groupFinished(letter) {
  return DATA.matches.filter((m) => m.group === letter && isFinished(m) && hasScore(m)).length >= 6;
}
function computeStandings(letter) {
  const teams = {};
  for (const t of DATA.groups[letter]) teams[t.key] = { ...t, pj: 0, g: 0, e: 0, p: 0, gf: 0, gc: 0, pts: 0 };
  for (const m of DATA.matches) {
    if (m.group !== letter || !hasScore(m) || !isFinished(m)) continue;
    const a = teams[m.team1.key], b = teams[m.team2.key];
    if (!a || !b) continue;
    a.pj++; b.pj++; a.gf += m.score1; a.gc += m.score2; b.gf += m.score2; b.gc += m.score1;
    if (m.score1 > m.score2) { a.g++; a.pts += 3; b.p++; }
    else if (m.score1 < m.score2) { b.g++; b.pts += 3; a.p++; }
    else { a.e++; b.e++; a.pts++; b.pts++; }
  }
  return Object.values(teams).sort((x, y) =>
    y.pts - x.pts || (y.gf - y.gc) - (x.gf - x.gc) || y.gf - x.gf || x.name.localeCompare(y.name));
}

function renderGrupos() {
  const el = document.getElementById("grupos");
  let html = `<h2 class="section-title">🏆 Grupos y tablas</h2>`;
  html += `<p class="qual-note"><span class="qual-dot"></span> Avanzan los <b>2 primeros</b> de cada grupo (y los 8 mejores terceros).</p>`;

  for (const letter of Object.keys(DATA.groups)) {
    const rows = computeStandings(letter);
    const prob = (DATA.tips.probabilidades || {})[letter] || [];
    const comentario = (DATA.tips.comentarios || {})[letter];
    const apunte = (DATA.tips.apuntes || {})[letter];
    const nameOf = (k) => (DATA.groups[letter].find((x) => x.key === k) || { name: k, flag: "" });

    html += `<div class="group-card">
      <h3><span class="gletter">${letter}</span> Grupo ${letter}</h3>
      <table class="standings">
        <thead><tr><th></th><th></th><th>PJ</th><th>G</th><th>E</th><th>P</th><th>GF</th><th>GC</th><th>DG</th><th>Pts</th></tr></thead>
        <tbody>
        ${rows.map((t, i) => `
          <tr class="${i < 2 ? "qualify" : ""}">
            <td class="pos">${i + 1}</td>
            <td class="team">${flagImg(t.key)} ${t.name}</td>
            <td>${t.pj}</td><td>${t.g}</td><td>${t.e}</td><td>${t.p}</td>
            <td>${t.gf}</td><td>${t.gc}</td><td>${t.gf - t.gc >= 0 ? "+" : ""}${t.gf - t.gc}</td>
            <td class="pts">${t.pts}</td>
          </tr>`).join("")}
        </tbody>
      </table>`;

    if (prob.length) {
      html += `<div class="prob-block"><div class="lbl">Probabilidad de ganar el grupo</div>`;
      for (const p of prob) {
        const t = nameOf(p.key);
        html += `<div class="prob-row">
          <span class="pteam">${flagImg(p.key)} ${t.name}</span>
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
  el.querySelectorAll("[data-img]").forEach((b) => b.addEventListener("click", () => openLightbox(b.dataset.img)));
}

// ===========================================================
//  Panel BRACKET
// ===========================================================
function teamByKey(key) {
  for (const g of Object.values(DATA.groups))
    for (const t of g) if (t.key === key) return t;
  return null;
}
function resolveSlot(code) {
  let m = code.match(/^([12])([A-L])$/);
  if (m) {
    const pos = +m[1], grp = m[2];
    if (groupFinished(grp)) {
      const t = computeStandings(grp)[pos - 1];
      if (t) return { key: t.key, name: t.name, real: true };
    }
    return { label: `${pos}º Grupo ${grp}` };
  }
  m = code.match(/^3:(.+)$/);
  if (m) return { label: `3º (${m[1]})` };
  m = code.match(/^W(\d+)$/);
  if (m) return { label: `Ganador ${m[1]}` };
  m = code.match(/^L(\d+)$/);
  if (m) return { label: `Perdedor ${m[1]}` };
  return { label: code };
}
function slotHtml(code) {
  const r = resolveSlot(code);
  if (r.real) return `<span class="bteam">${flagImg(r.key)}${r.name}</span>`;
  return `<span class="bslot">${r.label}</span>`;
}
function renderBracket() {
  const el = document.getElementById("bracket");
  let html = `<h2 class="section-title">🏆 Bracket (la llave)</h2>`;
  html += `<p class="hint">Resumen de la fase final. Los nombres se van llenando solos a medida que terminan los grupos y los partidos.</p>`;
  html += `<div class="bracket-scroll"><div class="bracket">`;
  for (const r of DATA.bracket.rondas) {
    html += `<div class="bround">
      <div class="bround-h">${r.nombre}<span>${r.fechas}</span></div>`;
    for (const p of r.partidos) {
      html += `<div class="bmatch">
        <div class="brow">${slotHtml(p.s1)}</div>
        <div class="bvs">vs</div>
        <div class="brow">${slotHtml(p.s2)}</div>
      </div>`;
    }
    html += `</div>`;
  }
  html += `</div></div>`;
  el.innerHTML = html;
}

// ===========================================================
//  Panel TIPS (campeón + curiosidades + notas)
// ===========================================================
function renderTips() {
  const el = document.getElementById("tips");
  const champ = DATA.champion || {};
  const lista = champ.lista || [];
  const cur = DATA.tips.curiosidades || [];
  const notas = DATA.tips.notas || [];
  let html = `<h2 class="section-title">💡 Tips y datos</h2>`;

  if (lista.length) {
    html += `<div class="tip-card">
      <h3>💰 Favoritos al título (casas de apuestas)</h3>
      <p class="src">${champ.fuente || ""} · ${champ.actualizado || ""}</p>`;
    const max = Math.max(...lista.map((x) => x.pct));
    for (const c of lista) {
      const t = teamByKey(c.key) || { name: c.key };
      html += `<div class="champ-row">
        <div class="champ-top">
          <span class="champ-name">${flagImg(c.key)} ${t.name}</span>
          <span class="champ-pct">${c.pct}%</span>
        </div>
        <div class="champ-bar-bg"><span class="champ-bar" style="width:${(c.pct / max) * 100}%"></span></div>
        <div class="champ-just">${c.justificacion}</div>
      </div>`;
    }
    html += `<p class="src">${champ.nota || ""}</p></div>`;
  }

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
  document.getElementById("lightbox-img").src = src;
  document.getElementById("lightbox").classList.add("open");
}
function closeLightbox() { document.getElementById("lightbox").classList.remove("open"); }

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
    const [g, m, tp, te, ch, br] = await Promise.all([
      fetch("data/groups.json").then((r) => r.json()),
      fetch("data/matches.json").then((r) => r.json()),
      fetch("data/tips.json").then((r) => r.json()),
      fetch("data/teams.json").then((r) => r.json()),
      fetch("data/champion.json").then((r) => r.json()),
      fetch("data/bracket.json").then((r) => r.json()),
    ]);
    DATA.groups = g; DATA.matches = m.matches; DATA.updated = m.updated_utc;
    DATA.tips = tp; DATA.teams = te; DATA.champion = ch; DATA.bracket = br;
  } catch (e) {
    document.querySelector("main").innerHTML =
      `<div class="empty">No se pudieron cargar los datos.<br>Si abriste el archivo directo, usa abrir.bat (mira el LÉEME).</div>`;
    return;
  }

  const tz = Intl.DateTimeFormat().resolvedOptions().timeZone || "tu zona";
  document.getElementById("tz-note").textContent = `🕐 Horarios en tu hora local (${tz})`;
  if (DATA.updated) {
    document.getElementById("updated").textContent =
      "Resultados actualizados: " + new Date(DATA.updated).toLocaleString("es-CL");
  }

  renderHoy(); renderCalendario(); renderGrupos(); renderBracket(); renderTips();
}

document.addEventListener("DOMContentLoaded", () => {
  setupTabs();
  document.querySelector(".lightbox-close").addEventListener("click", closeLightbox);
  document.getElementById("lightbox").addEventListener("click", (e) => { if (e.target.id === "lightbox") closeLightbox(); });
  load();
});
