"""BearDen: agents that keep Berkeley students safe through the whole apartment hunt.
Fo does the real-world outreach from its own number; Cognee remembers what every agent learns.
Run:  streamlit run app.py
"""
import html
import os
import re
import time
from datetime import datetime

import streamlit as st

import memory
from fo_tasks import build_fo_task
from overnight import load_feed, money_at_risk, run_overnight, screen

st.set_page_config(page_title="BearDen", page_icon="🐻", layout="wide", initial_sidebar_state="expanded")

NAVY = "#0B2D5B"
GOLD = "#F5B921"

# ---------------------------------------------------------------- styles
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"], .stApp, button, input, textarea, select {{ font-family: 'Inter', -apple-system, sans-serif; }}
.stApp {{ background: #F5F7FA; }}
header[data-testid="stHeader"] {{ background: transparent; }}
#MainMenu, footer, [data-testid="stToolbar"] {{ visibility: hidden; }}
.block-container {{ padding-top: 2.6rem; max-width: 1180px; }}
h1, h2, h3 {{ color: #10233F; letter-spacing: -0.02em; }}

/* sidebar */
section[data-testid="stSidebar"] {{ background: {NAVY}; }}
section[data-testid="stSidebar"] * {{ color: #E8EEF7; }}
section[data-testid="stSidebar"] [role="radiogroup"] {{ gap: 6px; }}
section[data-testid="stSidebar"] [role="radiogroup"] label {{
  padding: 11px 14px; border-radius: 10px; border-left: 3px solid transparent; width: 100%; margin: 0; }}
section[data-testid="stSidebar"] [role="radiogroup"] label:hover {{ background: rgba(255,255,255,.06); }}
section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {{
  background: rgba(255,255,255,.12); border-left-color: {GOLD}; }}
section[data-testid="stSidebar"] [role="radiogroup"] label > div:first-child,
section[data-testid="stSidebar"] [data-baseweb="radio"] > div:first-child,
section[data-testid="stSidebar"] label[data-testid="stRadioOption"] > div > div:first-child:not([data-testid]) {{ display: none !important; }}
section[data-testid="stSidebar"] label[data-testid="stRadioOption"][data-selected="true"] {{
  background: rgba(255,255,255,.12); border-left-color: {GOLD}; }}
section[data-testid="stSidebar"] [role="radiogroup"] label {{ min-width: 100%; }}
section[data-testid="stSidebar"] [role="radiogroup"] label p {{ font-size: 15px; font-weight: 600; }}
section[data-testid="stSidebar"] input {{ color: #10233F !important; }}
section[data-testid="stSidebar"] .stButton button {{ background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.18); }}

/* buttons */
.stButton button[kind="primary"], [data-testid="stBaseButton-primary"] {{
  background: {NAVY}; border-color: {NAVY}; color: #fff; font-weight: 600; border-radius: 10px; }}
.stButton button[kind="secondary"] {{ border-radius: 10px; font-weight: 600; }}

/* building blocks */
.bd-eyebrow {{ font-size: 12px; font-weight: 700; letter-spacing: .12em; color: #5A6B85; text-transform: uppercase; margin-bottom: 4px; }}
.bd-h1 {{ font-size: 40px; font-weight: 500; color: #10233F; line-height: 1.12; letter-spacing: -0.02em; margin: 0 0 8px; }}
.bd-sub {{ color: #5A6B85; font-size: 16px; margin-bottom: 26px; }}
.bd-card {{ background: #fff; border: 1px solid #E4E8EF; border-radius: 16px; padding: 22px 24px; margin-bottom: 14px; }}
.bd-stat {{ background: #fff; border: 1px solid #E4E8EF; border-radius: 14px; padding: 18px; display: flex; gap: 14px; align-items: flex-start; }}
.bd-stat .ic {{ width: 44px; height: 44px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 18px; }}
.bd-stat .n {{ font-size: 26px; font-weight: 600; color: #10233F; line-height: 1; }}
.bd-stat .l {{ font-size: 13px; font-weight: 600; color: #10233F; margin-top: 6px; }}
.bd-stat .s {{ font-size: 11.5px; color: #6B7A90; margin-top: 2px; }}
.bd-pill {{ display: inline-block; padding: 3px 10px; border-radius: 999px; font-size: 10.5px; font-weight: 700; letter-spacing: .06em; }}
.bd-tag {{ display: inline-block; padding: 3px 10px; border-radius: 999px; font-size: 12px; font-weight: 600; background: #EEF2F8; color: #24406B; margin: 2px 4px 2px 0; }}
.bd-note {{ background: #FFF8E8; border: 1px solid #F4DDA4; border-radius: 12px; padding: 14px 16px; color: #6B4E0E; font-size: 13.5px; }}
.bd-listing {{ display: flex; background: #fff; border: 1px solid #E4E8EF; border-radius: 16px; overflow: hidden; margin-bottom: 6px; min-height: 170px; }}
.bd-listing img {{ width: 150px; object-fit: cover; flex-shrink: 0; }}
.bd-listing .body {{ padding: 18px 20px; flex: 1; position: relative; }}
.bd-listing .verdict {{ font-size: 13px; font-weight: 700; color: #10233F; }}
.bd-listing .addr {{ font-size: 19px; font-weight: 500; color: #10233F; margin: 6px 0 8px; }}
.bd-listing .meta {{ font-size: 12.5px; color: #5A6B85; }}
.bd-listing .meta b {{ color: #10233F; }}
.bd-listing .why {{ font-size: 12.5px; color: #4A5A72; margin-top: 8px; }}
.bd-listing .win {{ font-size: 12.5px; color: #067647; font-weight: 600; margin-top: 6px; }}
.bd-listing .badge {{ position: absolute; top: 18px; right: 20px; }}
.bd-time {{ color: #B7791F; font-weight: 600; }}
.bd-perm {{ display: flex; gap: 12px; align-items: center; padding: 6px 0; }}
.bd-ico {{ width: 36px; height: 36px; border-radius: 9px; background: #EEF2F8; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }}
.bd-bubble-out {{ background: {NAVY}; color: #fff; padding: 11px 14px; border-radius: 12px 12px 2px 12px; margin: 4px 0 12px auto; max-width: 75%; font-size: 13.5px; }}
.bd-bubble-in {{ background: #EEF1F5; color: #10233F; padding: 11px 14px; border-radius: 12px 12px 12px 2px; margin: 4px auto 12px 0; max-width: 75%; font-size: 13.5px; }}
.bd-who {{ font-size: 10.5px; color: #7A889C; letter-spacing: .04em; text-transform: uppercase; }}
.bd-chain {{ display: flex; align-items: center; gap: 10px; justify-content: center; flex-wrap: wrap; margin: 18px 0; }}
.bd-node {{ border: 1px solid #E4E8EF; border-radius: 14px; padding: 16px 18px; text-align: center; background: #FAFBFD; min-width: 140px; }}
.bd-arrow {{ color: #8A97AB; font-size: 11px; text-align: center; }}
.bd-dark {{ background: {NAVY}; color: #fff; border-radius: 16px; padding: 20px 24px; display: flex; align-items: center; gap: 24px; }}
.bd-dark .n {{ color: {GOLD}; font-size: 22px; font-weight: 700; }}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------- state
ss = st.session_state
ss.setdefault("profile", dict(name="Maya", budget=1500, room="Private room", move_in="Aug 1", walk=20,
                              tours="Tue/Thu after 3pm",
                              musts=["In-unit laundry", "Utilities under $150", "Summer sublease allowed"]))
ss.setdefault("perms", dict(search=True, scams=True, fo=True, tours="Ask me first"))
ss.setdefault("settings", dict(quiet_from="9:00 PM", quiet_to="8:00 AM", brief="9:00 AM", paused=False))
ss.setdefault("convos", {})      # address -> pasted Fo report
ss.setdefault("sent", set())     # addresses Fo has a task for
ss.setdefault("nav", "Search Profile")
if "_goto" in ss:
    ss.nav = ss.pop("_goto")

P = ss.profile
student = P["name"]
budget = int(P["budget"])
FO_NUMBER = os.environ.get("FO_NUMBER", "").strip() or "Fo's number"


def go(page):
    ss._goto = page
    st.rerun()


def clock(ts):
    try:
        return datetime.strptime(ts, "%Y-%m-%d %H:%M").strftime("%-I:%M %p")
    except Exception:
        return ts


def esc(s):
    return html.escape(str(s or ""))


def rent_of(s):
    return int(re.sub(r"\D", "", s.get("rent", "")) or 0)


def true_cost(s):
    rent = rent_of(s)
    if "Utilities included" in s.get("amenities", []):
        util = 0
    else:
        m = re.search(r"~\$(\d+)", s.get("description", ""))
        util = int(m.group(1)) if m else 100
    return rent + util


NIGHT_TIMES = ["2:04 AM", "6:18 AM", "8:40 AM", "2:04 AM", "2:07 AM", "3:12 AM", "4:45 AM", "5:30 AM"]
ORDER = {"blocked": 0, "contact_at_8am": 1, "verify_first": 2, "over_budget": 3}
BADGE = {
    "blocked": ("BLOCKED", "#FDECEC", "#C0262D"),
    "contact_at_8am": ("VERIFIED", "#E5F5EC", "#0B7A47"),
    "verify_first": ("FO IS ASKING", "#FFF4DE", "#A86A00"),
    "over_budget": ("OVER BUDGET", "#EEF1F5", "#536179"),
}


def network_flag(s):
    return next((f for f in s.get("flags", []) if f.startswith("Flagged by another")), None)


def verdict(s):
    st_ = s["status"]
    if st_ == "blocked":
        return "⊘ Don't contact this landlord" if network_flag(s) else "⊘ Too risky to pursue"
    if st_ == "contact_at_8am":
        return "✓ Safe option, ready to tour"
    if st_ == "verify_first":
        return "! Promising, needs one more answer"
    return "$ Legit, but above your limit"


def reason(s):
    if s["status"] == "blocked":
        nf = network_flag(s)
        rest = [f for f in s["flags"] if f != nf]
        lead = (nf.split(": ", 1)[1][0].upper() + nf.split(": ", 1)[1][1:] + ". ") if nf else ""
        return lead + "; ".join(rest) + "."
    if s["status"] == "over_budget":
        return f"Looks legitimate, but is ${true_cost(s) - budget:,} over your ${budget:,} max monthly cost."
    if s["status"] == "verify_first":
        return "Fo is checking: " + "; ".join(s["flags"]) + "."
    return s["description"][:140]


def listing_card(s, i):
    label, bg, fg = BADGE[s["status"]]
    photo = (s.get("photos") or [""])[0]
    tc = true_cost(s)
    cost = f" &nbsp;•&nbsp; <b>${tc:,}/mo true cost</b>" if s["status"] != "blocked" else ""
    win = (f'<div class="win">You avoided a likely ${money_at_risk(s):,} loss</div>'
           if s["status"] == "blocked" else "")
    st.markdown(f"""
<div class="bd-listing">
  <img src="{esc(photo)}"/>
  <div class="body">
    <span class="badge bd-pill" style="background:{bg};color:{fg}">{label}</span>
    <div class="verdict">{esc(verdict(s))}</div>
    <div class="addr">{esc(s['address'])}</div>
    <div class="meta"><b>{esc(s['rent'])} rent</b>{cost} &nbsp;•&nbsp; {esc(s['source'])} &nbsp;•&nbsp;
      <span class="bd-time">☾ {NIGHT_TIMES[i % len(NIGHT_TIMES)]}</span></div>
    <div class="why">{esc(reason(s))}</div>{win}
  </div>
</div>""", unsafe_allow_html=True)


def send(task, addr=None, rerun=True):
    from fo_send import send_to_fo
    ok, msg = send_to_fo(task)
    if ok and addr:
        ss.sent.add(addr)
    ss.setdefault("flash", []).append((ok, (f"{addr}: " if addr else "") + msg))
    if rerun:
        st.rerun()
    return ok


def show_flash():
    items = ss.pop("flash", [])
    good = [m for ok, m in items if ok]
    if len(good) > 1:
        st.success(f"◉ Sent {len(good)} tasks to Fo ({FO_NUMBER}). Watch your phone for Fo's reports.")
    elif good:
        st.success(good[0])
    for ok, m in items:
        if not ok:
            st.error(m)


def safe_call(fn, *a, fail="Memory unavailable right now"):
    try:
        r = fn(*a)
        return True if r is None else r
    except Exception as e:  # keep the demo alive if Cognee hiccups
        st.warning(f"{fail} ({type(e).__name__})")
        return None


def screened_feed():
    night = ss.get("night")
    rows = night["screened"] if night else [screen(l, budget) for l in load_feed()]
    return sorted(rows, key=lambda s: (ORDER[s["status"]], true_cost(s)))


def header(eyebrow, title, sub, right_html=""):
    c1, c2 = st.columns([3, 1])
    c1.markdown(f'<div class="bd-eyebrow">{eyebrow}</div><div class="bd-h1">{title}</div>'
                f'<div class="bd-sub">{sub}</div>', unsafe_allow_html=True)
    if right_html:
        c2.markdown(right_html, unsafe_allow_html=True)


WORKED = ('<div class="bd-note" style="margin-top:22px">☾ <b>Your agent worked 10 hours.</b><br>'
          '<span style="font-size:12px">You spent 0 minutes.</span></div>')

# ---------------------------------------------------------------- sidebar
night = ss.get("night")
pending = len([a for a in (night or {}).get("fo_tasks", {}) if a not in ss.sent]) if night else 0
with st.sidebar:
    st.markdown(f'<div style="font-size:28px;font-weight:700;margin:4px 0 18px">🐻 BearDen</div>',
                unsafe_allow_html=True)
    status = ("☾ <b>Overnight complete</b><br><span style='font-size:12px;opacity:.75'>10h of work saved</span>"
              if night else
              "☾ <b>Ready for tonight</b><br><span style='font-size:12px;opacity:.75'>Starts watching at 11:00 PM</span>")
    if ss.settings["paused"]:
        status = "⏸ <b>Agent paused</b><br><span style='font-size:12px;opacity:.75'>Resume in Settings</span>"
    st.markdown(f'<div style="background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.15);'
                f'border-radius:14px;padding:14px 16px;margin-bottom:18px;font-size:14px">{status}</div>',
                unsafe_allow_html=True)
    pages = ["Search Profile", "Morning Briefing", "Listings", "Fo Activity", "Shared Memory", "Settings"]
    icons = {"Search Profile": "◎", "Morning Briefing": "⌂", "Listings": "▤", "Fo Activity": "◉",
             "Shared Memory": "⌘", "Settings": "⚙"}
    st.radio("Navigate", pages, key="nav", label_visibility="collapsed",
             format_func=lambda p: f"{icons[p]}   {p}" + (f"   ({pending})" if p == "Fo Activity" and pending else ""))
    st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)
    st.markdown(f"<div style='border-top:1px solid rgba(255,255,255,.15);padding-top:14px;font-size:14px'>"
                f"<b>{esc(student)}</b><br><span style='opacity:.7;font-size:12px'>UC Berkeley student</span></div>",
                unsafe_allow_html=True)

page = ss.nav

show_flash()

# ================================================================ SEARCH PROFILE
if page == "Search Profile":
    header("Your private search profile", "Tell BearDen once. It remembers.",
           "Your agent uses these preferences to make decisions while you sleep.",
           '<div style="text-align:right;margin-top:8px"><span class="bd-tag">🔒 Private memory</span></div>')
    left, right = st.columns([1.55, 1], gap="medium")
    with left:
        with st.container(border=True):
            st.markdown(f"#### {esc(student)}'s housing search")
            st.caption("Saved to your private agent memory")
            P["name"] = st.text_input("Your name", P["name"])
            a, b = st.columns(2)
            P["budget"] = a.number_input("Max monthly cost, incl. utilities ($)", 600, 4000, int(P["budget"]), 50)
            rooms = ["Private room", "Studio", "Shared room"]
            P["room"] = b.selectbox("Room type", rooms, index=rooms.index(P["room"]))
            P["move_in"] = a.selectbox("Move-in date", ["Now", "Jun 1", "Aug 1", "Aug 15"],
                                       index=["Now", "Jun 1", "Aug 1", "Aug 15"].index(P["move_in"]))
            P["walk"] = b.selectbox("Max walk to campus", [10, 15, 20, 30], index=[10, 15, 20, 30].index(P["walk"]),
                                    format_func=lambda m: f"{m} min")
            P["tours"] = st.text_input("Tour availability", P["tours"])
            opts = sorted(set(P["musts"]) | {"In-unit laundry", "Utilities under $150", "Summer sublease allowed",
                                             "Furnished", "Parking", "Pets OK"})
            P["musts"] = st.multiselect("Must-haves", opts, default=P["musts"])
            st.markdown('<div class="bd-note" style="background:#F3F6FA;border-color:#E4E8EF;color:#24406B">'
                        '🔒 <b>Private: only your agent sees this.</b><br>'
                        '<span style="font-size:12px">Never shared with other students or landlords.</span></div>',
                        unsafe_allow_html=True)
            if st.button("Save profile"):
                with st.spinner("Writing to private memory..."):
                    if safe_call(memory.save_student_profile, P["name"],
                                 f"Max ${P['budget']}/mo all-in, {P['room']}, move-in {P['move_in']}, "
                                 f"{P['walk']}-min walk, tours {P['tours']}, must-haves: {', '.join(P['musts'])}"):
                        st.success("✓ Saved")
    with right:
        with st.container(border=True):
            st.markdown('<div class="bd-eyebrow">Agent permissions</div>', unsafe_allow_html=True)
            st.markdown("#### While you sleep, BearDen may:")
            perms = ss.perms
            perms["search"] = st.toggle("🔎 Search new listings · across 4 trusted sources", perms["search"])
            perms["scams"] = st.toggle("◇ Screen for scams · rules + shared student memory", perms["scams"])
            perms["fo"] = st.toggle("◉ Have Fo message landlords · 8 AM–9 PM only", perms["fo"])
            perms["tours"] = st.selectbox("▣ Book tours", ["Ask me first", "Book automatically", "Never"],
                                          index=["Ask me first", "Book automatically", "Never"].index(perms["tours"]))
            st.markdown('<div class="bd-note">☾ <b>Ready for tonight</b><br>'
                        '<span style="font-size:12px">Starts watching at 11:00 PM</span></div>',
                        unsafe_allow_html=True)
            st.write("")
            if st.button("Start my overnight agent ☾", type="primary", use_container_width=True,
                         disabled=ss.settings["paused"]):
                result = run_overnight(student, budget, urgent=P["move_in"] == "Now")
                result["kept"] = sum(money_at_risk(s) for s in result["blocked"])
                box = st.empty()
                lines = [
                    f"🌙 11:00 PM · Watching listing sources... found **{result['found']}** listings",
                    f"🔍 2:00 AM · Screened against red-flag rules + other students' agents. Blocked **{len(result['blocked'])}**",
                    f"◉ 7:55 AM · Fo drafted messages to **{len(result['queued'])}** landlords from its own number",
                    "☀️ 8:00 AM · Morning briefing ready",
                ]
                for k in range(len(lines)):
                    box.markdown("\n\n".join(lines[:k + 1]))
                    time.sleep(0.8)
                ss.night = result
                ss.sent = set()
                go("Morning Briefing")
            st.caption("You can pause or change this anytime")

# ================================================================ MORNING BRIEFING
elif page == "Morning Briefing":
    today = datetime.now().strftime("%A, %B %-d").upper()
    header(today, f"Good morning, {esc(student)} ☀", "Here’s what happened while you slept.",
           WORKED if night else "")
    if not night:
        st.info("Your agent hasn't run yet. Set your preferences, then start your overnight agent.")
        if st.button("Go to Search Profile", type="primary"):
            go("Search Profile")
        st.stop()

    stats = [("⌕", "#EAF1FB", night["found"], "New listings", f"+{night['found']} overnight"),
             ("◇", "#FDECEC", len(night["blocked"]), "Scams blocked", f"${night['kept']:,} protected"),
             ("◉", "#F0EBFB", len(night["queued"]), "Landlords for Fo",
              "contacted by Fo" if all(s["address"] in ss.sent for s in night["queued"]) else "Waiting for your OK"),
             ("▣", "#FFF4DE", len([s for s in night["screened"] if s["status"] == "contact_at_8am"][:1]),
              "Tour offered", "Needs your OK")]
    for col, (ic, bg, n, l, s_) in zip(st.columns(4), stats):
        col.markdown(f'<div class="bd-stat"><div class="ic" style="background:{bg}">{ic}</div>'
                     f'<div><div class="n">{n}</div><div class="l">{l}</div><div class="s">{s_}</div></div></div>',
                     unsafe_allow_html=True)
    st.write("")

    tour = next((s for s in night["screened"] if s["status"] == "contact_at_8am"), None)
    if tour:
        with st.container(border=True):
            c1, c2, c3 = st.columns([0.6, 3.6, 3])
            c1.markdown('<div style="border:1px solid #E4E8EF;border-radius:8px;text-align:center;overflow:hidden">'
                        f'<div style="background:{GOLD};font-size:11px;font-weight:700">THU</div>'
                        '<div style="font-size:24px;font-weight:600;padding:2px 0">17</div></div>',
                        unsafe_allow_html=True)
            c2.markdown(f'<div class="bd-eyebrow" style="color:#A86A00">1 tour needs your OK</div>'
                        f'<div style="font-size:20px;color:#10233F">{esc(tour["address"])} · Thursday at 4:00 PM</div>'
                        f'<div style="font-size:12px;color:#0B7A47">✓ Fits your schedule · ✓ ${true_cost(tour):,} true cost'
                        f' · ✓ Verified landlord</div>', unsafe_allow_html=True)
            b1, b2 = c3.columns(2)
            if b2.button("Confirm tour", type="primary", use_container_width=True):
                send(f"Please confirm the in-person tour at {tour['address']} with {tour['landlord']} "
                     f"({tour['contact']}) for Thursday at 4:00 PM on behalf of a UC Berkeley student. "
                     f"Use your own number. Do not send any money.", tour["address"])
            if b1.button("Suggest another time", use_container_width=True):
                send(f"Ask {tour['landlord']} ({tour['contact']}) about {tour['address']}: Thursday 4 PM doesn't work. "
                     f"Offer {P['tours']} instead. Use your own number.", tour["address"])

    c1, c2 = st.columns([4, 1])
    c1.markdown('### Your overnight shortlist <span style="font-size:12px;color:#7A889C;font-weight:400">'
                'Ranked by safety and fit</span>', unsafe_allow_html=True)
    if c2.button("View all listings →"):
        go("Listings")
    for i, s in enumerate(sorted(night["screened"], key=lambda s: ORDER[s["status"]])[:5]):
        listing_card(s, i)

# ================================================================ LISTINGS
elif page == "Listings":
    header("Your shortlist", "Listings your agent reviewed",
           "Every option is ranked against your private preferences.", WORKED if night else "")

    with st.expander("🔍 Found one yourself? Paste a link or post and BearDen checks it in seconds"):
        pasted = st.text_area("Listing", height=110, label_visibility="collapsed",
                              placeholder="'Sunny room on Channing, $1,100. I'm overseas so can't show it, "
                                          "send $800 deposit by Zelle to hold. Text (510) 555-0142'")
        if st.button("Check it", type="primary") and pasted.strip():
            phone = re.search(r"\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}", pasted)
            email = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", pasted)
            rent = re.search(r"\$\s?(\d[\d,]{2,})", pasted)
            lst = dict(address="Pasted listing", title="", description=pasted,
                       rent=f"${rent.group(1)}" if rent else "", landlord="(from post)", company="",
                       contact=(phone or email).group(0) if (phone or email) else "", source="Pasted")
            ss.last_check = (lst, screen(lst, budget))
        if "last_check" in ss:
            lst, s = ss.last_check
            if s["status"] == "blocked":
                st.error(f"### ⊘ Likely scam. Don't send money.\nYou just kept your **${money_at_risk(lst):,}**.")
            elif s["status"] == "verify_first":
                st.warning("### ! Some warning signs. Let Fo verify the landlord before you pay anything.")
            else:
                st.success("### ✓ No red flags found. Fo can ask your questions.")
            for f in s["flags"]:
                st.write(("🌐 " if f.startswith("Flagged by another") else "🚩 ") + f)
            if s["status"] != "blocked" and lst["contact"]:
                if st.button("📲 Have Fo contact this landlord"):
                    send(build_fo_task(lst, student, "", P["move_in"] == "Now"))

    rows = screened_feed()
    c1, c2 = st.columns([4, 1])
    c1.markdown(f'### All {len(rows)} reviewed listings <span style="font-size:12px;color:#7A889C;'
                f'font-weight:400">Ranked by safety and fit</span>', unsafe_allow_html=True)
    hide = c2.toggle("Hide blocked", False)
    for i, s in enumerate(rows):
        if hide and s["status"] == "blocked":
            continue
        listing_card(s, i)
        with st.expander("Details · trust report · send to Fo"):
            d1, d2 = st.columns([1, 1])
            d1.write(s["description"])
            d1.caption(f'{s["room_type"]} · {s["neighborhood"]} · 🚶 {s["walk_min"]} min · move-in {s["move_in"]} · '
                       f'Landlord: {s["landlord"]}' + (f' ({s["company"]})' if s["company"] else ""))
            d1.markdown("".join(f'<span class="bd-tag">{esc(a)}</span>' for a in s["amenities"]),
                        unsafe_allow_html=True)
            for f in s["flags"] or ["No red flags found"]:
                d2.write(("🚩 " if s["flags"] else "✓ ") + f)
            if s["status"] == "blocked":
                d2.caption("Fo won't contact a landlord BearDen can't trust.")
            elif s["address"] in ss.sent:
                d2.success("Fo is on it ✓")
            elif d2.button("📲 Send to Fo", key=f"fo_{i}", type="primary"):
                known = safe_call(memory.ask_shared,
                                  f"What do we know about landlord {s['landlord']}, contact {s['contact']}, "
                                  f"or address {s['address']}?") or ""
                send(build_fo_task(s, student, known, P["move_in"] == "Now"), s["address"])

# ================================================================ FO ACTIVITY
elif page == "Fo Activity":
    header('<span class="bd-tag" style="background:#F0EBFB;color:#5B3DB5">◉ Outreach by Fo</span>',
           "Fo is handling the back-and-forth,<br>from its own number.",
           "Questions asked, follow-ups sent, red flags caught, all without exposing you.",
           f'<div class="bd-card" style="padding:14px 16px;margin-top:8px"><div class="bd-eyebrow">Fo’s contact</div>'
           f'<b>{esc(FO_NUMBER)}</b><br><span style="font-size:12px;color:#7A889C">Powered by Wajo</span></div>')
    st.markdown('<div class="bd-note" style="background:#EEF5FC;border-color:#CFE0F3;color:#24406B">▣ '
                '<b>Your personal phone and email are never shared with landlords.</b><br>'
                '<span style="font-size:12px">Fo uses a dedicated identity and only shares what you approve.</span></div>',
                unsafe_allow_html=True)
    st.write("")
    if not night:
        st.info("No outreach yet. Start your overnight agent and Fo will draft messages to every landlord worth contacting.")
        st.stop()

    queued = night["queued"]
    waiting = [s for s in queued if s["address"] not in ss.sent]
    if waiting:
        with st.container(border=True):
            c1, c2 = st.columns([3, 1.3])
            c1.markdown(f"**✋ Fo drafted messages to {len(waiting)} landlord{'s' if len(waiting) > 1 else ''} "
                        f"and is waiting for your OK.**  \nNothing is sent until you approve.")
            if c2.button(f"Approve & send to {len(waiting)}", type="primary", use_container_width=True):
                for s in waiting:
                    send(night["fo_tasks"][s["address"]], s["address"], rerun=False)
                st.rerun()

    convos = queued + [s for s in night["blocked"] if network_flag(s)]
    left, right = st.columns([1, 2.1], gap="medium")
    with left:
        with st.container(border=True):
            st.markdown(f"**Conversations** <span style='float:right;font-size:12px;color:#7A889C'>"
                        f"{len(queued)} active</span>", unsafe_allow_html=True)

            def tag(s):
                if s["status"] == "blocked":
                    return "BLOCKED"
                if s["address"] in ss.convos:
                    return "REPLIED"
                return "SENT" if s["address"] in ss.sent else "DRAFTED"
            pick = st.radio("Conversation", [s["address"] for s in convos], label_visibility="collapsed",
                            format_func=lambda a: f"{a}  ·  {tag(next(s for s in convos if s['address'] == a))}")
    s = next(x for x in convos if x["address"] == pick)
    with right:
        with st.container(border=True):
            label, bg, fg = BADGE[s["status"]] if s["status"] == "blocked" else (
                ("TOUR OFFERED", "#E5F5EC", "#0B7A47") if s["address"] in ss.convos else
                ("FO IS ASKING", "#FFF4DE", "#A86A00"))
            st.markdown(f'<span class="bd-pill" style="float:right;background:{bg};color:{fg}">{label}</span>'
                        f'<b style="font-size:16px">{esc(s["address"])}</b><br>'
                        f'<span style="font-size:12px;color:#7A889C">{esc(s["company"] or s["landlord"])} · '
                        f'{esc(s["contact"])}</span>', unsafe_allow_html=True)
            st.divider()
            if s["status"] == "blocked":
                st.markdown(f'<div class="bd-bubble-in"><div class="bd-who">From shared memory</div>'
                            f'{esc(network_flag(s).split(": ", 1)[1])}</div>', unsafe_allow_html=True)
                st.markdown('<div class="bd-note" style="background:#FDECEC;border-color:#F6C9C9;color:#8A1C1C">'
                            '⊘ Fo did not contact this landlord. Another student\'s agent already caught this number.</div>',
                            unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="bd-who" style="text-align:right">Fo · task</div>'
                            f'<div class="bd-bubble-out">Hi! I\'m reaching out on behalf of a UC Berkeley student about '
                            f'{esc(s["address"])}. Is it still available for an {esc(P["move_in"])} move-in? '
                            f'Can they tour in person {esc(P["tours"])}? Whose name is on the lease, and is the '
                            f'deposit paid before or after signing?</div>', unsafe_allow_html=True)
                report = ss.convos.get(s["address"], "")
                for line in report.splitlines():
                    if not line.strip():
                        continue
                    who, _, msg = line.partition(":")
                    out = who.strip().lower() in ("fo", "fo (bearden)")
                    st.markdown(f'<div class="bd-who" style="text-align:{"right" if out else "left"}">{esc(who)}</div>'
                                f'<div class="{"bd-bubble-out" if out else "bd-bubble-in"}">{esc(msg.strip() or line)}</div>',
                                unsafe_allow_html=True)
                with st.expander("Full task Fo received"):
                    st.code(night["fo_tasks"].get(s["address"], ""), language=None)
                a, b = st.columns(2)
                if s["address"] not in ss.sent and a.button("📲 Send to Fo", type="primary", key="send_one"):
                    send(night["fo_tasks"][s["address"]], s["address"])
                    st.rerun()
                with st.form(f"log_{pick}", clear_on_submit=True):
                    convo = st.text_area("Paste Fo's report", height=110,
                                         placeholder="Fo: Is the unit still available?\nLandlord: Yes, tours Thursday at 4 PM...")
                    if st.form_submit_button("Save to shared memory") and convo.strip():
                        ss.convos[s["address"]] = convo
                        with st.spinner("Teaching every student's agent what Fo learned..."):
                            safe_call(memory.save_debrief, student, s, convo)
                        st.rerun()

# ================================================================ SHARED MEMORY
elif page == "Shared Memory":
    idx = memory._load_index()
    facts = sum(len(v) for v in idx.values())
    header('<span class="bd-tag">⌘ Memory by Cognee</span>', "Every student’s agent<br>makes everyone safer.",
           "Agents share safety facts, not student identities or private preferences.",
           f'<div class="bd-card" style="padding:16px;margin-top:8px"><span style="font-size:24px;font-weight:600">'
           f'{facts}</span><br><span style="font-size:12px;color:#7A889C">safety facts remembered</span></div>')

    caught = [s for s in screened_feed() if network_flag(s)]
    with st.container(border=True):
        st.markdown('<div class="bd-eyebrow">Last night · live memory chain</div>', unsafe_allow_html=True)
        st.markdown("#### One warning protected the next student")
        if caught:
            s = caught[0]
            h = memory.lookup_contact(s["contact"])[-1]
            st.markdown(f"""
<div class="bd-chain">
  <div class="bd-node"><div style="font-size:22px">🧑‍🎓</div><b>{esc(h.get('checked_for', 'Another student'))}'s agent</b><br>
    <span style="font-size:11px;color:#7A889C">Student identity private</span></div>
  <div class="bd-arrow">learned {esc(clock(h['when']))}<br>⟶</div>
  <div class="bd-node"><div style="font-size:20px">☎</div><b>{esc(s['contact'])}</b><br>
    <span style="font-size:11px">"{esc(h['landlord'])}" · SCAM</span></div>
  <div class="bd-arrow">linked instantly<br>⟶</div>
  <div><div class="bd-node" style="padding:8px 12px;margin-bottom:6px;text-align:left"><b>{esc(h['address'])}</b><br>
    <span style="font-size:11px;color:#7A889C">Original report</span></div>
    <div class="bd-node" style="padding:8px 12px;text-align:left"><b>{esc(s['address'])}</b><br>
    <span style="font-size:11px;color:#7A889C">New listing</span></div></div>
  <div class="bd-arrow">protected<br>⟶</div>
  <div class="bd-node" style="background:#FFF8E8;border-color:#F4DDA4"><div style="font-size:22px">🐻</div>
    <b>{esc(student)}'s agent</b><br><span style="font-size:11px">Blocked automatically</span><br>
    <span class="bd-pill" style="background:#E5F5EC;color:#0B7A47">Likely ${money_at_risk(s):,} saved</span></div>
</div>
<div class="bd-note">☾ <b>This entire chain happened while {esc(student)} slept.</b>
  They never saw the scam or exposed their phone number.</div>""", unsafe_allow_html=True)
        else:
            st.info("No cross-student warnings yet. When Fo reports a scammy landlord in Fo Activity, "
                    "every other student's agent blocks that number automatically.")

    a, b = st.columns(2, gap="medium")
    with a:
        with st.container(border=True):
            st.markdown("**⌘ Shared with all agents**  \n<span style='font-size:12px;color:#7A889C'>"
                        "Safety facts that protect the community</span>", unsafe_allow_html=True)
            for t in ["Landlord phone numbers", "Scam patterns & payment requests", "Verified tour reports",
                      "Landlord response times"]:
                st.markdown(f"✓ {t}")
    with b:
        with st.container(border=True):
            st.markdown(f"**▣ Private to {esc(student)} only** <span class='bd-pill' style='float:right;"
                        f"background:#EEF1F5'>PRIVATE</span>  \n<span style='font-size:12px;color:#7A889C'>"
                        f"Never shared</span>", unsafe_allow_html=True)
            for t in [f"${budget:,} monthly budget", f"{P['tours']} schedule", "Must-haves & room preferences",
                      "Personal contact details"]:
                st.markdown(f"▫ {esc(t)}")

    with st.container(border=True):
        st.markdown("**Ask BearDen** · answers from your private memory plus everything other agents learned")
        q = st.text_input("Ask", "Is this landlord safe to rent from, and what will my real monthly cost be?",
                          label_visibility="collapsed")
        if st.button("Ask", type="primary"):
            with st.spinner("Thinking with private + shared memory..."):
                ans = safe_call(memory.ask_for_student, student, q)
            if ans:
                st.write(ans)

    learned = len(ss.convos)
    st.markdown(f"""<div class="bd-dark"><div style="flex:1">☾ <b>Learned tonight</b><br>
<span style="font-size:12px;opacity:.75">New knowledge added while students slept</span></div>
<div style="text-align:center"><div class="n">{len(caught)}</div><span style="font-size:11px;opacity:.75">scam numbers</span></div>
<div style="text-align:center"><div class="n">{learned}</div><span style="font-size:11px;opacity:.75">Fo reports</span></div>
<div style="text-align:center"><div class="n">{facts}</div><span style="font-size:11px;opacity:.75">facts total</span></div>
</div>""", unsafe_allow_html=True)
    st.write("")
    if st.button("See how Fo learned this →"):
        go("Fo Activity")

# ================================================================ SETTINGS
elif page == "Settings":
    header("Agent controls", "Settings", "You’re always in control of when and how your agent acts.")
    S = ss.settings
    times = [f"{h}:00 {ap}" for ap in ("AM", "PM") for h in [12] + list(range(1, 12))]
    with st.container(border=True):
        c1, c2, c3 = st.columns([3, 1, 1])
        c1.markdown("**☾ Quiet hours**  \n<span style='font-size:12px;color:#7A889C'>No landlord contact during "
                    "these hours</span>", unsafe_allow_html=True)
        S["quiet_from"] = c2.selectbox("From", times, index=times.index(S["quiet_from"]), label_visibility="collapsed")
        S["quiet_to"] = c3.selectbox("To", times, index=times.index(S["quiet_to"]), label_visibility="collapsed")
        st.divider()
        c1, c2 = st.columns([3, 2])
        c1.markdown("**▣ Tour approval level**  \n<span style='font-size:12px;color:#7A889C'>What Fo can do when a "
                    "tour is offered</span>", unsafe_allow_html=True)
        opts = ["Ask me first", "Book automatically", "Never"]
        ss.perms["tours"] = c2.selectbox("Tours", opts, index=opts.index(ss.perms["tours"]), label_visibility="collapsed")
        st.divider()
        c1, c2 = st.columns([3, 2])
        c1.markdown("**☀ Morning briefing**  \n<span style='font-size:12px;color:#7A889C'>When your overnight "
                    "results arrive</span>", unsafe_allow_html=True)
        S["brief"] = c2.selectbox("Brief", times, index=times.index(S["brief"]), label_visibility="collapsed")
        st.divider()
        c1, c2 = st.columns([3, 2])
        c1.markdown("**◉ Fo privacy identity**  \n<span style='font-size:12px;color:#7A889C'>Landlords see Fo’s "
                    "number and email, never yours</span>", unsafe_allow_html=True)
        c2.markdown('<div style="text-align:right"><span class="bd-pill" style="background:#E5F5EC;color:#0B7A47">'
                    'PROTECTED</span></div>', unsafe_allow_html=True)
    with st.container(border=True):
        c1, c2 = st.columns([3, 1])
        c1.markdown("**⏸ Pause my agent**  \n<span style='font-size:12px;color:#7A889C'>Stops all searches, "
                    "screening, and landlord outreach.</span>", unsafe_allow_html=True)
        if c2.button("Resume agent" if S["paused"] else "Pause agent", type="primary", use_container_width=True):
            S["paused"] = not S["paused"]
            st.rerun()
    with st.expander("Demo tools"):
        if st.button("⚠️ Reset all memory (before demo)"):
            memory.reset_all()
            for k in ("night", "convos", "sent"):
                ss.pop(k, None)
            st.success("Memory cleared")
