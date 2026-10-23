import { html, useCallback, useEffect, useState } from "./lib.js";
import { api, useFetch } from "./api.js";
import { EmployeesView } from "./employees.js";
import { InsightsView } from "./insights.js";

const TABS = [["employees", "Employees"], ["insights", "Pay insights"]];
const tabFromHash = () => (location.hash === "#insights" ? "insights" : "employees");

function App() {
  const [tab, setTab] = useState(tabFromHash());
  const [metaVersion, setMetaVersion] = useState(0);
  const meta = useFetch(() => api.meta(), [metaVersion]);
  const staleMeta = useCallback(() => setMetaVersion((v) => v + 1), []);

  useEffect(() => {
    const onHash = () => setTab(tabFromHash());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  return html`<div class="app">
    <header class="topbar">
      <div class="brand">Salary Management<span class="brand-sub">ACME</span></div>
      <nav aria-label="Main">
        ${TABS.map(([id, label]) => html`<a key=${id} href=${"#" + id} class=${tab === id ? "on" : ""}
            aria-current=${tab === id ? "page" : undefined}>${label}</a>`)}
      </nav>
    </header>
    <main>
      ${meta.error && html`<p class="banner error" role="alert">Couldn't reach the server. Start the backend and reload.</p>`}
      ${!meta.data && meta.loading && html`<p class="muted pad">Loading…</p>`}
      ${meta.data && (tab === "insights"
        ? html`<${InsightsView} meta=${meta.data} />`
        : html`<${EmployeesView} meta=${meta.data} onMetaStale=${staleMeta} />`)}
    </main>
  </div>`;
}

ReactDOM.createRoot(document.getElementById("root")).render(html`<${App} />`);
