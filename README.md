# 🐻 BearDen

**Is this listing legit?** Paste any Berkeley housing listing and get a verdict in seconds. Then BearDen's agents keep hunting, safely, while you sleep.

Built at Agents After Dark (Founder Square, UC Berkeley Haas), Nov 16, 2026.

## Features
- **🔍 Is this legit?** Paste a link or post. You get an instant plain-language verdict, red flags, and the money you kept ("You just kept your $800").
- **🌐 Network effect (Cognee):** "Flagged by another student's agent 10 min ago." Landlord intel is shared across every student's agent, and preferences stay private.
- **⚡ Urgency:** students who need to move in 2 weeks get urgent mode, where Fo reaches out right away and follows up after 2 hours.
- **🌙 Overnight agent:** finds and screens listings, drafts Fo outreach, then sends a lock-screen notification and a morning report.
- **✋ You approve Fo:** "Fo wants to contact 5 landlords. Preview → Approve." Fo uses its own number, so your phone stays private.
- **🏠 Browse:** photos, filters, a verdict first ("✅ Safe so far · Good value · 8 min to campus"), and the score on tap. True monthly cost.
- **💗 My Den:** save, rank, and This or That. Likely scams can't be scored or saved.
- **📝 Give-to-get check-ins:** a 3-tap post-tour check-in unlocks full verified reports.

Sponsor tech: **Cognee Cloud** (shared + private agent memory), **Wajo Fo** (landlord outreach from its own number).

- **Fo (Wajo):** contacts landlords from its own number/email, asks the questions, follows up.
- **Cognee:** shared landlord memory across every student's agent, plus private memory per student.

## Setup (Mac, ~5 min)
```bash
cd bearden
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # then open .env and add your key
streamlit run app.py
```
The first Cognee call is slow (it creates its local databases). Run one "Save profile" before the demo to warm it up.

## Connect Fo to Claude
In the Wajo app, go to Settings → Integrations/MCP and copy the Fo MCP URL. Add it to Claude
(Claude Desktop: Settings → Connectors → Add custom connector; or Claude Code: `claude mcp add --transport http fo <URL>`).
Then in Claude: "Use Fo to do this task:" and paste the task BearDen generates.
Ask Jenny or Lucas on the Wajo Discord if you can't find the MCP URL.

## Demo script (2 min)
Story: *agents that keep you safe through the whole apartment hunt, while you sleep.*
0. Do steps 2–3 below first, so the scammer's number is already in shared memory. Then open the **🌙 Overnight** tab as Student B and click **Run tonight's agent**: 5 listings found, 2 scams blocked (one because Student A's agent already caught that number), 2 queued for Fo at 8am, 1 over budget.
1. Sidebar: **Reset all memory**.
2. Student A checks a listing at 2400 Durant, contact (510) 555-0142. Result: new contact.
3. Fo texts the "landlord" (a teammate), who dodges the tour and asks for a Zelle deposit. Paste that into tab 2 and click **Debrief**.
4. Switch the sidebar to **Student B**. Check a *different* address (2600 Channing) with the **same number**. BearDen flags it instantly and shows what it already knows. Fo never has to contact them.
5. Tab 3: "Is this landlord safe, and what's my real monthly cost?"

Submit at foundersquare.org/submit **and** quote-post the video on @shibani_pi's latest launch post by 8pm.
