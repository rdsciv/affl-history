# AFFL History

The AFFL history book — ESPN league **51418**, **non-PPR**, seasons **2014–2025** only.

This repo is a standalone archive forked from [rdsciv/affl-analytics](https://github.com/rdsciv/affl-analytics). It is not a card on the live analytics History page.

**Pages (when enabled):** https://rdsciv.github.io/affl-history/

## What is here

Home is the year wall. Each 2014–2025 card shows champion, runner-up, third, sacko, and regular-season point title, with W-L and PF, using **current franchise names**.

Click a year for that season’s standings plus links to draft, awards, and teams. Franchise pages, combined titles, the finishes heatmap, trophy case, H2H ledger, single-season records, and the champions timeline live on Records / Teams / Awards.

- Pounders and Pollywogs are historic.
- Chupacabras is current.
- Gabagooners is new and has **no** 2014–2025 history.
- There is no AFFL 2026 season on this site before the draft.
- 2014–17 weekly benches and transactions are missing in the ESPN extract. Missing stays missing — never zero, never “not rostered.”

Stats are copied from `rdsciv/affl-analytics` (`verify/full-audit` year JSON, which is the richest site payload). Nothing is invented.

## Local preview

```bash
python3 scripts/build_history.py          # rebuild site/history.json from site/data.json
python3 evals/test_history_site.py        # archive / honors / logo-cap / record-table gates
python3 -m http.server 8788 --directory site
```

Then open http://localhost:8788/

## GitHub Pages

Same workflow as affl-analytics: push `main`, deploy the `site/` folder via `.github/workflows/pages.yml`.

## Source

Year bundles, logos (chrome-burst header mark + footer banner), and standings JSON come from affl-analytics. Table and archive logos are hard-capped at **28px** with `object-fit: contain`.
