# Salary Management — Requirements (one page)

**User:** the HR Manager of ACME (single persona).
**Problem:** Salary data for ~10,000 employees across many countries lives in Excel files. It is tedious to maintain and hard to answer "how do we pay people?"

## Goal
Replace the spreadsheets with a web app where the HR Manager can (1) keep employee salary records accurate and (2) answer pay questions in seconds.

## In scope
| # | Feature | Why |
|---|---------|-----|
| 1 | Employee CRUD: name, email, job title, department, country, employment type, annual salary + currency, hire date | Replaces the spreadsheet as the source of truth |
| 2 | Search, filter (country, department, job title, type), sort and **server-side pagination** | 10k rows: must stay fast and usable |
| 3 | **Pay insights**: headcount, min / P25 / median / P75 / max / average, grouped by country, department, job title or employment type, with filters | The "how do we pay people" questions |
| 4 | Company summary: headcount, total annual payroll (USD), countries, departments | At-a-glance health |
| 5 | Salary history: every salary change is recorded with date and previous value | HR must be able to explain *why* someone earns what they do |
| 6 | Multi-currency: salary stored in local currency; insights normalised to USD with a fixed FX table | Employees are in multiple countries; mixing currencies would be wrong |
| 7 | Seed script generating 10,000 realistic employees (deterministic) | Demo and performance testing |

## Deliberately left out (and why)
- **Authentication / roles** — one persona; auth is orthogonal to the decisions being assessed. Would be the first addition before real use (salary data is sensitive).
- **Bonus, equity, allowances, total compensation** — base salary answers the stated problem; extra pay types multiply the data model.
- **Gender / demographic pay-equity analysis** — valuable, but requires collecting sensitive data and legal review. Left to a later phase.
- **Live FX rates** — rates are a small, editable table; a live feed adds an external dependency and non-deterministic numbers.
- **Excel import/export, approval workflows, payroll runs** — adjacent products, not the stated problem.
- **Bulk edit** — single-record edit is enough for v1; revisit if HR requests it.

## Key assumptions
- Salary is **annual gross base pay**. Currency is implied by country (one currency per country).
- Email is unique per employee. Deleting an employee is a hard delete (history removed with them).
- Insights use USD-normalised values so countries are comparable; local-currency figures are shown on single-country views.

## Success criteria
- List, search and insight queries over 10,000 rows respond well under 200 ms locally.
- Core logic covered by fast, deterministic unit/API tests.
- App runs with one command and ships a container for deployment.
