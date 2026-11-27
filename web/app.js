"use strict";

// Die Länder und ihre Einstellungen kommen aus laender.json (erzeugt von build_site.py aus laender/*.py),
// die Bankdaten aus der API (api/v1/<CC>/alle.json). Für ein neues Land ist hier nichts zu ändern.

const PAGE = 100;
const $ = (s) => document.querySelector(s);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const fmtDate = (iso) => { if (!iso) return ""; const [y, m, d] = iso.split("-"); return `${d}.${m}.${y}`; };
const fmtNum = (n) => n.toLocaleString("de-AT");
const norm = (s) => String(s ?? "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/ß/g, "ss");
const get = (obj, path) => path.split(".").reduce((o, k) => (o == null ? o : o[k]), obj);
const plzOrt = (a) => [a?.plz, a?.ort].filter(Boolean).join(" ");

// Semikolon-CSV mit Anführungszeichen (wie von Pythons csv-Modul geschrieben).
function parseCSV(text) {
  text = text.replace(/^﻿/, "");
  const rows = [];
  let row = [], field = "", quoted = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (quoted) {
      if (c === '"') {
        if (text[i + 1] === '"') { field += '"'; i++; } else quoted = false;
      } else field += c;
    } else if (c === '"') quoted = true;
    else if (c === ";") { row.push(field); field = ""; }
    else if (c === "\n" || c === "\r") {
      if (c === "\r" && text[i + 1] === "\n") i++;
      row.push(field); rows.push(row); row = []; field = "";
    } else field += c;
  }
  if (field !== "" || row.length) { row.push(field); rows.push(row); }
  const header = rows.shift() || [];
  return rows.filter((r) => r.some((v) => v !== "")).map((r) => Object.fromEntries(header.map((h, i) => [h, r[i] ?? ""])));
}

async function fetchText(url) {
  const res = await fetch(url, { cache: "no-cache" });
  if (!res.ok) throw new Error(`${url}: HTTP ${res.status}`);
  return res.text();
}

const state = { laender: {}, country: null, data: {}, filtered: [], shown: 0, days: [], loadedDays: new Map(), build: null };
const C = () => state.laender[state.country];
const D = () => state.data[state.country];

/* ---------- Daten eines Landes ---------- */

function prepare(conf, records) {
  const all = new Map();
  const active = [], removed = [];
  for (const r of records) {
    // Bankleitzahl zusätzlich in IBAN-Schreibweise suchbar (z. B. 200 -> 0200)
    const padded = conf.blz_stellen ? r.bankleitzahl.padStart(conf.blz_stellen, "0") : "";
    const b = {
      rec: r,
      blz: r.bankleitzahl,
      blzKeys: new Set([r.bankleitzahl, padded].filter(Boolean)),
      search: norm([...conf.suche.map((p) => get(r, p)), ...(conf.suche_listen || []).flatMap((p) => get(r, p) || []), padded]
        .filter(Boolean).join(" ")),
      branchSearch: (r.filialen || []).map((f) => norm((conf.filial_suche || ["bic", "name", "plz", "ort"])
        .map((k) => f[k]).filter(Boolean).join(" "))),
    };
    all.set(b.blz, b);
    (r.status === "aktiv" ? active : removed).push(b);
  }
  return { all, banks: active, removed };
}

function col5(conf, r) {
  const v = get(r, conf.spalte5.feld);
  if (conf.spalte5.art === "anzahl") return Array.isArray(v) && v.length ? fmtNum(v.length) : "–";
  if (conf.spalte5.art === "ja_nein") return v === true ? "ja" : v === false ? "nein" : "";
  return v ?? "";
}

/* ---------- Suche ---------- */

function highlight(text, terms) {
  let html = esc(text);
  for (const t of terms) {
    if (!t) continue;
    const re = new RegExp(`(${t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})`, "ig");
    html = html.replace(re, "<mark>$1</mark>");
  }
  return html;
}

function matchBank(b, terms) {
  // jeder Suchbegriff muss in der Bank selbst oder in einer ihrer Filialen vorkommen
  let branchHit = null;
  for (const t of terms) {
    if (b.search.includes(t)) continue;
    const i = b.branchSearch.findIndex((s) => s.includes(t));
    if (i < 0) return null;
    branchHit ??= b.rec.filialen[i];
  }
  return { branchHit };
}

function applyFilter() {
  if (!D()) return;
  const conf = C();
  const terms = norm($("#q").value.trim()).split(/\s+/).filter(Boolean);
  const active = conf.filter.map((f, i) => [f.feld, $(`#f-${i}`)?.value]).filter(([, v]) => v);
  state.filtered = [];
  for (const b of D().banks) {
    if (active.some(([feld, v]) => get(b.rec, feld) !== v)) continue;
    const m = matchBank(b, terms);
    if (m) state.filtered.push({ b, branchHit: m.branchHit });
  }
  // entfernte/überführte Bankleitzahlen nur bei exakter Eingabe der Bankleitzahl zeigen
  const raw = $("#q").value.trim().split(/\s+/).filter(Boolean);
  if (raw.length === 1) for (const b of D().removed) if (b.blzKeys.has(raw[0])) state.filtered.push({ b, branchHit: null });
  // exakte Treffer der Bankleitzahl zuerst (z. B. ABI 1010 vor Filialen mit CAB 01010)
  if (raw.length === 1) {
    const exakt = (x) => (x.b.blzKeys.has(raw[0]) ? 0 : 1);
    state.filtered.sort((x, y) => exakt(x) - exakt(y));
  }
  state.shown = 0;
  $("#rows").innerHTML = "";
  renderMore();
  const n = state.filtered.length;
  $("#result-count").textContent = `${fmtNum(n)} ${n === 1 ? "Eintrag" : "Einträge"}`;
  updateHash();
}

function renderMore() {
  const conf = C();
  const terms = $("#q").value.trim().split(/\s+/).filter(Boolean);
  const slice = state.filtered.slice(state.shown, state.shown + PAGE);
  if (!state.filtered.length) $("#rows").innerHTML = `<tr><td colspan="5" class="empty">Keine Bank gefunden.</td></tr>`;
  $("#rows").insertAdjacentHTML("beforeend", slice.map(({ b, branchHit: f }) => {
    const r = b.rec;
    return `
    <tr data-blz="${esc(b.blz)}" tabindex="0">
      <td>${highlight(r.bankleitzahl, terms)}</td>
      <td>${highlight(r.bic, terms) || "–"}</td>
      <td>${highlight(r.name, terms)}${r.art === "Filiale" ? ' <span class="branch">(Filiale)</span>' : ""}${r.loeschung_angekuendigt ? ' <span class="tag entfernt small">Löschung angekündigt</span>' : ""}${r.status === "entfernt" ? ` <span class="tag entfernt small">entfernt${r.nachfolge_bankleitzahl ? ` → ${esc(r.nachfolge_bankleitzahl)}` : ""}</span>` : ""}
        ${f ? `<div class="branch">Filiale: ${f.cab ? `<span class="mono">CAB ${highlight(f.cab, terms)}</span> · ` : ""}${highlight([f.plz, f.ort].filter(Boolean).join(" "), terms)}${f.strasse ? `, ${highlight(f.strasse, terms)}` : ""}${f.bic ? ` · <span class="mono">${highlight(f.bic, terms)}</span>` : ""}${f.name && f.name !== r.name ? ` · ${highlight(f.name, terms)}` : ""}</div>` : ""}</td>
      <td class="hide-sm">${highlight(plzOrt(r.adresse), terms) || "–"}</td>
      <td class="hide-md">${esc(col5(conf, r))}</td>
    </tr>`;
  }).join(""));
  state.shown += slice.length;
  $("#more").hidden = state.shown >= state.filtered.length;
}

/* ---------- Detail ---------- */

function fieldHtml(value, kind = "") {
  if (value == null || value === "" || value === false) return null;
  if (kind === "adresse") {
    const text = [value.strasse, value.postfach && `Postfach ${value.postfach}`, plzOrt(value)].filter(Boolean).join(", ");
    return text ? esc(text) : null;
  }
  if (kind.startsWith("ja:")) return value === true ? esc(kind.slice(3)) : null;
  if (kind === "liste") return Array.isArray(value) && value.length ? esc(value.join(", ")) : null;
  if (typeof value === "object") return null;
  const html = esc(value);
  const copy = ` <button class="copy" data-copy="${html}">Kopieren</button>`;
  switch (kind) {
    case "kopieren": return `<span class="mono">${html}</span>${copy}`;
    case "lei": return `<span class="mono">${html}</span> · <a href="https://search.gleif.org/#/record/${encodeURIComponent(value)}" target="_blank" rel="noopener">GLEIF</a>${copy}`;
    case "email": return `<a href="mailto:${html}">${html}</a>`;
    case "url": return `<a href="${esc(/^https?:/.test(value) ? value : "https://" + value)}" target="_blank" rel="noopener">${html}</a>`;
    case "datum": return esc(fmtDate(value));
    case "blz": return `<span class="mono">${html}</span>${D().all.has(value) ? ` · <a href="#" data-open-blz="${html}">anzeigen</a>` : ""}`;
    default: return html;
  }
}

function showDetail(b, note, hit) {
  const r = b.rec;
  if (!note && r.status === "entfernt") note = r.entfernt_am
    ? `Am ${fmtDate(r.entfernt_am)} aus dem Verzeichnis entfernt – letzter bekannter Stand.`
    : `Nicht mehr im Verzeichnis${r.nachfolge_bankleitzahl ? `, überführt in ${r.nachfolge_bankleitzahl}` : ""}.`;
  const rows = C().details.map(([label, path, kind]) => {
    const h = fieldHtml(get(r, path), kind);
    return h ? `<dt>${esc(label)}</dt><dd>${h}</dd>` : "";
  }).join("");
  const fil = r.filialen || [];
  const spalten = C().filial_spalten || [["Ort", "plz_ort"], ["BIC", "bic", "mono"], ["Name", "name"]];
  let branches = "";
  if (fil.length) {
    branches = `<details class="branches" ${fil.length <= 8 || hit ? "open" : ""}>
      <summary>${fmtNum(fil.length)} weitere ${fil.length === 1 ? "Ort" : "Orte"} mit dieser Bankleitzahl</summary>
      ${fil.some((f) => f.bic) ? '<p class="hint">Für Zahlungen gilt der BIC oben. Filial-BICs und abweichende Namen dienen nur der Zuordnung.</p>' : ""}
      <table class="mini"><thead><tr>${spalten.map(([t]) => `<th>${esc(t)}</th>`).join("")}</tr></thead><tbody>
      ${fil.map((f) => `<tr${f === hit ? ' class="hit"' : ""}>${spalten.map(([, k, art]) => {
        const v = k === "plz_ort" ? plzOrt(f) : k === "name" && f.name === r.name ? "" : f[k];
        return `<td${art === "mono" ? ' class="mono"' : ""}>${esc(v) || (art === "mono" ? "–" : "")}</td>`;
      }).join("")}</tr>`).join("")}
      </tbody></table></details>`;
  }
  $("#detail-body").innerHTML = `<h2>${esc(r.name)}</h2>${note ? `<p class="hint">${esc(note)}</p>` : ""}<dl class="kv">${rows}</dl>${branches}`;
  if (!$("#detail").open) $("#detail").showModal();
  $("#detail tr.hit")?.scrollIntoView({ block: "nearest" });
}

/* ---------- Änderungen ---------- */

function renderDays() {
  const box = $("#days");
  $("#changes-hint").textContent = C().hinweis_aenderungen;
  if (!state.days.length) {
    box.innerHTML = `<p class="empty">Noch keine Änderungen seit Beginn der Aufzeichnung.</p>`;
    return;
  }
  box.innerHTML = state.days.map((d, i) => `
    <details class="day" data-day="${d.datum}" ${i === 0 ? "open" : ""}>
      <summary><strong>${fmtDate(d.datum)}</strong>
        ${d.neu ? `<span class="tag neu">${d.neu} neu</span>` : ""}
        ${d.geaendert ? `<span class="tag geändert">${d.geaendert} geändert</span>` : ""}
        ${d.entfernt ? `<span class="tag entfernt">${d.entfernt} entfernt</span>` : ""}
      </summary>
      <div class="day-body"><p class="loading">lädt …</p></div>
    </details>`).join("");
  box.querySelectorAll("details").forEach((el) => {
    el.addEventListener("toggle", () => el.open && loadDay(el));
    if (el.open) loadDay(el);
  });
}

async function loadDay(el) {
  const day = el.dataset.day, cc = state.country, key = `${cc}/${day}`, conf = C();
  if (state.loadedDays.has(key)) return;
  state.loadedDays.set(key, null);
  const body = el.querySelector(".day-body");
  const url = `${conf.aenderungen}${day}.csv`;
  try {
    const rows = parseCSV(await fetchText(url));
    state.loadedDays.set(key, rows);
    body.innerHTML = `<p class="mono" style="margin:0;padding:6px 14px 0;text-align:right"><a href="${url}" download>CSV</a></p>` +
      rows.map((r) => {
        const fields = r["Geänderte Felder"] ? r["Geänderte Felder"].split(" | ").map((f) => {
          const m = f.match(/^(.*?): (.*) -> (.*)$/);
          return m ? `<div>${esc(m[1])}: <del>${esc(m[2]) || "(leer)"}</del> → <ins>${esc(m[3]) || "(leer)"}</ins></div>` : `<div>${esc(f)}</div>`;
        }).join("") : "";
        const known = D().all.has(r.Bankleitzahl);
        const label = `<span class="mono">${esc(r.Bankleitzahl)}</span> · ${esc(r[conf.aenderung_name])}`;
        return `<div class="change"><span><span class="tag ${esc(r["Änderung"])}">${esc(r["Änderung"])}</span></span>
          <span>${known ? `<a href="#" data-open-blz="${esc(r.Bankleitzahl)}">${label}</a>` : label}
          <span class="mono">${esc(r[conf.aenderung_bic])}</span></span>
          ${fields ? `<div class="fields">${fields}</div>` : ""}</div>`;
      }).join("");
  } catch (err) {
    state.loadedDays.delete(key);
    body.innerHTML = `<p class="loading">Fehler beim Laden: ${esc(err.message)}</p>`;
  }
}

/* ---------- Land wechseln ---------- */

function updateHash() {
  const q = $("#q").value.trim();
  const first = Object.keys(state.laender)[0];
  const parts = [];
  if (state.country !== first) parts.push(`land=${state.country}`);
  if (q) parts.push(`q=${encodeURIComponent(q)}`);
  try { history.replaceState(null, "", parts.length ? `#${parts.join("&")}` : location.pathname); } catch {}
}

function renderMeta() {
  const d = D();
  if (!d) return;
  const parts = [`${fmtNum(d.banks.length)} Bankleitzahlen`];
  if (C().stand_text) parts.push(C().stand_text);
  if (state.build?.geprueft) parts.push(`geprüft am ${fmtDate(state.build.geprueft)}`);
  if (state.days.length) parts.push(`letzte Änderung ${fmtDate(state.days[0].datum)}`);
  $("#meta").textContent = parts.join(" · ");
}

function renderFilters(conf) {
  $("#filters-extra").innerHTML = conf.filter.map((f, i) => `
    <label><span class="sr">${esc(f.alle)}</span><select id="f-${i}"><option value="">${esc(f.alle)}</option>
    ${[...new Set(D().banks.map((b) => get(b.rec, f.feld)).filter(Boolean))].sort((a, b) => a.localeCompare(b, "de"))
      .map((v) => `<option>${esc(v)}</option>`).join("")}</select></label>`).join("");
  conf.filter.forEach((_, i) => $(`#f-${i}`).addEventListener("change", applyFilter));
}

async function selectCountry(cc) {
  if (!state.laender[cc]) cc = Object.keys(state.laender)[0];
  state.country = cc;
  const conf = C();
  document.querySelectorAll("[data-country]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.country === cc)));
  $("#source").textContent = conf.quelle.kurz;
  renderAttribution(conf);
  $("#q").placeholder = conf.suche_platzhalter;
  $("#col5").textContent = conf.spalte5.titel;
  document.querySelectorAll("a.dl").forEach((a) => (a.href = conf.csv));
  $("#filters-extra").innerHTML = "";
  $("#meta").textContent = "lädt …";
  $("#rows").innerHTML = `<tr><td colspan="5" class="empty">lädt …</td></tr>`;
  $("#result-count").textContent = "";

  if (!state.data[cc]) {
    try {
      const [records, days] = await Promise.all([
        fetchText(conf.daten).then(JSON.parse),
        fetchText(`${conf.aenderungen}index.json`).then(JSON.parse).catch(() => []),
      ]);
      state.data[cc] = { ...prepare(conf, records), days };
    } catch (err) {
      if (state.country !== cc) return;
      $("#rows").innerHTML = `<tr><td colspan="5" class="empty">Daten konnten nicht geladen werden (${esc(err.message)}).</td></tr>`;
      $("#meta").textContent = "Daten nicht verfügbar";
      return;
    }
  }
  if (state.country !== cc) return; // inzwischen umgeschaltet
  state.days = D().days;
  $("#changes-badge").textContent = state.days.length || "";
  renderFilters(conf);
  renderMeta();
  applyFilter();
  renderDays();
}

/* ---------- Quellenangabe des gewählten Landes ---------- */

function renderAttribution(conf) {
  const q = conf.quelle;
  const links = [`<a href="${esc(q.url)}">Quelle</a>`, `<a href="${esc(q.bedingungen)}">Nutzungsbedingungen</a>`];
  if (q.lizenz) links.push(`<a href="${esc(q.lizenz)}">Lizenz CC BY 4.0</a>`);
  if (conf.original) links.push(`<a href="${esc(conf.original)}" download>Originaldatei</a>`);
  $("#attribution").innerHTML = `<strong>${esc(conf.name)}:</strong> ${esc(q.hinweis || q.name)} · ${links.join(" · ")}`;
  $("#swift").hidden = !conf.zusatz_hinweis;
  $("#swift").textContent = conf.zusatz_hinweis ? `BICs (Italien): ${conf.zusatz_hinweis}` : "";
}

/* ---------- Tabs & Start ---------- */

function selectTab(name) {
  for (const t of ["suche", "aenderungen"]) {
    $(`#tab-${t}`).setAttribute("aria-selected", String(t === name));
    $(`#view-${t}`).hidden = t !== name;
  }
}

function openBlz(blz) {
  const b = D()?.all.get(blz);
  if (b) showDetail(b);
}

async function init() {
  $("#tab-suche").addEventListener("click", () => selectTab("suche"));
  $("#tab-aenderungen").addEventListener("click", () => selectTab("aenderungen"));
  $("#q").addEventListener("input", applyFilter);
  $("#more-btn").addEventListener("click", () => renderMore());
  const openRow = (tr) => { const hit = state.filtered.find((x) => x.b.blz === tr.dataset.blz); if (hit) showDetail(hit.b, "", hit.branchHit); };
  $("#rows").addEventListener("click", (e) => { const tr = e.target.closest("tr[data-blz]"); if (tr) openRow(tr); });
  $("#rows").addEventListener("keydown", (e) => { const tr = e.target.closest("tr[data-blz]"); if (tr && e.key === "Enter") openRow(tr); });
  $("#days").addEventListener("click", (e) => {
    const a = e.target.closest("[data-open-blz]");
    if (a) { e.preventDefault(); openBlz(a.dataset.openBlz); }
  });
  $("#detail").addEventListener("click", (e) => {
    if (e.target === $("#detail")) $("#detail").close();
    const btn = e.target.closest("[data-copy]");
    if (btn) navigator.clipboard?.writeText(btn.dataset.copy).then(() => { btn.textContent = "Kopiert"; setTimeout(() => (btn.textContent = "Kopieren"), 1200); });
    const link = e.target.closest("[data-open-blz]");
    if (link) { e.preventDefault(); openBlz(link.dataset.openBlz); }
  });

  try {
    state.laender = JSON.parse(await fetchText("laender.json"));
  } catch (err) {
    $("#meta").textContent = "Daten nicht verfügbar";
    $("#rows").innerHTML = `<tr><td colspan="5" class="empty">Länderliste konnte nicht geladen werden (${esc(err.message)}).</td></tr>`;
    return;
  }
  $("#countries").innerHTML = Object.entries(state.laender).map(([cc, l]) =>
    `<button type="button" data-country="${esc(cc)}" aria-pressed="false" title="${esc(l.name)}" aria-label="${esc(l.name)}"><span class="cc">${esc(cc)}</span><span class="cn"> ${esc(l.name)}</span></button>`).join("");
  document.querySelectorAll("[data-country]").forEach((b) => b.addEventListener("click", () => {
    if (b.dataset.country !== state.country) selectCountry(b.dataset.country);
  }));
  const quellen = new Map(Object.values(state.laender).map((l) => [l.quelle.url, l.quelle]));
  $("#sources").innerHTML = [...quellen.values()].map((q) =>
    `<a href="${esc(q.url)}">${esc(q.name.split(" – ")[0])}</a>${q.bedingungen !== q.url ? ` (<a href="${esc(q.bedingungen)}">Bedingungen</a>)` : ""}`).join(", ");

  const params = new URLSearchParams(location.hash.slice(1));
  if (params.get("q")) $("#q").value = params.get("q");
  fetchText("build.json").then((t) => { state.build = JSON.parse(t); renderMeta(); }).catch(() => {});
  await selectCountry((params.get("land") || "").toUpperCase());
}

init();
