"""Builds the instruction BearDen hands to Fo.

Fo does the real-world part (texts / calls / emails the landlord from its own
number and waits for replies). Send this task to Fo through the Fo MCP in
Claude, or paste it into the Wajo app. Then paste the conversation back into
BearDen so the debrief can go into Cognee.
"""

BASE_QUESTIONS = [
    "Is the unit still available for the dates I need?",
    "Can I tour it in person this week? What times work?",
    "Whose name (person or company) will be on the lease?",
    "Are utilities included? If not, roughly how much per month?",
    "Is the lease June-June, Aug-Aug, or something else? Is summer subleasing allowed?",
    "How is the deposit paid, and is it paid before or after signing the lease?",
]


def build_fo_task(listing: dict, student: str, already_known: str, urgent: bool = False) -> str:
    known = already_known.strip() or "Nothing yet."
    qs = "\n".join(f"- {q}" for q in BASE_QUESTIONS)
    return f"""You are contacting a landlord on behalf of a UC Berkeley student ({student}).
Do NOT share the student's personal phone number or email. Use your own number/email.

Listing: {listing.get('address')} — {listing.get('rent')}/mo
Landlord: {listing.get('landlord')} ({listing.get('company') or 'no company given'})
Contact: {listing.get('contact')}

BearDen's shared memory already knows this about this landlord / company:
{known}

Skip any question already answered above. Ask the rest, politely and briefly:
{qs}

{"URGENT: the student needs to move within 2 weeks. Reach out now, and if there's no reply in 2 hours, follow up by a different channel (text -> call)." if urgent else "If there's no reply within 24 hours, follow up once by a different channel (text -> call, or email -> text)."} Do not send any money or agree to anything.
When done, report the full conversation and anything that seemed off
(refused a tour, asked for payment before a lease, wouldn't give a unit number or name)."""
