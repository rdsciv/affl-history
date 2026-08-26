#!/usr/bin/env python3
"""Derive AFFL history book JSON from site/data.json.

Honors and records are computed from ESPN-backed season standings in
data.json. Nothing is invented: 2014–17 benches/transactions stay absent,
and a 2026 season is never emitted.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "site" / "data.json"
OUT_PATH = ROOT / "site" / "history.json"

HISTORY_YEARS = list(range(2014, 2026))
# Same person, different ESPN member GUIDs across seasons.
OWNER_ALIAS = {
    "m01": "m07",  # Jason Kafka / Chupacabras
    "m03": "m08",  # Kevin Sliger / Gringos
    "m20": "m10",  # Tanner Dunn / Wake Snakes
}
# 2026 planning metadata only — no invented W-L / PF.
HISTORIC_OWNERS = {"m19", "m14"}  # Pounders, Pollywogs
CURRENT_EXTRA = {"m07"}  # Chupacabras returning
NEW_FRANCHISES = [
    {
        "id": "new-gabagooners",
        "name": "Gabagooners",
        "status": "new",
        "seasons": 0,
        "note": "New franchise — no 2014–2025 history",
    }
]


def canon_owner(oid: str) -> str:
    return OWNER_ALIAS.get(oid, oid)


def wl(team: dict) -> str:
    w, l, t = team["wins"], team["losses"], team.get("ties") or 0
    return f"{w}-{l}-{t}" if t else f"{w}-{l}"


def latest_logo(seasons: dict, owner: str) -> str:
    logo = ""
    for year in HISTORY_YEARS:
        season = seasons.get(str(year))
        if not season:
            continue
        for team in season["teams"]:
            if canon_owner(team["owner"]) == owner and team.get("logo"):
                logo = team["logo"]
    return logo


def build() -> dict:
    data = json.loads(DATA_PATH.read_text())
    seasons = data["seasons"]
    members = data["members"]
    franchise_by_owner = {f["owner"]: f for f in data["franchises"]}

    years = []
    finish_rows = {}  # owner -> {year: finish}
    honors_by_owner = {}

    def bucket(owner: str) -> dict:
        return honors_by_owner.setdefault(
            owner,
            {"championships": 0, "seconds": 0, "thirds": 0, "pointTitles": 0, "sackos": 0},
        )

    for year in HISTORY_YEARS:
        season = seasons[str(year)]
        teams = list(season["teams"])
        by_id = {t["id"]: t for t in teams}
        champ = by_id[season["champion"]]
        runner = by_id[season["runnerUp"]]
        third = next(t for t in teams if t["finalRank"] == 3)
        sacko = max(teams, key=lambda t: t["finalRank"])
        point = max(teams, key=lambda t: t["pf"])

        def honor(team: dict, kind: str) -> dict:
            owner = canon_owner(team["owner"])
            fr = franchise_by_owner.get(owner, {})
            return {
                "kind": kind,
                "teamId": team["id"],
                "owner": owner,
                "seasonName": team["name"],
                "currentName": fr.get("currentName") or team["name"],
                "ownerName": fr.get("ownerName") or members.get(team["owner"], ""),
                "record": wl(team),
                "pf": team["pf"],
                "finalRank": team["finalRank"],
                "logo": team.get("logo") or "",
            }

        card = {
            "year": year,
            "champion": honor(champ, "champion"),
            "runnerUp": honor(runner, "runnerUp"),
            "third": honor(third, "third"),
            "sacko": honor(sacko, "sacko"),
            "pointTitle": honor(point, "pointTitle"),
            "teamCount": len(teams),
            "totalPts": season.get("totalPts"),
        }
        years.append(card)

        bucket(canon_owner(champ["owner"]))["championships"] += 1
        bucket(canon_owner(runner["owner"]))["seconds"] += 1
        bucket(canon_owner(third["owner"]))["thirds"] += 1
        bucket(canon_owner(point["owner"]))["pointTitles"] += 1
        bucket(canon_owner(sacko["owner"]))["sackos"] += 1

        for team in teams:
            owner = canon_owner(team["owner"])
            finish_rows.setdefault(owner, {})[str(year)] = team["finalRank"]

    # 2025 active set, minus historic leavers, plus Chupacabras.
    active_2025 = set(data["activeOwners"])
    current_owners = (active_2025 - HISTORIC_OWNERS) | CURRENT_EXTRA

    franchises = []
    for fr in data["franchises"]:
        owner = fr["owner"]
        h = honors_by_owner.get(owner, {"championships": 0, "seconds": 0, "thirds": 0, "pointTitles": 0, "sackos": 0})
        combined = h["championships"] + h["seconds"] + h["thirds"] + h["pointTitles"] - h["sackos"]
        if owner in HISTORIC_OWNERS:
            status = "historic"
        elif owner in current_owners:
            status = "current"
        else:
            status = "historic"
        franchises.append(
            {
                "owner": owner,
                "ownerName": fr["ownerName"],
                "currentName": fr["currentName"],
                "seasons": fr["seasons"],
                "years": fr["years"],
                "wins": fr["wins"],
                "losses": fr["losses"],
                "ties": fr.get("ties") or 0,
                "pf": fr["pf"],
                "pa": fr["pa"],
                "winPct": fr["winPct"],
                "titles": fr["titles"],
                "runnerUps": fr["runnerUps"],
                "playoffs": fr["playoffs"],
                "bestFinish": fr["bestFinish"],
                "lastSacko": fr.get("lastSacko"),
                "pfBySeason": fr["pfBySeason"],
                "logo": latest_logo(seasons, owner),
                "status": status,
                "championships": h["championships"],
                "seconds": h["seconds"],
                "thirds": h["thirds"],
                "pointTitles": h["pointTitles"],
                "sackos": h["sackos"],
                "combinedTitles": combined,
                "finishes": finish_rows.get(owner, {}),
            }
        )

    franchises.sort(key=lambda f: (-f["combinedTitles"], -f["championships"], -f["winPct"]))

    # Single-season records from regular-season standings only.
    season_rows = []
    for year in HISTORY_YEARS:
        season = seasons[str(year)]
        for team in season["teams"]:
            owner = canon_owner(team["owner"])
            fr = franchise_by_owner.get(owner, {})
            season_rows.append(
                {
                    "year": year,
                    "owner": owner,
                    "seasonName": team["name"],
                    "currentName": fr.get("currentName") or team["name"],
                    "ownerName": fr.get("ownerName") or members.get(team["owner"], ""),
                    "wins": team["wins"],
                    "losses": team["losses"],
                    "ties": team.get("ties") or 0,
                    "record": wl(team),
                    "pf": team["pf"],
                    "pa": team["pa"],
                    "avgPts": team["avgPts"],
                    "finalRank": team["finalRank"],
                    "logo": team.get("logo") or "",
                }
            )

    def top(key, reverse=True, n=8):
        return sorted(season_rows, key=lambda r: (r[key], r["wins"]), reverse=reverse)[:n]

    records = {
        "highestPf": top("pf"),
        "lowestPf": top("pf", reverse=False),
        "mostWins": top("wins"),
        "mostLosses": top("losses"),
        "bestAvg": top("avgPts"),
        "worstAvg": top("avgPts", reverse=False),
    }

    timeline = []
    for y in years:
        c = y["champion"]
        timeline.append(
            {
                "year": y["year"],
                "currentName": c["currentName"],
                "seasonName": c["seasonName"],
                "ownerName": c["ownerName"],
                "record": c["record"],
                "pf": c["pf"],
                "logo": c["logo"],
                "owner": c["owner"],
            }
        )

    out = {
        "league": "AFFL",
        "espnLeagueId": 51418,
        "scoring": "non-PPR",
        "firstYear": 2014,
        "lastYear": 2025,
        "years": years,
        "franchises": franchises,
        "newFranchises": NEW_FRANCHISES,
        "records": records,
        "timeline": timeline,
        "h2h": data["h2h"],
        "members": members,
        "source": "rdsciv/affl-analytics verify/full-audit site/data.json",
    }
    OUT_PATH.write_text(json.dumps(out, indent=2) + "\n")
    return out


if __name__ == "__main__":
    built = build()
    print(f"wrote {OUT_PATH} ({len(built['years'])} years, {len(built['franchises'])} franchises)")
    print("2014 champion:", built["years"][0]["champion"]["seasonName"], "/", built["years"][0]["champion"]["currentName"])
    print("2025 champion:", built["years"][-1]["champion"]["seasonName"], "/", built["years"][-1]["champion"]["currentName"])
