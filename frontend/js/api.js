import { useEffect, useState } from "./lib.js";

async function request(path, options = {}) {
  const res = await fetch("/api" + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (res.status === 204) return null;
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    const err = new Error((body && body.error) || "request_failed");
    err.status = res.status;
    err.fields = (body && body.fields) || {};
    throw err;
  }
  return body;
}

export function qs(params) {
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) if (v !== "" && v != null) p.set(k, v);
  const s = p.toString();
  return s ? "?" + s : "";
}

const send = (method) => (path, data) => request(path, { method, body: JSON.stringify(data) });

export const api = {
  meta: () => request("/meta"),
  listEmployees: (p) => request("/employees" + qs(p)),
  getEmployee: (id) => request(`/employees/${id}`),
  createEmployee: (d) => send("POST")("/employees", d),
  updateEmployee: (id, d) => send("PUT")(`/employees/${id}`, d),
  deleteEmployee: (id) => request(`/employees/${id}`, { method: "DELETE" }),
  insights: (p) => request("/insights" + qs(p)),
  distribution: (p) => request("/insights/distribution" + qs(p)),
  summary: (p) => request("/summary" + qs(p)),
};

/** Fetch on dependency change. Keeps the previous data visible while reloading and
 *  ignores responses from outdated requests (no out-of-order flicker). */
export function useFetch(fn, deps) {
  const [state, setState] = useState({ data: null, error: null, loading: true });
  useEffect(() => {
    let cancelled = false;
    setState((s) => ({ ...s, loading: true, error: null }));
    fn()
      .then((data) => !cancelled && setState({ data, error: null, loading: false }))
      .catch((error) => !cancelled && setState({ data: null, error, loading: false }));
    return () => { cancelled = true; };
  }, deps);
  return state;
}
