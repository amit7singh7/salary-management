import { html, useEffect, useState } from "./lib.js";
import { api, useFetch } from "./api.js";
import { count, money, usd, TYPE_LABEL } from "./format.js";
import { EmployeeModal } from "./employee-modal.js";

const PAGE_SIZE = 25;
const COLUMNS = [
  ["name", "Name"], ["job_title", "Job title"], ["department", "Department"],
  ["country", "Country"], [null, "Type"], ["salary", "Annual salary"], ["hire_date", "Hired"],
];

function Select({ label, value, onChange, options, allLabel }) {
  return html`<label class="filter">
    <span class="visually-hidden">${label}</span>
    <select value=${value} onChange=${(e) => onChange(e.target.value)} aria-label=${label}>
      <option value="">${allLabel}</option>
      ${options.map(([v, text]) => html`<option key=${v} value=${v}>${text}</option>`)}
    </select>
  </label>`;
}

export function EmployeesView({ meta, onMetaStale }) {
  const [search, setSearch] = useState("");
  const [filters, setFilters] = useState({ q: "", country: "", department: "", job_title: "", employment_type: "" });
  const [sort, setSort] = useState("name");
  const [order, setOrder] = useState("asc");
  const [page, setPage] = useState(1);
  const [version, setVersion] = useState(0);
  const [modal, setModal] = useState(null); // null | {id: number|null}

  // debounce typing so we don't query on every keystroke
  useEffect(() => {
    const t = setTimeout(() => { setFilters((f) => ({ ...f, q: search.trim() })); setPage(1); }, 250);
    return () => clearTimeout(t);
  }, [search]);

  const setFilter = (key) => (value) => { setFilters((f) => ({ ...f, [key]: value })); setPage(1); };
  const { data, error, loading } = useFetch(
    () => api.listEmployees({ ...filters, sort, order, page, page_size: PAGE_SIZE }),
    [filters, sort, order, page, version],
  );

  function toggleSort(col) {
    if (!col) return;
    if (col === sort) setOrder(order === "asc" ? "desc" : "asc");
    else { setSort(col); setOrder(col === "salary" || col === "hire_date" ? "desc" : "asc"); }
    setPage(1);
  }
  const changed = () => { setVersion((v) => v + 1); onMetaStale(); };
  const clear = () => { setSearch(""); setFilters({ q: "", country: "", department: "", job_title: "", employment_type: "" }); setPage(1); };
  const hasFilters = Object.values(filters).some(Boolean) || search;

  const total = data ? data.total : 0;
  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const from = total === 0 ? 0 : (page - 1) * PAGE_SIZE + 1;
  const to = Math.min(page * PAGE_SIZE, total);

  return html`<section aria-labelledby="emp-h">
    <div class="view-head">
      <div>
        <h1 id="emp-h">Employees</h1>
        <p class="muted">${data ? count(total) + (hasFilters ? " matching" : " in total") : "Loading…"}</p>
      </div>
      <button class="btn primary" onClick=${() => setModal({ id: null })}>Add employee</button>
    </div>

    <div class="toolbar">
      <input class="search" type="search" placeholder="Search by name or email" aria-label="Search by name or email"
             value=${search} onInput=${(e) => setSearch(e.target.value)} />
      <${Select} label="Country" allLabel="All countries" value=${filters.country} onChange=${setFilter("country")}
                 options=${meta.countries.map((c) => [c.name, c.name])} />
      <${Select} label="Department" allLabel="All departments" value=${filters.department} onChange=${setFilter("department")}
                 options=${meta.departments.map((d) => [d, d])} />
      <${Select} label="Job title" allLabel="All job titles" value=${filters.job_title} onChange=${setFilter("job_title")}
                 options=${meta.job_titles.map((t) => [t, t])} />
      <${Select} label="Employment type" allLabel="All types" value=${filters.employment_type} onChange=${setFilter("employment_type")}
                 options=${meta.employment_types.map((t) => [t, TYPE_LABEL[t]])} />
      ${hasFilters && html`<button class="btn link" onClick=${clear}>Clear filters</button>`}
    </div>

    ${error && html`<p class="banner error" role="alert">Couldn't load employees. Check that the server is running, then reload.</p>`}

    <div class="table-wrap ${loading ? "is-loading" : ""}">
      <table>
        <thead><tr>
          ${COLUMNS.map(([col, label]) => html`<th key=${label}
              aria-sort=${col === sort ? (order === "asc" ? "ascending" : "descending") : "none"}
              class=${col === "salary" ? "right" : ""}>
            ${col ? html`<button class="th-btn" onClick=${() => toggleSort(col)}>
                ${label}<span class="sort-mark" aria-hidden="true">${col === sort ? (order === "asc" ? "▲" : "▼") : ""}</span>
              </button>` : label}
          </th>`)}
        </tr></thead>
        <tbody>
          ${data && data.items.map((e) => html`<tr key=${e.id} class="row" tabIndex="0"
              onClick=${() => setModal({ id: e.id })}
              onKeyDown=${(ev) => ev.key === "Enter" && setModal({ id: e.id })}>
            <td><div class="strong">${e.name}</div><div class="muted small">${e.email}</div></td>
            <td>${e.job_title}</td>
            <td>${e.department}</td>
            <td>${e.country}</td>
            <td>${TYPE_LABEL[e.employment_type]}</td>
            <td class="right num">
              <div class="strong">${money(e.salary, e.currency)}</div>
              ${e.currency !== "USD" && html`<div class="muted small">≈ ${usd(e.salary_usd)}</div>`}
            </td>
            <td class="num">${e.hire_date}</td>
          </tr>`)}
          ${data && data.items.length === 0 && html`<tr><td colspan="7" class="empty">
            No employees match these filters. <button class="btn link" onClick=${clear}>Clear filters</button>
          </td></tr>`}
        </tbody>
      </table>
    </div>

    <nav class="pager" aria-label="Pagination">
      <span class="muted">${total ? `${count(from)}–${count(to)} of ${count(total)}` : ""}</span>
      <span class="spacer"></span>
      <button class="btn" disabled=${page <= 1} onClick=${() => setPage(page - 1)}>Previous</button>
      <span class="muted">Page ${count(page)} of ${count(pages)}</span>
      <button class="btn" disabled=${page >= pages} onClick=${() => setPage(page + 1)}>Next</button>
    </nav>

    ${modal && html`<${EmployeeModal} id=${modal.id} meta=${meta} onClose=${() => setModal(null)} onChanged=${changed} />`}
  </section>`;
}
