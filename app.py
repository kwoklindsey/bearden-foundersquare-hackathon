"""BearDen — trustworthy apartment hunting for Berkeley students.
Run:  streamlit run app.py
"""
import streamlit as st

import memory
from fo_tasks import build_fo_task

st.set_page_config(page_title="BearDen", page_icon="🐻", layout="wide")
st.title("🐻 BearDen")
st.caption("Is this listing legit? Paste it and find out in seconds. Then BearDen keeps hunting, safely, while you sleep.")

student = st.sidebar.text_input("Student", "Student A")
with st.sidebar.expander("Private profile (only this student's agent sees it)"):
    profile = st.text_area("Needs", "Budget $1,400, own room, move in Aug 1, 20-min walk to campus, free after 3pm Tue/Thu")
    if st.button("Save profile"):
        with st.spinner("Writing to private memory..."):
            memory.save_student_profile(student, profile)
        st.success("Saved to " + memory.student_ds(student))
if st.sidebar.button("⚠️ Reset all memory (before demo)"):
    memory.reset_all()
    st.sidebar.success("Memory cleared")

st.markdown("""
<style>
h1, h2, h3 { color: #003262; }
.stButton>button[kind="primary"] { background:#003262; border-color:#003262; }
.bd-card { border:1px solid #E6E8EC; border-radius:14px; padding:12px 14px; margin-bottom:6px; background:#fff; }
.bd-price { font-size:1.35rem; font-weight:700; color:#003262; }
.bd-meta { color:#5B6270; font-size:0.9rem; }
.bd-pill { display:inline-block; padding:2px 10px; border-radius:999px; font-size:0.8rem; font-weight:600; margin:2px 4px 2px 0; }
.bd-chip { display:inline-block; padding:1px 8px; border-radius:999px; font-size:0.75rem; background:#F1F3F6; color:#3A4150; margin:2px 4px 2px 0; }
</style>""", unsafe_allow_html=True)

st.sidebar.markdown("### 🔎 Filters")
budget = st.sidebar.slider("Max all-in rent ($)", 600, 2500, int(st.session_state.get("qs_budget", 1400)), 50)
urgent = st.session_state.get("urgency", "In 2 weeks") != "Next fall"
f_hoods = st.sidebar.multiselect("Neighborhood", ["Southside", "Northside", "Downtown"], default=["Southside", "Northside", "Downtown"])
f_types = st.sidebar.multiselect("Room type", ["Private room", "Studio", "Shared room"], default=["Private room", "Studio", "Shared room"])
f_walk = st.sidebar.slider("Max walk to campus (min)", 5, 30, 20)
f_move = st.sidebar.multiselect("Move-in", ["Now", "Jun 1", "Aug 1", "Aug 15"], default=["Now", "Jun 1", "Aug 1", "Aug 15"])
f_amen = st.sidebar.multiselect("Must have", ["In-unit laundry", "Utilities included", "Furnished", "Parking", "Pets OK", "Balcony", "Backyard", "Gym"])
f_safe = st.sidebar.toggle("Hide likely scams", value=False)
f_trust = st.sidebar.toggle("Only verified-safe", value=False)

st.sidebar.markdown("### 💫 Your housing vibe")
_hoods = ["Southside", "Northside", "Downtown"]
v_hood = st.sidebar.selectbox("Favorite neighborhood", _hoods, index=_hoods.index(st.session_state.get("qs_hood", "Southside")))
v_nice = st.sidebar.multiselect("Nice to have", ["In-unit laundry", "Utilities included", "Furnished", "Parking", "Pets OK", "Balcony", "Backyard", "Gym"], default=["In-unit laundry"])

import re as _re
st.session_state.setdefault("den", [])


def rent_of(s):
    return int(_re.sub(r"\D", "", s["rent"]) or 0)


def true_cost(s):
    rent = rent_of(s)
    if "Utilities included" in s["amenities"]:
        util = 0
    else:
        m = _re.search(r"~\$(\d+)", s["description"])
        util = int(m.group(1)) if m else 100
    internet = 0 if "Utilities included" in s["amenities"] else 50
    parking = 30 if "Parking" in s["amenities"] else 0
    return rent, util, internet, parking, rent + util + internet + parking


def match(s):
    """Rule-based fit score. Scams never get a score: BearDen won't rank what it can't trust."""
    if s["status"] == "blocked":
        return None, ["Hidden: BearDen won't rank a listing it can't trust"]
    total = true_cost(s)[4]
    score, why = 50, []
    if total <= budget:
        score += 20; why.append(f"All-in ${total:,}/mo fits your budget")
    else:
        score -= 15; why.append(f"All-in ${total:,}/mo is over budget")
    if s["neighborhood"] == v_hood:
        score += 10; why.append(f"In {v_hood}, your favorite")
    if s["walk_min"] <= 10:
        score += 8; why.append(f"{s['walk_min']}-min walk to campus")
    hits = [a for a in v_nice if a in s["amenities"]]
    score += 6 * len(hits)
    why += [f"Has {a.lower()}" for a in hits]
    if s["status"] == "contact_at_8am":
        score += 6; why.append("Passed BearDen's trust screening")
    return max(5, min(score, 97)), why


def verdict(s):
    """Plain-language verdict shown before any score."""
    if s["status"] == "blocked":
        return "🛑 Likely scam · Don't send money"
    parts = ["✅ Safe so far" if s["status"] == "contact_at_8am" else "⚠️ Verify first"]
    parts.append("Good value" if true_cost(s)[4] <= budget else "Over budget")
    parts.append(f"{s['walk_min']} min to campus")
    return " · ".join(parts)

STATUS_STYLE = {
    "blocked": ("🛑 Likely scam", "#FDE8E8", "#B42318"),
    "verify_first": ("⚠️ Fo will verify", "#FEF4E6", "#B54708"),
    "contact_at_8am": ("✅ Passed screening", "#E7F6EC", "#067647"),
    "over_budget": ("💸 Over budget", "#F1F3F6", "#475467"),
}


def pill(status):
    label, bg, fg = STATUS_STYLE[status]
    return f'<span class="bd-pill" style="background:{bg};color:{fg}">{label}</span>'


tabL, tabB, tabD, tab0, tab1, tab2, tab3 = st.tabs(["🔍 Is this legit?", "🏠 Browse", "💗 My Den", "🌙 Overnight", "1 · Check a listing", "2 · Log Fo's conversation", "3 · Ask BearDen"])

with tabL:
    import re as _re2
    from overnight import screen as _screen, money_at_risk
    st.subheader("🔍 Is this listing legit?")
    st.caption("Paste a link or the listing text from Facebook, Craigslist, a group chat, or a friend. Get a verdict in seconds.")
    pasted = st.text_area("Listing", height=140, key="pasted",
        placeholder="https://facebook.com/marketplace/...  or paste the post: 'Sunny room on Channing, $1,100. I'm overseas so can't show it, send $800 deposit by Zelle to hold. Text (510) 555-0142'")
    if st.button("Check it", type="primary", key="check_legit") and pasted.strip():
        phone = _re2.search(r"\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}", pasted)
        email = _re2.search(r"[\w.+-]+@[\w-]+\.[\w.]+", pasted)
        rent = _re2.search(r"\$\s?(\d[\d,]{2,})", pasted)
        lst = dict(address="Pasted listing", title="", description=pasted,
                   rent=f"${rent.group(1)}" if rent else "", landlord="(from post)", company="",
                   contact=(phone or email).group(0) if (phone or email) else "", source="Pasted")
        s = _screen(lst, int(budget))
        st.session_state["last_check"] = (s, money_at_risk(lst))
    if "last_check" in st.session_state:
        s, risk = st.session_state["last_check"]
        if s["status"] == "blocked":
            st.error(f"## 🛑 Likely scam. Don't send money.\nYou just kept your **${risk:,}**.")
        elif s["status"] == "verify_first":
            st.warning("## ⚠️ Some warning signs. Let Fo verify the landlord before you pay anything.")
        else:
            st.success("## ✅ No red flags found. BearDen can have Fo ask your questions.")
        for f in s["flags"]:
            st.write(("🌐 " if f.startswith("Flagged by another") else "🚩 ") + f)
        st.caption("A warning isn't proof of fraud, and no flags doesn't guarantee safety. Fo can verify.")

        st.markdown("---")
        st.markdown("#### Want BearDen to keep watching for you? 3 quick questions")
        q1, q2, q3 = st.columns(3)
        q1.radio("When do you need to move?", ["In 2 weeks", "Next month", "Next fall"], key="urgency")
        q2.number_input("Max all-in rent ($)", 600, 3000, 1400, 50, key="qs_budget")
        q3.selectbox("Favorite neighborhood", ["Southside", "Northside", "Downtown"], key="qs_hood")
        if st.session_state.get("urgency", "In 2 weeks") != "Next fall":
            st.info("⚡ Urgent mode: Fo contacts landlords right away and follows up after 2 hours, not 24.")
        if st.button("Start my overnight agent", key="qs_go"):
            try:
                memory.save_student_profile(student, f"Move: {st.session_state['urgency']}. Max all-in ${st.session_state['qs_budget']}. Prefers {st.session_state['qs_hood']}.")
                st.success("Saved to your private memory. Check 🌙 Overnight tomorrow morning.")
            except Exception as e:
                st.warning(f"Preferences applied (memory save failed: {e})")

with tabB:
    from overnight import load_feed, screen
    rows = [screen(l, int(budget)) for l in load_feed()]

    def keep(s):
        rent = int("".join(c for c in s["rent"] if c.isdigit()) or 0)
        return (rent <= budget or s["status"] == "blocked") and s["neighborhood"] in f_hoods \
            and s["room_type"] in f_types and s["walk_min"] <= f_walk and s["move_in"] in f_move \
            and all(a in s["amenities"] for a in f_amen) \
            and not (f_safe and s["status"] == "blocked") \
            and not (f_trust and s["status"] != "contact_at_8am")

    shown = [s for s in rows if keep(s)]
    shown.sort(key=lambda s: -(match(s)[0] or -1))
    blocked_n = sum(1 for s in rows if s["status"] == "blocked")
    m1, m2, m3 = st.columns(3)
    m1.metric("Listings matching your filters", len(shown))
    m2.metric("Scams caught", blocked_n)
    m3.metric("Sources watched", len({s["source"] for s in rows}))

    cols = st.columns(3)
    for i, s in enumerate(shown):
        with cols[i % 3]:
            st.image(s["photos"][0], use_container_width=True)
            sc, why = match(s)
            st.markdown(f"**{verdict(s)}**")
            chips = "".join(f'<span class="bd-chip">{a}</span>' for a in s["amenities"])
            st.markdown(
                f'<div class="bd-card"><div class="bd-price">{s["rent"]}/mo</div>'
                f'<b>{s["title"]}</b><div class="bd-meta">{s["address"]} · {s["neighborhood"]} · '
                f'{s["room_type"]} · 🚶 {s["walk_min"]} min · Move-in {s["move_in"]}</div>'
                f'{pill(s["status"])}<span class="bd-chip">via {s["source"]}</span><br>{chips}</div>',
                unsafe_allow_html=True)
            with st.expander("Details & trust report"):
                if len(s["photos"]) > 1:
                    st.image(s["photos"][1], use_container_width=True)
                st.write(s["description"])
                st.caption(f'{s["beds"]} bd · {s["baths"]} ba · Landlord: {s["landlord"]}'
                           + (f' ({s["company"]})' if s["company"] else ""))
                if s["flags"]:
                    for f in s["flags"]:
                        st.write(f"🚩 {f}")
                else:
                    st.write("✅ No red flags found")
                st.markdown(f"**Match: {sc}/100**" if sc is not None else "**No match score**")
                st.markdown("**Why BearDen ranks it this way**")
                for w in why:
                    st.write(f"· {w}")
                r_, u_, n_, p_, t_ = true_cost(s)
                st.markdown(f"**True monthly cost: ${t_:,}**  \nRent ${r_:,} + utilities ~${u_} + internet ${n_} + parking ${p_}")
                if s["status"] != "blocked":
                    if s["address"] in st.session_state["den"]:
                        st.caption("💗 In My Den")
                    elif st.button("💗 Save to My Den", key=f"save_{i}"):
                        st.session_state["den"].append(s["address"])
                        st.rerun()
                else:
                    st.caption("Can't save: likely scam")
                if s["status"] != "blocked" and st.button("📲 Send to Fo", key=f"fo_{i}"):
                    from fo_send import send_to_fo
                    ok, msg = send_to_fo(build_fo_task(s, student, "", urgent))
                    (st.success if ok else st.error)(msg)
    if not shown:
        st.info("No listings match these filters. Try widening them.")

with tabD:
    from overnight import load_feed as _lf, screen as _sc
    by_addr = {l["address"]: _sc(l, int(budget)) for l in _lf()}
    den = st.session_state["den"]
    st.subheader("💗 My Den: your saved apartments, ranked")
    if not den:
        st.info("Save apartments from Browse with 💗 to rank them here.")
    for rank, addr in enumerate(den):
        s = by_addr[addr]
        c1, c2, c3, c4 = st.columns([1, 2, 5, 2])
        c1.markdown(f"## #{rank + 1}")
        c2.image(s["photos"][0], use_container_width=True)
        sc, _ = match(s)
        c3.markdown(f'**{s["title"]}**  \n{s["address"]} · {sc}% match · True cost ${true_cost(s)[4]:,}/mo')
        c3.markdown(pill(s["status"]), unsafe_allow_html=True)
        if c4.button("⬆️", key=f"up_{addr}", disabled=rank == 0):
            den[rank - 1], den[rank] = den[rank], den[rank - 1]; st.rerun()
        if c4.button("⬇️", key=f"dn_{addr}", disabled=rank == len(den) - 1):
            den[rank + 1], den[rank] = den[rank], den[rank + 1]; st.rerun()

    if den:
        st.markdown("---")
        st.subheader("📝 Toured a place? 3-tap check-in")
        st.caption("Give to get: one check-in unlocks full verified reports from other students.")
        ck = st.session_state.setdefault("checkins", {})
        pick = st.selectbox("Which place did you tour?", den, key="ck_pick")
        a1, a2, a3 = st.columns(3)
        r1 = a1.radio("Matched the listing?", ["Yes", "Mostly", "No"], key="ck1", horizontal=True)
        r2 = a2.radio("Landlord responsive?", ["Yes", "No"], key="ck2", horizontal=True)
        r3 = a3.radio("Would you live there?", ["Yes", "Maybe", "No"], key="ck3", horizontal=True)
        if st.button("Submit check-in", key="ck_go"):
            ck[pick] = dict(matched=r1, responsive=r2, live=r3)
            try:
                memory.save_debrief(student, by_addr[pick] | {"contact": by_addr[pick]["contact"]},
                    f"Post-tour check-in by a student: matched listing={r1}, landlord responsive={r2}, would live there={r3}.")
            except Exception:
                pass
            st.success("Thanks! Full verified reports unlocked.")
        st.markdown("#### 🔎 Verified reports")
        if not ck:
            st.info("🔒 Locked. Submit one check-in to see what other students found on their tours.")
        else:
            for addr in den:
                s = by_addr[addr]
                with st.expander(f"🔓 {addr}: verified report"):
                    st.write(verdict(s))
                    if addr in ck:
                        c = ck[addr]
                        st.write(f"🧑‍🎓 Student check-in: matched listing **{c['matched']}** · landlord responsive **{c['responsive']}** · would live there **{c['live']}**")
                    else:
                        st.write("🧑‍🎓 No tour check-ins yet. Be the first.")
                    for f in s["flags"]:
                        st.write(f"🚩 {f}")
                    if not s["flags"]:
                        st.write("✅ No red flags from screening")

    if len(den) >= 2:
        st.markdown("---")
        st.subheader("🤔 This or That?")
        st.caption("Pick where you'd rather live. Your choice moves up in your ranking.")
        i = st.session_state.get("tot_i", 0) % (len(den) - 1)
        a, b = by_addr[den[i]], by_addr[den[i + 1]]
        ca, cb = st.columns(2)
        for col, s, other, key in ((ca, a, b, "A"), (cb, b, a, "B")):
            with col:
                st.image(s["photos"][0], use_container_width=True)
                st.markdown(f'**{s["title"]}**  \n{s["neighborhood"]} · ${true_cost(s)[4]:,}/mo all-in · {", ".join(s["amenities"][:2])}')
                if st.button(f"Choose {key}", key=f"tot_{key}", use_container_width=True):
                    w, l = den.index(s["address"]), den.index(other["address"])
                    if w > l:
                        den[w], den[l] = den[l], den[w]
                    st.session_state["tot_i"] = i + 1
                    st.rerun()

with tab0:
    st.subheader("Go to sleep looking for housing. Wake up with safe options lined up.")
    if urgent:
        st.caption("⚡ Urgent mode is on: Fo reaches out right away and follows up after 2 hours.")
    if st.button("🌙 Run tonight's agent", type="primary"):
        import time
        from overnight import run_overnight, money_at_risk
        result = run_overnight(student, int(budget), urgent)
        result["kept"] = sum(money_at_risk(s) for s in result["blocked"])
        steps = st.empty()
        timeline = [
            f"🌙 11:00 PM: Watching listing sources... found **{result['found']}** new listings",
            f"🔍 2:00 AM: Screened every listing against red-flag rules and other students' agents. Blocked **{len(result['blocked'])}**",
            f"✋ 7:55 AM: Fo drafted messages to **{len(result['queued'])}** landlords and is **waiting for your OK**",
            "☀️ 8:00 AM: Morning report ready",
        ]
        shown = []
        for line in timeline:
            shown.append(line)
            steps.markdown("\n\n".join(shown))
            time.sleep(1.0)
        st.session_state["night"] = result
        st.session_state.pop("approved", None)

    result = st.session_state.get("night")
    if result:
        net = [s for s in result["blocked"] if any(f.startswith("Flagged by another") for f in s["flags"])]
        # Lock-screen notification
        st.markdown(f"""
<div style="max-width:420px;margin:18px auto;padding:22px;border-radius:28px;
background:linear-gradient(160deg,#0b1f3a,#003262);color:#fff;font-family:-apple-system,Inter,sans-serif">
  <div style="text-align:center;font-size:44px;font-weight:300">8:00</div>
  <div style="text-align:center;opacity:.8;margin-bottom:14px">Tuesday</div>
  <div style="background:rgba(255,255,255,.16);border-radius:16px;padding:12px 14px">
    <div style="font-size:12px;opacity:.85">🐻 BEARDEN · now</div>
    <div style="font-weight:600">Your housing report is ready</div>
    <div style="font-size:14px">{len(result['blocked'])} scams blocked (kept ${result['kept']:,}) · {len(result['queued'])} landlords ready to contact. Tap to approve.</div>
  </div>
</div>""", unsafe_allow_html=True)

        # Approval card
        st.markdown("### ✋ Fo is waiting for your OK")
        st.write(f"Fo wants to contact **{len(result['queued'])} landlords** from its own number. Your phone and email stay private.")
        for addr, task in result["fo_tasks"].items():
            with st.expander(f"Preview message: {addr}"):
                st.code(task, language=None)
        if st.session_state.get("approved"):
            st.success("Approved. Fo is contacting landlords now.")
        elif st.button(f"✅ Approve & send to {len(result['queued'])} landlords", type="primary"):
            from fo_send import send_to_fo
            for addr, task in result["fo_tasks"].items():
                ok, msg = send_to_fo(task)
                (st.success if ok else st.error)(f"{addr}: {msg}")
            st.session_state["approved"] = True

        # Morning report
        st.markdown("### ☀️ Your morning report")
        c1, c2, c3 = st.columns(3)
        c1.metric("New listings checked", result["found"])
        c2.metric("Scams blocked", len(result["blocked"]))
        c3.metric("Money kept", f"${result['kept']:,}")
        for s in net:
            st.info(f"🌐 **{s['address']}** was flagged by another student's agent: "
                    + next(f for f in s["flags"] if f.startswith("Flagged by another")).split(": ", 1)[1])
        for s in result["screened"]:
            with st.expander(f"{verdict(s)}  ·  {s['address']} · {s['rent']}  ({s['source']})"):
                if s.get("photos"):
                    st.image(s["photos"][0], width=360)
                st.write(s["description"])
                for f in s["flags"]:
                    st.write(f"- 🚩 {f}")

with tab1:
    c1, c2 = st.columns(2)
    address = c1.text_input("Address", "2400 Durant Ave #3")
    rent = c1.text_input("Rent", "$1,350")
    landlord = c2.text_input("Landlord name", "Mark")
    company = c2.text_input("Management company", "")
    contact = st.text_input("Landlord phone or email", "(510) 555-0142")
    listing = dict(address=address, rent=rent, landlord=landlord, company=company, contact=contact)
    st.session_state["listing"] = listing

    if st.button("Check BearDen memory", type="primary"):
        hits = memory.lookup_contact(contact)
        if hits:
            st.error(f"⚠️ This contact has been seen before, {len(hits)} time(s):")
            for h in hits:
                st.write(f"- {h['when']}: listed as **{h['address']}** under the name **{h['landlord']}**")
        else:
            st.info("New contact. No history yet.")
        with st.spinner("Searching shared landlord memory..."):
            known = memory.ask_shared(
                f"What do we know about landlord {landlord}, company {company or 'n/a'}, "
                f"contact {contact}, or address {address}? Include utilities, lease terms, "
                f"subleasing, deposits, how they respond, and any red flags."
            )
        st.session_state["known"] = known
        st.markdown("**What BearDen already knows:**")
        st.write(known)

    st.markdown("---")
    task = build_fo_task(listing, student, st.session_state.get("known", ""), urgent)
    st.markdown("**Task for Fo**")
    st.code(task, language=None)
    if st.button("📲 Send to Fo", type="primary", key="send_single"):
        from fo_send import send_to_fo
        ok, msg = send_to_fo(task)
        (st.success if ok else st.error)(msg)

with tab2:
    listing = st.session_state.get("listing", {})
    st.write(f"Logging conversation for **{listing.get('address', '—')}** ({listing.get('contact', '—')})")
    convo = st.text_area("Paste the conversation Fo reported", height=220,
                         placeholder="Fo: Hi, is the unit still available?\nLandlord: Yes but I'm overseas, can't show it. Send $800 deposit by Zelle to hold...")
    if st.button("Debrief → shared memory", type="primary"):
        with st.spinner("Extracting entities and red flags into the knowledge graph..."):
            memory.save_debrief(student, listing, convo)
        st.success("Learned. Every student's agent can now use this.")

with tab3:
    q = st.text_input("Ask", "Is this landlord safe to rent from, and what will my real monthly cost be?")
    if st.button("Ask"):
        with st.spinner("Thinking with private + shared memory..."):
            st.write(memory.ask_for_student(student, q))
