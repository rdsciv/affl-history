#!/usr/bin/env python3
"""Prove the AFFL history book is a 2014–2025 archive built from real data."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
FAILS = []


def ok(cond, msg):
    if cond:
        print("  PASS", msg)
    else:
        FAILS.append(msg)
        print("  FAIL", msg)


def load_json(name):
    return json.loads((SITE / name).read_text())


def test_twelve_year_cards():
    print("twelve year cards, no 2026")
    hist = load_json("history.json")
    years = [y["year"] for y in hist["years"]]
    ok(years == list(range(2014, 2026)), f"history.json years == 2014–2025 ({years})")
    ok(2026 not in years, "history.json has no 2026")
    ok(len(hist["years"]) == 12, "exactly 12 year cards")

    index_html = (SITE / "index.html").read_text()
    ok('id="year-wall"' in index_html, "home has #year-wall")
    ok("2014–2025" in index_html or "2014-2025" in index_html or "2014–2025" in index_html, "home copy names 2014–2025")
    ok("2026" not in json.dumps(hist["years"]), "year card payload has no 2026")

    manifest = load_json("index_years.json")
    man_years = [y["year"] for y in manifest["years"]]
    ok(man_years == list(range(2014, 2026)), f"index_years.json is 2014–2025 ({man_years})")
    year_files = sorted(int(p.stem) for p in (SITE / "years").glob("*.json"))
    ok(year_files == list(range(2014, 2026)), f"site/years files are 2014–2025 ({year_files})")
    ok(not (SITE / "years" / "2026.json").exists(), "no years/2026.json")
    ok(not (SITE / "years" / "2013.json").exists(), "no years/2013.json")


def test_honors_present_and_real():
    print("champion / sacko / point-title present and match data.json")
    hist = load_json("history.json")
    data = load_json("data.json")
    alias = {"m01": "m07", "m03": "m08", "m20": "m10"}

    def canon(oid):
        return alias.get(oid, oid)

    for card in hist["years"]:
        year = card["year"]
        for key in ("champion", "runnerUp", "third", "sacko", "pointTitle"):
            h = card[key]
            ok(bool(h.get("currentName")), f"{year} {key} has currentName")
            ok(h.get("pf") not in (None, ""), f"{year} {key} has PF")
            ok(h.get("record"), f"{year} {key} has W-L")

        season = data["seasons"][str(year)]
        teams = season["teams"]
        by_id = {t["id"]: t for t in teams}
        champ = by_id[season["champion"]]
        sacko = max(teams, key=lambda t: t["finalRank"])
        point = max(teams, key=lambda t: t["pf"])
        ok(canon(champ["owner"]) == card["champion"]["owner"], f"{year} champion owner matches ESPN final")
        ok(canon(sacko["owner"]) == card["sacko"]["owner"], f"{year} sacko is last finalRank")
        ok(canon(point["owner"]) == card["pointTitle"]["owner"], f"{year} point title is max regular-season PF")
        ok(card["champion"]["pf"] == champ["pf"], f"{year} champion PF is not invented")


def test_logo_css_cap():
    print("logo CSS cap ≤ 28px")
    css = (SITE / "styles.css").read_text()
    block = css.split("Hard cap:")[-1]
    ok("max-width: 28px" in block and "max-height: 28px" in block, "hard-cap block sets max 28px")
    ok("object-fit: contain" in block, "hard-cap block uses object-fit contain")
    ok(".archive-mark" in block and ".tbl img" in block, "cap applies to archive marks and table imgs")
    ok(".sb-logo" in block, "scoreboard logos are capped")

    # No table/archive mark may declare a size above 28px.
    for sel in (".archive-mark", ".tbl img", ".tbl .mini", ".sb-logo"):
        for m in re.finditer(re.escape(sel) + r"[^{]*\{([^}]+)\}", css):
            body = m.group(1)
            for prop in ("width", "height", "max-width", "max-height"):
                for num in re.findall(rf"{prop}\s*:\s*(\d+)px", body):
                    ok(int(num) <= 28, f"{sel} {prop} {num}px ≤ 28")


def test_record_tables_still_there():
    print("existing record tables still there")
    rec = (SITE / "records.html").read_text()
    for table_id in (
        "franchise-tbl",
        "combined-tbl",
        "heatmap-tbl",
        "h2h-tbl",
        "timeline",
        "trophy-case",
        "ss-pf",
        "ss-wins",
    ):
        ok(f'id="{table_id}"' in rec, f"records.html has #{table_id}")
    js = (SITE / "history.js").read_text()
    ok("combinedTitles" in js, "combined titles renderer exists")
    ok("championships + seconds + thirds" in rec, "combined-title formula is documented")


def test_missing_data_stays_missing():
    print("2014–17 benches/transactions stay missing")
    for year in (2014, 2015, 2016, 2017):
        y = load_json(f"years/{year}.json")
        ok(y.get("hasRosters") is False, f"{year} hasRosters is false")
        ok(y.get("hasTx") is False, f"{year} hasTx is false")
        ok(y.get("players") == [], f"{year} players list is missing (empty), not invented")
        ok(y.get("moves") == [], f"{year} moves list is missing, not invented")
        ok(y.get("trades") == [], f"{year} trades list is missing, not invented")


def test_franchise_metadata():
    print("franchise status + Gabagooners have no invented history")
    hist = load_json("history.json")
    by_name = {f["currentName"]: f for f in hist["franchises"]}
    ok(by_name["Pasco Pounders"]["status"] == "historic", "Pounders historic")
    ok(by_name["Poulsbo Pollywogs"]["status"] == "historic", "Pollywogs historic")
    ok(by_name["Chula Vista Chupacabras"]["status"] == "current", "Chupacabras current")
    gab = hist["newFranchises"][0]
    ok(gab["name"] == "Gabagooners", "Gabagooners listed")
    ok(gab["seasons"] == 0, "Gabagooners has 0 seasons")
    ok("no 2014–2025 history" in gab["note"], "Gabagooners note is honest")


def test_pages_workflow():
    print("GitHub Pages deploy")
    docs = ROOT / "docs"
    ok((docs / "index.html").exists(), "docs/index.html exists for Pages")
    ok((docs / ".nojekyll").exists(), "docs/.nojekyll so Pages serves the SPA as-is")
    ok((docs / "history.json").exists(), "docs/history.json is published")
    year_files = sorted(int(p.stem) for p in (docs / "years").glob("*.json"))
    ok(year_files == list(range(2014, 2026)), f"docs/years is 2014–2025 ({year_files})")
    ok(not (docs / "years" / "2026.json").exists(), "docs has no 2026.json")
    yml = ROOT / ".github" / "workflows" / "pages.yml"
    if yml.exists():
        text = yml.read_text()
        ok("branches: [main]" in text, "Pages workflow (if present) deploys from main")


def main():
    print("AFFL history site evals")
    test_twelve_year_cards()
    test_honors_present_and_real()
    test_logo_css_cap()
    test_record_tables_still_there()
    test_missing_data_stays_missing()
    test_franchise_metadata()
    test_pages_workflow()
    print()
    if FAILS:
        print(f"{len(FAILS)} FAIL")
        for f in FAILS:
            print(" -", f)
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
