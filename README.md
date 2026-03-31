# analytics-vms

**Type:** Script (+ optional minimal web report)

## What it is
Script-first pipeline that ingests VMS data and generates a final report (HTML/PDF/CSV). Optional tiny front just to view/print the report.

## MVP
- [ ] Input format defined (CSV/JSON/DB export)
- [ ] Generate `report.html` (and/or CSV)
- [ ] Basic KPIs + summary
- [ ] Reproducible run instructions

## Output
- `out/report.html`
- `out/summary.csv`

## Notes
No secrets in repo (.env, keys).
