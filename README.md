# Salary Management

Web app for an HR manager to manage salary data for ~10,000 employees across countries and answer
"how do we pay people?" — see [`docs/requirements.md`](docs/requirements.md) for scope.

**Stack:** Python 3.9+ · Flask · SQLite · React 18 (+ htm, no build step) · unittest

## Run locally
```bash
cd backend
pip install -r requirements.txt
python seed.py          # 10,000 deterministic employees (use --reset to reseed, -n to change count)
python run.py           # http://localhost:8000  (API under /api, UI at /)
```
Or with Docker (self-seeds on first boot):
```bash
docker build -t salary-mgmt . && docker run -p 8000:8000 -v salary-data:/data salary-mgmt
```
The UI loads React, htm and fonts from CDNs (pinned versions), so the browser needs internet access.

## Test & benchmark
```bash
make test      # (use `python3 -m unittest discover -s . -t . -p "test_*.py"` from backend/ if `python` is not found) 50 fast, deterministic tests (~0.5s)
make bench     # latency of each endpoint on the seeded DB
```

## Features
- **Employees:** add / edit / delete, search (name, email), filter (country, department, job title, type), sortable columns, pagination, salary history per person.
- **Pay insights:** headcount, payroll, median/average; pay by country / department / job title / employment type shown as min–max, P25–P75 and median on a shared USD axis; salary distribution histogram; all filterable.

## API
| Method & path | Purpose |
|---|---|
| `GET /api/employees?q&country&department&job_title&employment_type&sort&order&page&page_size` | list (paginated) |
| `POST /api/employees` · `GET/PUT/DELETE /api/employees/<id>` | CRUD (GET includes `history`) |
| `GET /api/insights?group_by=country\|department\|job_title\|employment_type&<filters>` | pay statistics per group |
| `GET /api/insights/distribution?<filters>` · `GET /api/summary?<filters>` | histogram · totals |
| `GET /api/meta` | countries/currencies and filter options |

Errors: `422 {error:"validation_failed", fields:{field:message}}`, `404`, `400` (bad `group_by`).

## Layout
```
backend/app/   api.py · validation.py · repository.py · insights.py · currency.py · db.py
backend/       seed.py · benchmark.py · run.py · tests/
frontend/      index.html · styles.css · js/ (app, employees, employee-modal, insights, api, format)
docs/          requirements.md · design-notes.md · ai-usage.md
```

## Pre-submission checklist
- [ ] Click through the UI once (add, edit salary, delete, filters, both insight tabs)
- [ ] Deploy (Dockerfile works on Render / Fly.io / Railway) and put the URL here
- [ ] Record the short demo video
- [ ] Update `docs/ai-usage.md` with your own real prompts
