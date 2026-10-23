import { html, useMemo, useState } from "./lib.js";
import { api, useFetch } from "./api.js";
import { compact, count, groupName, GROUP_LABEL, money, TYPE_LABEL, usd } from "./format.js";

const GROUPS = ["country", "department", "job_title", "employment_type"];

/** Round an axis maximum up to a "nice" number (1, 2, 2.5, 5 × 10^n). */
export function niceMax(value) {
  if (value <= 0) return 1;
  const exp = Math.pow(10, Math.floor(Math.log10(value)));
  const f = value / exp;
  const nice = f <= 1 ? 1 : f <= 2 ? 2 : f <= 2.5 ? 2.5 : f <= 5 ? 5 : 10;
  return nice * exp;
}

function Stat({ label, value, hint }) {
  return html`<div class="stat">
    <div class="stat-value num">${value}</div>
    <div class="stat-label">${label}</div>
    ${hint && html`<div class="muted small">${hint}</div>`}
  </div>`;
}

function Strip({ g, axisMax }) {
  const pct = (v) => `${Math.min(100, (v / axisMax) * 100)}%`;
  const desc = `Median ${usd(g.median)}. Middle half of employees earn ${usd(g.p25)} to ${usd(g.p75)}. Full range ${usd(g.min)} to ${usd(g.max)}.`;
  return html`<div class="strip" role="img" aria-label=${desc} title=${desc}>
    <span class="whisker" style=${{ left: pct(g.min), width: `calc(${pct(g.max)} - ${pct(g.min)})` }}></span>
    <span class="iqr" style=${{ left: pct(g.p25), width: `calc(${pct(g.p75)} - ${pct(g.p25)})` }}></span>
    <span class="median" style=${{ left: pct(g.median) }}></span>
  </div>`;
}

function RangeChart({ groups, field }) {
  const axisMax = useMemo(() => niceMax(Math.max(...groups.map((g) => g.max))), [groups]);
  const ticks = [0, 0.25, 0.5, 0.75, 1].map((t) => t * axisMax);
  return html`<div class="range-chart">
    <div class="range-legend muted small">
      <span><i class="key whisker-key"></i>Lowest to highest</span>
      <span><i class="key iqr-key"></i>Middle 50% (P25–P75)</span>
      <span><i class="key median-key"></i>Median</span>
      <span>All values are annual, converted to USD.</span>
    </div>
    <div class="range-row range-axis" aria-hidden="true">
      <span></span><span></span>
      <div class="axis">${ticks.map((t, i) => html`<span key=${i} style=${{ left: `${(t / axisMax) * 100}%` }}>${"$" + compact(t)}</span>`)}</div>
      <span></span>
    </div>
    ${groups.map((g) => html`<div class="range-row" key=${g.group}>
      <div class="range-name">${groupName(field, g.group)}</div>
      <div class="num muted small right">${count(g.headcount)}</div>
      <${Strip} g=${g} axisMax=${axisMax} />
      <div class="range-median num right">
        <div class="strong">${usd(g.median)}</div>
        ${g.local && g.currency !== "USD" && html`<div class="muted small">${money(g.local.median, g.currency)}</div>`}
      </div>
    </div>`)}
  </div>`;
}

function Histogram({ buckets }) {
  const max = Math.max(1, ...buckets.map((b) => b.count));
  const name = (b) => (b.to == null ? `$${compact(b.from)}+` : `$${compact(b.from)}–${compact(b.to)}`);
  return html`<div class="histogram" role="list">
    ${buckets.map((b) => html`<div class="hist-col" role="listitem" key=${b.from}
        title=${`${name(b)}: ${count(b.count)} employees`}>
      <span class="hist-count num small">${b.count ? count(b.count) : ""}</span>
      <span class="hist-bar" style=${{ height: `${(b.count / max) * 100}%` }}></span>
      <span class="hist-label small muted">${name(b)}</span>
    </div>`)}
  </div>`;
}

export function InsightsView({ meta }) {
  const [groupBy, setGroupBy] = useState("country");
  const [filters, setFilters] = useState({ country: "", department: "", employment_type: "" });
  const setFilter = (k) => (e) => setFilters((f) => ({ ...f, [k]: e.target.value }));
  const active = Object.values(filters).some(Boolean);

  const summary = useFetch(() => api.summary(filters), [filters]);
  const stats = useFetch(() => api.insights({ group_by: groupBy, ...filters }), [groupBy, filters]);
  const dist = useFetch(() => api.distribution(filters), [filters]);

  const s = summary.data;
  return html`<section aria-labelledby="ins-h">
    <div class="view-head">
      <div>
        <h1 id="ins-h">Pay insights</h1>
        <p class="muted">How ACME pays people, normalised to USD so countries can be compared.</p>
      </div>
    </div>

    <div class="toolbar">
      <label class="filter"><span class="visually-hidden">Country</span>
        <select aria-label="Country" value=${filters.country} onChange=${setFilter("country")}>
          <option value="">All countries</option>
          ${meta.countries.map((c) => html`<option key=${c.name} value=${c.name}>${c.name}</option>`)}
        </select></label>
      <label class="filter"><span class="visually-hidden">Department</span>
        <select aria-label="Department" value=${filters.department} onChange=${setFilter("department")}>
          <option value="">All departments</option>
          ${meta.departments.map((d) => html`<option key=${d} value=${d}>${d}</option>`)}
        </select></label>
      <label class="filter"><span class="visually-hidden">Employment type</span>
        <select aria-label="Employment type" value=${filters.employment_type} onChange=${setFilter("employment_type")}>
          <option value="">All types</option>
          ${meta.employment_types.map((t) => html`<option key=${t} value=${t}>${TYPE_LABEL[t]}</option>`)}
        </select></label>
      ${active && html`<button class="btn link" onClick=${() => setFilters({ country: "", department: "", employment_type: "" })}>Clear filters</button>`}
    </div>

    <div class="stats">
      <${Stat} label="Employees" value=${s ? count(s.headcount) : "–"} />
      <${Stat} label="Annual payroll" value=${s ? usd(s.total_payroll_usd) : "–"} />
      <${Stat} label="Median salary" value=${s && s.headcount ? usd(s.median) : "–"} />
      <${Stat} label="Average salary" value=${s && s.headcount ? usd(s.average) : "–"} />
    </div>

    <div class="panel">
      <div class="panel-head">
        <h2>Pay by</h2>
        <div class="segmented" role="group" aria-label="Group pay by">
          ${GROUPS.map((g) => html`<button key=${g} class=${g === groupBy ? "on" : ""} aria-pressed=${g === groupBy}
              onClick=${() => setGroupBy(g)}>${GROUP_LABEL[g]}</button>`)}
        </div>
      </div>
      ${stats.error && html`<p class="banner error" role="alert">Couldn't load insights.</p>`}
      ${stats.data && stats.data.groups.length === 0 && html`<p class="empty">No employees match these filters.</p>`}
      ${stats.data && stats.data.groups.length > 0 && html`<${RangeChart} groups=${stats.data.groups} field=${stats.data.group_by} />`}
      ${!stats.data && stats.loading && html`<p class="muted pad">Loading…</p>`}
    </div>

    <div class="panel">
      <div class="panel-head"><h2>Salary distribution</h2><span class="muted small">Employees per USD salary band</span></div>
      ${dist.data && html`<${Histogram} buckets=${dist.data.buckets} />`}
      ${!dist.data && dist.loading && html`<p class="muted pad">Loading…</p>`}
    </div>
  </section>`;
}
