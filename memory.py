"""BearDen memory layer (Cognee).

Two kinds of memory:
  - shared_landlord_intel : what every landlord/property manager told Fo, plus red flags.
                            Every student's agent reads from this.
  - student_<name>        : one private dataset per student (budget, dates, schedule).

Plus a tiny local index (intel_index.json) of phone numbers / emails, so the
"seen before" check is instant and 100% reliable during the live demo.
"""
import asyncio
import json
import re
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

import cognee  # noqa: E402  (load .env before cognee reads config)

SHARED = "shared_landlord_intel"
INDEX = Path(__file__).with_name("intel_index.json")


def student_ds(name: str) -> str:
    return "student_" + re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


# ---------- local contact index (instant "seen before") ----------

def _load_index() -> dict:
    return json.loads(INDEX.read_text()) if INDEX.exists() else {}


def normalize_contact(c: str) -> str:
    c = c.strip().lower()
    digits = re.sub(r"\D", "", c)
    return digits[-10:] if len(digits) >= 10 and "@" not in c else c


def lookup_contact(contact: str) -> list[dict]:
    return _load_index().get(normalize_contact(contact), [])


def record_contact(contact: str, entry: dict) -> None:
    idx = _load_index()
    idx.setdefault(normalize_contact(contact), []).append(entry)
    INDEX.write_text(json.dumps(idx, indent=2))


# ---------- Cognee Cloud ----------
# Uses your Cognee Cloud credits: no OpenAI/Anthropic key needed.
# .env needs COGNEE_URL (tenant URL from the API Keys page) and COGNEE_API_KEY.
import os  # noqa: E402

RUN_FILE = Path(__file__).with_name(".demo_run")


def _run_id() -> str:
    return RUN_FILE.read_text().strip() if RUN_FILE.exists() else "r1"


def _ds(name: str) -> str:
    # Suffix lets "Reset" start fresh datasets without deleting anything in the cloud.
    return f"{name}_{_run_id()}"


async def _connect():
    await cognee.serve(url=os.environ["COGNEE_URL"], api_key=os.environ["COGNEE_API_KEY"])


async def _add_and_cognify(text: str, dataset: str) -> None:
    await _connect()
    await cognee.remember(text, dataset_name=_ds(dataset))


def _fmt(r) -> str:
    for attr in ("answer", "search_result", "text", "content"):
        v = getattr(r, attr, None)
        if v:
            return str(v)
    if isinstance(r, dict):
        for k in ("answer", "search_result", "text", "content"):
            if r.get(k):
                return str(r[k])
    return str(r)


async def _ask(question: str, datasets: list[str]) -> str:
    await _connect()
    results = await cognee.recall(query_text=question, datasets=[_ds(d) for d in datasets])
    if not results:
        return "Nothing in memory yet."
    return "\n".join(_fmt(r) for r in results)


def save_student_profile(student: str, profile: str) -> None:
    asyncio.run(_add_and_cognify(f"Student {student} housing needs: {profile}", student_ds(student)))


def save_debrief(student: str, listing: dict, conversation: str) -> None:
    """After Fo talks to a landlord, write what was learned into SHARED memory.
    This is the self-improving step: the next student's agent benefits."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    text = (
        f"[{ts}] Landlord verification debrief.\n"
        f"Listing address: {listing.get('address')}\n"
        f"Landlord name given: {listing.get('landlord')}\n"
        f"Management company: {listing.get('company') or 'unknown'}\n"
        f"Landlord contact: {listing.get('contact')}\n"
        f"Asking rent: {listing.get('rent')}\n"
        f"Conversation between Fo (BearDen's agent) and the landlord:\n{conversation}\n"
    )
    asyncio.run(_add_and_cognify(text, SHARED))
    record_contact(listing.get("contact", ""), {
        "when": ts,
        "address": listing.get("address"),
        "landlord": listing.get("landlord"),
        "checked_for": student,
    })


def ask_shared(question: str) -> str:
    return asyncio.run(_ask(question, [SHARED]))


def ask_for_student(student: str, question: str) -> str:
    """Student agent: private prefs + shared intel together."""
    return asyncio.run(_ask(question, [student_ds(student), SHARED]))


def reset_all() -> None:
    """Start fresh demo datasets (new suffix) and clear the local contact index."""
    n = int(_run_id().lstrip("r") or 1) + 1
    RUN_FILE.write_text(f"r{n}")
    if INDEX.exists():
        INDEX.unlink()
