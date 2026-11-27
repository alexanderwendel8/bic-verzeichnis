"use strict";

const PAGE = 100;
const $ = (s) => document.querySelector(s);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const fmtDate = (iso) => { if (!iso) return ""; const [y, m, d] = iso.split("-"); return `${d}.${m}.${y}`; };
const fmtNum = (n) => n.toLocaleString("de-AT");
const norm = (s) => String(s ?? "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/ß/g, "ss");

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

/* ---------- Länder ---------- */

const COUNTRIES = {
  AT: {
    label: "Österreich",
    csv: "data/sepa-zv-vz_gesamt.csv",
    changes: "changes/",
    col5: "Sektor",
    filters: true,
    placeholder: "Bankleitzahl, BIC, Bankname, Ort oder LEI …",
    hint: "Täglicher Vergleich mit dem Vortag. Banken, die aus dem OeNB-Verzeichnis verschwinden, bleiben hier mit ihrem letzten Stand erhalten.",
    source: "OeNB-Verzeichnis",
    async load() {
      const rows = parseCSV(await fetchText(this.csv));
      return { banks: rows.map((r) => this.bank(r)), info: null };
    },
    bank(r) {
      return {
        blz: r.Bankleitzahl, bic: r["SWIFT-Code"], name: r.Bankenname, plz: r.PLZ, ort: r.Ort,
        col5: r.Sektor, land: r.Bundesland, sektor: r.Sektor, isBranch: r.Kennzeichen === "Filiale",
        branches: [], raw: r,
        search: norm([r.Bankleitzahl, r["SWIFT-Code"], r.Bankenname, r.PLZ, r.Ort, r.LEI, r.Bundesland, r.Sektor].join(" ")),
      };
    },
    changeName: (r) => r.Bankenname,
    changeBic: (r) => r["SWIFT-Code"],
    detail(b) {
      const r = b.raw;
      return [
        ["Bankleitzahl", r.Bankleitzahl, "copy"], ["BIC", r["SWIFT-Code"], "copy"], ["LEI", r.LEI, "lei"],
        ["Art", r.Kennzeichen], ["Sektor", r.Sektor], ["Institutsart", r.Institutsart],
        ["Identnummer", r.Identnummer], ["Firmenbuchnummer", r.Firmenbuchnummer === "nullnull" ? "" : r.Firmenbuchnummer],
        ["Adresse", [r["Straße"], [r.PLZ, r.Ort].filter(Boolean).join(" ")].filter(Boolean).join(", ")],
        ["Postadresse", [r["Postadresse / Straße"], r.Postfach && `Postfach ${r.Postfach}`,
          [r["Postadresse / PLZ"], r["Postadresse / Ort"]].filter(Boolean).join(" ")].filter(Boolean).join(", ")],
        ["Bundesland", r.Bundesland], ["Telefon", r.Telefon], ["Fax", r.Fax],
        ["E-Mail", r["E-Mail"], "mail"], ["Homepage", r.Homepage, "url"], ["Gründungsdatum", r["Gründungsdatum"]],
      ];
    },
  },
  DE: {
    label: "Deutschland",
    csv: "data/de/bankleitzahlen.csv",
    changes: "changes/de/",
    col5: "Filialen",
    filters: false,
    placeholder: "Bankleitzahl, BIC (auch Filial-BIC), Bankname oder Ort …",
    hint: "Die Bundesbank aktualisiert die Bankleitzahlendatei viermal im Jahr (März, Juni, September, Dezember). Änderungen stehen unter dem Tag, ab dem sie gelten. Gelöschte Bankleitzahlen bleiben mit ihrem letzten Stand erhalten.",
    source: "Bankleitzahlendatei",
    async load() {
      const [banks, branches, meta] = await Promise.all([
        fetchText(this.csv), fetchText("data/de/filialen.csv"), fetchText("data/de/meta.json"),
      ]);
      const byBlz = new Map();
      for (const f of parseCSV(branches)) {
        if (!byBlz.has(f.Bankleitzahl)) byBlz.set(f.Bankleitzahl, []);
        byBlz.get(f.Bankleitzahl).push(f);
      }
      return { banks: parseCSV(banks).map((r) => this.bank(r, byBlz.get(r.Bankleitzahl) || [])), info: JSON.parse(meta) };
    },
    bank(r, branches = []) {
      return {
        blz: r.Bankleitzahl, bic: r.BIC, name: r.Bezeichnung, plz: r.PLZ, ort: r.Ort,
        col5: branches.length ? fmtNum(branches.length) : "–", isBranch: false,
        announced: r["Bankleitzahllöschung"] === "1",
        branches, raw: r,
        search: norm([r.Bankleitzahl, r.BIC, r.Bezeichnung, r.Kurzbezeichnung, r.PLZ, r.Ort].join(" ")),
        branchSearch: branches.map((f) => norm([f.BIC, f.Bezeichnung, f.Kurzbezeichnung, f.PLZ, f.Ort].join(" "))),
      };
    },
    changeName: (r) => r.Bezeichnung,
    changeBic: (r) => r.BIC,
    detail(b) {
      const r = b.raw, succ = r["Nachfolge-Bankleitzahl"];
      const hasSucc = succ && succ !== "00000000";
      return [
        ["Bankleitzahl", r.Bankleitzahl, "copy"], ["BIC", r.BIC, "copy"],
        ["Kurzbezeichnung", r.Kurzbezeichnung],
        ["Ort", [r.PLZ, r.Ort].filter(Boolean).join(" ")],
        ["Löschung", b.announced ? "angekündigt – Bankleitzahl wird künftig gelöscht" : ""],
        ["Nachfolge-BLZ", hasSucc ? succ : "", "blz"],
        ["Prüfziffermethode", r["Prüfzifferberechnungsmethode"]],
        ["Kartennummer (PAN)", r.PAN],
        ["Datensatznummer", r.Datensatznummer],
      ];
    },
  },
};

const state = { country: "AT", data: {}, filtered: [], shown: 0, days: [], loadedDays: new Map(), build: null };
const C = () => COUNTRIES[state.country];
const D = () => state.data[state.country];

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
    const i = (b.branchSearch || []).findIndex((s) => s.includes(t));
    if (i < 0) return null;
    branchHit ??= b.branches[i];
  }
  return { branchHit };
}

function applyFilter() {
  if (!D()) return;
  const q = $("#q").value.trim();
  const terms = norm(q).split(/\s+/).filter(Boolean);
  const land = $("#f-land").value, sektor = $("#f-sektor").value;
  state.filtered = [];
  for (const b of D().banks) {
    if (C().filters && ((land && b.land !== land) || (sektor && b.sektor !== sektor))) continue;
    const m = matchBank(b, terms);
    if (m) state.filtered.push({ b, branchHit: m.branchHit });
  }
  state.shown = 0;
  $("#rows").innerHTML = "";
  renderMore();
  const n = state.filtered.length;
  $("#result-count").textContent = `${fmtNum(n)} ${n === 1 ? "Eintrag" : "Einträge"}`;
  updateHash();
}

function renderMore() {
  const terms = $("#q").value.trim().split(/\s+/).filter(Boolean);
  const slice = state.filtered.slice(state.shown, state.shown + PAGE);
  if (!state.filtered.length) {
    $("#rows").innerHTML = `<tr><td colspan="5" class="empty">Keine Bank gefunden.</td></tr>`;
  }
  $("#rows").insertAdjacentHTML("beforeend", slice.map(({ b, branchHit }) => `
    <tr data-blz="${esc(b.blz)}" tabindex="0">
      <td>${highlight(b.blz, terms)}</td>
      <td>${highlight(b.bic, terms) || "–"}</td>
      <td>${highlight(b.name, terms)}${b.isBranch ? ' <span class="branch">(Filiale)</span>' : ""}${b.announced ? ' <span class="tag entfernt small">Löschung angekündigt</span>' : ""}
        ${branchHit ? `<div class="branch">Filiale: ${highlight([branchHit.PLZ, branchHit.Ort].filter(Boolean).join(" "), terms)}${branchHit.BIC ? ` · <span class="mono">${highlight(branchHit.BIC, terms)}</span>` : ""}${branchHit.Bezeichnung !== b.name ? ` · ${highlight(branchHit.Bezeichnung, terms)}` : ""}</div>` : ""}</td>
      <td class="hide-sm">${highlight([b.plz, b.ort].filter(Boolean).join(" "), terms)}</td>
      <td class="hide-md">${esc(b.col5)}</td>
    </tr>`).join(""));
  state.shown += slice.length;
  $("#more").hidden = state.shown >= state.filtered.length;
}

/* ---------- Detail ---------- */

function fieldHtml(value, kind) {
  let html = esc(value);
  if (kind === "mail") return `<a href="mailto:${esc(value)}">${html}</a>`;
  if (kind === "url") return `<a href="${esc(/^https?:/.test(value) ? value : "https://" + value)}" target="_blank" rel="noopener">${html}</a>`;
  if (kind === "lei") return `<span class="mono">${html}</span> · <a href="https://search.gleif.org/#/record/${encodeURIComponent(value)}" target="_blank" rel="noopener">GLEIF</a> <button class="copy" data-copy="${esc(value)}">Kopieren</button>`;
  if (kind === "blz") {
    const known = D().banks.some((x) => x.blz === value);
    return `<span class="mono">${html}</span>${known ? ` · <a href="#" data-open-blz="${esc(value)}">anzeigen</a>` : ""}`;
  }
  if (kind === "copy") return `<span class="mono">${html}</span> <button class="copy" data-copy="${esc(value)}">Kopieren</button>`;
  return html;
}

function showDetail(b, note, hit) {
  const rows = C().detail(b)
    .filter(([, v]) => v)
    .map(([label, v, kind]) => `<dt>${label}</dt><dd>${fieldHtml(v, kind)}</dd>`).join("");
  let branches = "";
  if (b.branches.length) {
    branches = `<details class="branches" ${b.branches.length <= 8 || hit ? "open" : ""}>
      <summary>${fmtNum(b.branches.length)} weitere ${b.branches.length === 1 ? "Ort" : "Orte"} mit dieser Bankleitzahl</summary>
      <p class="hint">Für Zahlungen gilt der BIC oben. Filial-BICs und abweichende Namen dienen nur der Zuordnung.</p>
      <table class="mini"><thead><tr><th>Ort</th><th>BIC</th><th>Name</th></tr></thead><tbody>
      ${b.branches.map((f) => `<tr${f === hit ? ' class="hit"' : ""}><td>${esc([f.PLZ, f.Ort].filter(Boolean).join(" "))}</td>
        <td class="mono">${esc(f.BIC) || "–"}</td><td>${f.Bezeichnung !== b.name ? esc(f.Bezeichnung) : ""}</td></tr>`).join("")}
      </tbody></table></details>`;
  }
  $("#detail-body").innerHTML = `<h2>${esc(b.name)}</h2>${note ? `<p class="hint">${note}</p>` : ""}<dl class="kv">${rows}</dl>${branches}`;
  if (!$("#detail").open) $("#detail").showModal();
  $("#detail tr.hit")?.scrollIntoView({ block: "nearest" });
}

/* ---------- Änderungen ---------- */

function renderDays() {
  const box = $("#days");
  $("#changes-hint").textContent = C().hint;
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
  const url = `${conf.changes}${day}.csv`;
  try {
    const rows = parseCSV(await fetchText(url));
    state.loadedDays.set(key, rows);
    body.innerHTML = `<p class="mono" style="margin:0;padding:6px 14px 0;text-align:right"><a href="${url}" download>CSV</a></p>` +
      rows.map((r, i) => {
        const fields = r["Geänderte Felder"] ? r["Geänderte Felder"].split(" | ").map((f) => {
          const m = f.match(/^(.*?): (.*) -> (.*)$/);
          return m ? `<div>${esc(m[1])}: <del>${esc(m[2]) || "(leer)"}</del> → <ins>${esc(m[3]) || "(leer)"}</ins></div>` : `<div>${esc(f)}</div>`;
        }).join("") : "";
        return `<div class="change"><span><span class="tag ${esc(r["Änderung"])}">${esc(r["Änderung"])}</span></span>
          <span><a href="#" data-day-row="${i}"><span class="mono">${esc(r.Bankleitzahl)}</span> · ${esc(conf.changeName(r))}</a>
          <span class="mono">${esc(conf.changeBic(r))}</span></span>
          ${fields ? `<div class="fields">${fields}</div>` : ""}</div>`;
      }).join("");
    body.querySelectorAll("[data-day-row]").forEach((a) => a.addEventListener("click", (e) => {
      e.preventDefault();
      const r = rows[+a.dataset.dayRow];
      const current = r["Änderung"] !== "entfernt" && D().banks.find((x) => x.blz === r.Bankleitzahl);
      const note = r["Änderung"] === "entfernt"
        ? `Am ${fmtDate(day)} aus dem ${conf.source} entfernt – letzter bekannter Stand.` : "";
      showDetail(current || conf.bank(r), note);
    }));
  } catch (err) {
    state.loadedDays.delete(key);
    body.innerHTML = `<p class="loading">Fehler beim Laden: ${esc(err.message)}</p>`;
  }
}

/* ---------- Land wechseln ---------- */

function updateHash() {
  const q = $("#q").value.trim();
  const parts = [];
  if (state.country !== "AT") parts.push(`land=${state.country}`);
  if (q) parts.push(`q=${encodeURIComponent(q)}`);
  try { history.replaceState(null, "", parts.length ? `#${parts.join("&")}` : location.pathname); } catch {}
}

function renderMeta() {
  const d = D();
  if (!d) return;
  let meta = `${fmtNum(d.banks.length)} ${state.country === "DE" ? "Bankleitzahlen" : "Einträge"}`;
  if (d.info?.ValidFrom) meta += ` · Bundesbank-Datei gültig ${fmtDate(d.info.ValidFrom)}–${fmtDate(d.info.ValidTill)}`;
  if (state.build?.geprueft) meta += ` · geprüft am ${fmtDate(state.build.geprueft)}`;
  if (state.days.length) meta += ` · letzte Änderung ${fmtDate(state.days[0].datum)}`;
  $("#meta").textContent = meta;
}

async function selectCountry(cc) {
  if (!COUNTRIES[cc]) cc = "AT";
  state.country = cc;
  const conf = C();
  document.querySelectorAll("[data-country]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.country === cc)));
  $("#source").textContent = cc === "DE" ? "Deutscher Bundesbank" : "OeNB";
  $("#q").placeholder = conf.placeholder;
  $("#col5").textContent = conf.col5;
  document.querySelectorAll(".f-at").forEach((el) => (el.hidden = !conf.filters));
  document.querySelectorAll("a.dl").forEach((a) => (a.href = conf.csv));
  $("#meta").textContent = "lädt …";
  $("#rows").innerHTML = `<tr><td colspan="5" class="empty">lädt …</td></tr>`;
  $("#result-count").textContent = "";

  if (!state.data[cc]) {
    try {
      const [loaded, days] = await Promise.all([conf.load(), fetchText(`${conf.changes}index.json`).then(JSON.parse).catch(() => [])]);
      loaded.banks.sort((a, b) => a.blz.padStart(10, "0").localeCompare(b.blz.padStart(10, "0")));
      loaded.days = days;
      state.data[cc] = loaded;
      if (conf.filters) {
        const fill = (sel, key) => [...new Set(loaded.banks.map((b) => b[key]).filter(Boolean))].sort((a, b) => a.localeCompare(b, "de"))
          .forEach((v) => sel.insertAdjacentHTML("beforeend", `<option>${esc(v)}</option>`));
        fill($("#f-land"), "land");
        fill($("#f-sektor"), "sektor");
      }
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
  renderMeta();
  applyFilter();
  renderDays();
}

/* ---------- Tabs & Start ---------- */

function selectTab(name) {
  for (const t of ["suche", "aenderungen"]) {
    $(`#tab-${t}`).setAttribute("aria-selected", String(t === name));
    $(`#view-${t}`).hidden = t !== name;
  }
}

async function init() {
  $("#tab-suche").addEventListener("click", () => selectTab("suche"));
  $("#tab-aenderungen").addEventListener("click", () => selectTab("aenderungen"));
  document.querySelectorAll("[data-country]").forEach((b) => b.addEventListener("click", () => {
    if (b.dataset.country !== state.country) selectCountry(b.dataset.country);
  }));
  $("#q").addEventListener("input", applyFilter);
  $("#f-land").addEventListener("change", applyFilter);
  $("#f-sektor").addEventListener("change", applyFilter);
  $("#more-btn").addEventListener("click", () => renderMore());
  const openRow = (tr) => { const hit = state.filtered.find((x) => x.b.blz === tr.dataset.blz); if (hit) showDetail(hit.b, "", hit.branchHit); };
  $("#rows").addEventListener("click", (e) => { const tr = e.target.closest("tr[data-blz]"); if (tr) openRow(tr); });
  $("#rows").addEventListener("keydown", (e) => { const tr = e.target.closest("tr[data-blz]"); if (tr && e.key === "Enter") openRow(tr); });
  $("#detail").addEventListener("click", (e) => {
    if (e.target === $("#detail")) $("#detail").close();
    const btn = e.target.closest("[data-copy]");
    if (btn) navigator.clipboard?.writeText(btn.dataset.copy).then(() => { btn.textContent = "Kopiert"; setTimeout(() => (btn.textContent = "Kopieren"), 1200); });
    const link = e.target.closest("[data-open-blz]");
    if (link) { e.preventDefault(); const b = D().banks.find((x) => x.blz === link.dataset.openBlz); if (b) showDetail(b); }
  });

  const params = new URLSearchParams(location.hash.slice(1));
  if (params.get("q")) $("#q").value = params.get("q");
  fetchText("build.json").then((t) => { state.build = JSON.parse(t); renderMeta(); }).catch(() => {});
  await selectCountry((params.get("land") || "AT").toUpperCase());
}

init();
