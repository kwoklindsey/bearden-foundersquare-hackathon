"""BearDen overnight agent: works while the student sleeps.

11 PM  Watch: pull new listings from the feed (demo: sample_listings.json;
       later: Berkeley off-campus housing portal, Craigslist, FB groups).
2 AM   Screen: red-flag rules + shared Cognee memory (seen this contact before?).
8 AM   Act: queue Fo outreach for listings that pass, at a polite hour.
9 AM   Brief: morning summary for the student.
"""
import json
import re
from pathlib import Path

import memory
from fo_tasks import build_fo_task

FEED = Path(__file__).with_name("sample_listings.json")

RED_FLAG_RULES = [
    (r"zelle|wire|western union|venmo|cash ?app|gift card", "Asks for payment by Zelle/wire/app"),
    (r"overseas|out of the country|abroad|missionary|deployed", "Landlord says they're away and can't show it"),
    (r"no (in[- ]person )?(tour|showing|viewing)s?|can'?t show", "No in-person tour"),
    (r"deposit (first|before)|hold (it|the unit) with|send .*deposit", "Wants money before a lease or tour"),
    (r"urgent|many people interested|first come", "Pressure to act fast"),
]


def time_ago(ts: str) -> str:
    from datetime import datetime
    try:
        mins = int((datetime.now() - datetime.strptime(ts, "%Y-%m-%d %H:%M")).total_seconds() // 60)
    except Exception:
        return "recently"
    if mins < 1:
        return "just now"
    if mins < 60:
        return f"{mins} min ago"
    return f"{mins // 60} hr ago"


def money_at_risk(listing: dict) -> int:
    """Largest dollar amount the 'landlord' asks for up front (deposit/hold)."""
    text = f"{listing.get('title','')} {listing.get('description','')}"
    upfront = []
    for m in re.finditer(r"\$\s?(\d[\d,]{2,})", text):
        window = text[max(0, m.start() - 30): m.end() + 30]
        if re.search(r"deposit|hold|zelle|wire", window, re.I):
            upfront.append(int(m.group(1).replace(",", "")))
    rent = _rent_value(listing.get("rent", ""))
    return max(upfront) if upfront else rent


def load_feed() -> list[dict]:
    return json.loads(FEED.read_text())


def _rent_value(rent: str) -> int:
    digits = re.sub(r"[^\d]", "", rent or "")
    return int(digits) if digits else 0


def screen(listing: dict, student_budget: int) -> dict:
    text = f"{listing.get('title','')} {listing.get('description','')}".lower()
    flags = [label for pattern, label in RED_FLAG_RULES if re.search(pattern, text)]

    rent = _rent_value(listing.get("rent", ""))
    if rent and rent < 800:
        flags.append(f"Rent ${rent} is far below the Berkeley market for a private room")

    history = memory.lookup_contact(listing.get("contact", ""))
    if history:
        h = history[-1]
        flags.insert(0, f"Flagged by another student's agent {time_ago(h['when'])}: same number at "
                        f"{h['address']} under the name '{h['landlord']}'")

    over_budget = bool(rent and student_budget and rent > student_budget)
    if history or len(flags) >= 2:
        status = "blocked"
    elif flags:
        status = "verify_first"
    elif over_budget:
        status = "over_budget"
    else:
        status = "contact_at_8am"
    return {**listing, "flags": flags, "status": status}


def run_overnight(student: str, student_budget: int, urgent: bool = False) -> dict:
    listings = load_feed()
    screened = [screen(l, student_budget) for l in listings]
    queued = [s for s in screened if s["status"] in ("contact_at_8am", "verify_first")]
    fo_tasks = {s["address"]: build_fo_task(s, student, "", urgent) for s in queued}
    return {
        "found": len(listings),
        "screened": screened,
        "blocked": [s for s in screened if s["status"] == "blocked"],
        "queued": queued,
        "fo_tasks": fo_tasks,
    }
