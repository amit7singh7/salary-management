import { html, useEffect, useRef, useState } from "./lib.js";
import { api, useFetch } from "./api.js";
import { money, usd } from "./format.js";

const EMPTY = {
  name: "", email: "", job_title: "", department: "", country: "",
  employment_type: "full_time", salary: "", hire_date: "",
};

function Field({ label, error, children }) {
  return html`<label class="field ${error ? "has-error" : ""}">
    <span class="field-label">${label}</span>
    ${children}
    ${error && html`<span class="field-error" role="alert">${error}</span>`}
  </label>`;
}

function History({ rows }) {
  return html`<section class="history" aria-label="Salary history">
    <h3>Salary history</h3>
    <ul>
      ${rows.map((h, i) => html`<li key=${i}>
        <span class="num">${money(h.salary, h.currency)}</span>
        <span class="muted">from ${h.effective_date}${h.note && h.note !== "Starting salary" ? " · " + h.note : ""}${h.note === "Starting salary" ? " · starting salary" : ""}</span>
      </li>`)}
    </ul>
  </section>`;
}

/** Create (id == null) or edit (id set) an employee. */
export function EmployeeModal({ id, meta, onClose, onChanged }) {
  const isEdit = id != null;
  const loaded = useFetch(() => (isEdit ? api.getEmployee(id) : Promise.resolve(null)), [id]);
  const [form, setForm] = useState(EMPTY);
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState("");
  const [saving, setSaving] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const firstField = useRef(null);

  useEffect(() => {
    if (loaded.data) {
      const { history, salary_usd, ...rest } = loaded.data;
      setForm({ ...EMPTY, ...rest, salary: String(rest.salary) });
    }
  }, [loaded.data]);

  useEffect(() => {
    const onKey = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  useEffect(() => { firstField.current && firstField.current.focus(); }, [loaded.loading]);

  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));
  const currency = (meta.countries.find((c) => c.name === form.country) || {}).currency;

  async function submit(e) {
    e.preventDefault();
    setSaving(true); setErrors({}); setFormError("");
    const payload = { ...form, salary: form.salary.trim() === "" ? null : Number(form.salary.replace(/,/g, "")) };
    try {
      if (isEdit) await api.updateEmployee(id, payload); else await api.createEmployee(payload);
      onChanged();
      onClose();
    } catch (err) {
      if (err.status === 422) setErrors(err.fields);
      else setFormError("Couldn't save. Check your connection and try again.");
    } finally { setSaving(false); }
  }

  async function remove() {
    setSaving(true);
    try { await api.deleteEmployee(id); onChanged(); onClose(); }
    catch { setFormError("Couldn't delete this employee. Try again."); setSaving(false); }
  }

  const title = isEdit ? "Edit employee" : "Add employee";
  return html`<div class="overlay" onMouseDown=${(e) => e.target === e.currentTarget && onClose()}>
    <div class="modal" role="dialog" aria-modal="true" aria-label=${title}>
      <header class="modal-head">
        <h2>${title}</h2>
        <button class="icon-btn" onClick=${onClose} aria-label="Close">✕</button>
      </header>
      ${isEdit && loaded.loading && !loaded.data && html`<p class="muted pad">Loading…</p>`}
      ${isEdit && loaded.error && html`<p class="banner error">Couldn't load this employee.</p>`}
      ${(!isEdit || loaded.data) && html`
      <form onSubmit=${submit} noValidate>
        <div class="grid-2">
          <${Field} label="Full name" error=${errors.name}>
            <input ref=${firstField} value=${form.name} onInput=${set("name")} maxLength="100" autoComplete="off" />
          <//>
          <${Field} label="Email" error=${errors.email}>
            <input type="email" value=${form.email} onInput=${set("email")} autoComplete="off" />
          <//>
          <${Field} label="Job title" error=${errors.job_title}>
            <input list="titles" value=${form.job_title} onInput=${set("job_title")} maxLength="100" />
            <datalist id="titles">${meta.job_titles.map((t) => html`<option key=${t} value=${t} />`)}</datalist>
          <//>
          <${Field} label="Department" error=${errors.department}>
            <input list="depts" value=${form.department} onInput=${set("department")} maxLength="100" />
            <datalist id="depts">${meta.departments.map((d) => html`<option key=${d} value=${d} />`)}</datalist>
          <//>
          <${Field} label="Country" error=${errors.country}>
            <select value=${form.country} onChange=${set("country")}>
              <option value="">Select a country</option>
              ${meta.countries.map((c) => html`<option key=${c.name} value=${c.name}>${c.name}</option>`)}
            </select>
          <//>
          <${Field} label="Employment type" error=${errors.employment_type}>
            <select value=${form.employment_type} onChange=${set("employment_type")}>
              <option value="full_time">Full-time</option>
              <option value="part_time">Part-time</option>
              <option value="contract">Contract</option>
            </select>
          <//>
          <${Field} label=${"Annual salary" + (currency ? ` (${currency})` : "")} error=${errors.salary}>
            <input inputmode="numeric" value=${form.salary} onInput=${set("salary")} placeholder="e.g. 85000" />
          <//>
          <${Field} label="Hire date" error=${errors.hire_date}>
            <input type="date" value=${form.hire_date} onInput=${set("hire_date")} />
          <//>
        </div>
        ${formError && html`<p class="banner error" role="alert">${formError}</p>`}
        ${isEdit && loaded.data && html`<${History} rows=${loaded.data.history} />`}
        <footer class="modal-foot">
          ${isEdit && !confirmDelete && html`<button type="button" class="btn danger-ghost" onClick=${() => setConfirmDelete(true)}>Delete employee</button>`}
          ${isEdit && confirmDelete && html`<span class="confirm">
            Delete ${form.name}? This also removes their salary history.
            <button type="button" class="btn danger" disabled=${saving} onClick=${remove}>Yes, delete</button>
            <button type="button" class="btn" onClick=${() => setConfirmDelete(false)}>Keep</button>
          </span>`}
          <span class="spacer"></span>
          <button type="button" class="btn" onClick=${onClose}>Cancel</button>
          <button type="submit" class="btn primary" disabled=${saving}>${saving ? "Saving…" : isEdit ? "Save changes" : "Add employee"}</button>
        </footer>
      </form>`}
    </div>
  </div>`;
}
