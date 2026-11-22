import json
from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Tarang AI | Portfolio Command Center", page_icon="🧭", layout="wide")
DATA_DIR = Path(__file__).parent / "data"

@st.cache_data
def load_data():
    clients = pd.read_csv(DATA_DIR / "clients.csv")
    inbox = pd.read_csv(DATA_DIR / "inbox_records.csv")
    crm = pd.read_csv(DATA_DIR / "crm_notes.csv")
    return clients, inbox, crm

clients, inbox, crm = load_data()

def analyse_text(text):
    t = str(text).lower()
    negative = ["frustrated", "disappointed", "ignored", "waiting to be paid", "not generated", "missing", "failure", "blocked", "unresolved", "again"]
    positive = ["thank you", "resolved", "working well", "appreciate"]
    neg = sum(word in t for word in negative)
    pos = sum(word in t for word in positive)
    sentiment = "Negative" if neg >= 2 else ("Positive" if pos else "Neutral")
    recurring = any(word in t for word in ["third occurrence", "third time", "again", "previously", "similar issues", "reported previously"])
    return sentiment, recurring

def assess(row, client_map):
    t = str(row["raw_text"]).lower()
    severity = str(row.get("stated_severity", "medium")).lower()
    impact = 5 if any(x in t for x in ["40 suppliers", "waiting to be paid", "invoices have not generated", "blocked"]) else 4 if any(x in t for x in ["third occurrence", "third time", "renewal", "leadership visit", "ignored for ten days"]) else 3 if severity == "high" else 2
    urgency = 5 if any(x in t for x in ["since saturday", "waiting to be paid", "nine days", "third occurrence"]) else 4 if any(x in t for x in ["next week", "ten days", "wednesday"]) else 3 if severity == "high" else 2
    relationship = 5 if any(x in t for x in ["disappointed", "ignored", "waiting to be paid", "leadership visit"]) else 4 if "renewal" in t else 3
    client = client_map.get(str(row["client_id"]), {})
    acv = float(client.get("annual_contract_value_inr", 0))
    commercial = 5 if acv >= 10_000_000 else 4 if acv >= 8_000_000 else 3 if acv >= 5_000_000 else 2
    sentiment, recurring = analyse_text(t)
    recurrence = 5 if recurring else 4 if int(row.get("age_days", 0)) >= 7 else 2
    score = .30*impact + .25*urgency + .20*relationship + .15*commercial + .10*recurrence
    priority = "Critical" if score >= 4.2 else ("High" if score >= 3.4 else ("Medium" if score >= 2.5 else "Low"))
    return pd.Series([impact, urgency, relationship, commercial, recurrence, round(score,2), priority, sentiment, recurring])

def recommendation(row):
    category = str(row["issue_category"]).lower()
    if "invoice" in category:
        return "Escalate invoice-generation incident; validate backlog and prevent duplicate invoices."
    if "order update" in category or "order status" in category:
        return "Assign technical owner; investigate logs and implement a permanent fix, not another restart."
    if "renewal" in category:
        return "Contact decision-maker today; clarify objections and agree a decision timeline."
    if "unanswered support" in category:
        return "Acknowledge publicly, move details to a private channel and assign a named support owner."
    if "executive" in category or "unresolved" in category:
        return "Prepare an issue-by-issue recovery plan with owners and target dates before the leadership visit."
    if "demo" in category:
        return "Confirm use case and attendees; prepare a focused demo with the Solution Consultant."
    return "Confirm impact with the account owner, assign a next action and record the next update time."

client_map = clients.set_index("client_id").to_dict("index")
scored = inbox.copy()
scored[["impact","urgency","relationship_risk","commercial_exposure","recurrence","score","priority","sentiment","recurring"]] = scored.apply(lambda r: assess(r, client_map), axis=1)
scored["recommended_action"] = scored.apply(recommendation, axis=1)
scored = scored.sort_values(["score","age_days"], ascending=[False,False]).reset_index(drop=True)
scored.insert(0, "rank", range(1, len(scored)+1))

st.title("🧭 Tarang AI — Portfolio Command Center")
st.caption("Lightweight weekly client triage | Synthetic demonstration data | Human approval required")
st.info("This simplified version runs without an API key, paid credits or external AI service. Classification and recommendations use transparent local rules and keyword matching; they are not LLM-generated.")

total_acv = clients["annual_contract_value_inr"].sum()
critical_high = int(scored["priority"].isin(["Critical","High"]).sum())
m1,m2,m3,m4 = st.columns(4)
m1.metric("Clients monitored", f"{clients.client_id.nunique()}")
m2.metric("Records analysed", f"{len(scored)}")
m3.metric("Critical / high items", f"{critical_high}")
m4.metric("Synthetic portfolio ACV", f"₹{total_acv/1e7:.2f} Cr")

tabs = st.tabs(["Priority queue","Client portfolio","Issue insights","Weekly brief","Methodology"])

with tabs[0]:
    st.subheader("Ranked action queue")
    st.caption("Scores are deterministic decision-support indicators, not probabilities. Apply human judgement to critical incidents and deadlines.")
    display = scored[["rank","priority","client_name","source_type","issue_category","age_days","score","sentiment","recurring"]].copy()
    display.columns = ["Rank","Priority","Client","Source","Issue","Age (days)","Score / 5","Sentiment","Recurring signal"]
    st.dataframe(display, use_container_width=True, hide_index=True)
    selected = st.selectbox("Inspect a record", scored["record_id"].tolist())
    row = scored[scored.record_id == selected].iloc[0]
    st.markdown(f"**{row.client_name} — {row.issue_category}**")
    st.write(row.raw_text)
    st.write(f"**Priority:** {row.priority} | **Score:** {row.score}/5 | **Sentiment:** {row.sentiment} | **Recurring signal:** {'Yes' if row.recurring else 'No'}")
    st.success(f"Recommended next action: {row.recommended_action}")
    st.download_button("Download ranked queue CSV", scored.to_csv(index=False).encode("utf-8"), "tarang_ranked_queue.csv", "text/csv")

with tabs[1]:
    st.subheader("Client portfolio")
    portfolio = clients.merge(crm[["client_id","open_opportunities_inr","last_qbr_date"]], on="client_id", how="left")
    counts = scored.groupby("client_id").size().rename("Inbox records")
    portfolio = portfolio.merge(counts, on="client_id", how="left").fillna({"Inbox records":0})
    portfolio["ACV (₹ L)"] = (portfolio.annual_contract_value_inr/100000).round(1)
    portfolio["Open opportunity (₹ L)"] = (portfolio.open_opportunities_inr/100000).round(1)
    st.dataframe(portfolio[["client_name","industry","ACV (₹ L)","account_health","Inbox records","Open opportunity (₹ L)","last_qbr_date"]], use_container_width=True, hide_index=True)
    st.bar_chart(portfolio.set_index("client_name")["ACV (₹ L)"])
    st.caption("Portfolio values include synthetic demonstration accounts. Do not present the total as the case's stated ₹3.40 Cr existing ACV.")

with tabs[2]:
    st.subheader("Issue and sentiment insights")
    a,b,c = st.columns(3)
    a.metric("Negative-sentiment records", int((scored.sentiment=="Negative").sum()))
    b.metric("Recurring-issue signals", int(scored.recurring.sum()))
    c.metric("Open records older than 7 days", int((scored.age_days>7).sum()))
    st.markdown("**Recurring issue signals**")
    recurring_rows = scored[scored.recurring]
    if len(recurring_rows):
        st.dataframe(recurring_rows[["client_name","issue_category","age_days","raw_text"]], use_container_width=True, hide_index=True)
    else:
        st.write("No recurring signals detected.")
    st.markdown("**Negative sentiment records**")
    negative_rows = scored[scored.sentiment=="Negative"]
    if len(negative_rows):
        st.dataframe(negative_rows[["client_name","issue_category","sentiment","raw_text"]], use_container_width=True, hide_index=True)
    else:
        st.write("No negative sentiment signals detected.")

with tabs[3]:
    st.subheader("Weekly management brief")
    st.markdown("### Top five items requiring attention")
    for _, row in scored.head(5).iterrows():
        st.markdown(f"**{row.priority} · {row.client_name}** — {row.issue_category} (score {row.score}/5; record {row.record_id})")
        st.caption(row.recommended_action)
    st.markdown("### Suggested operating actions")
    st.markdown("- Confirm scope and customer impact before communicating resolution.")
    st.markdown("- Assign a named owner and next-update time to every high-priority item.")
    st.markdown("- Validate renewal dates and commercial terms in CRM.")
    st.markdown("- Review recommendations before communicating with clients.")
    brief = ["TARANG AI — WEEKLY PORTFOLIO BRIEF","", "Top five priorities:"]
    for _, row in scored.head(5).iterrows():
        brief.append(f"- {row.priority} | {row.client_name} | {row.issue_category} | {row.recommended_action} | Evidence: {row.record_id}")
    st.download_button("Download weekly brief", "\n".join(brief).encode("utf-8"), "tarang_weekly_brief.txt")

with tabs[4]:
    st.subheader("Methodology and safeguards")
    st.markdown("""
**Data:** All 12 client accounts and inbox records are synthetic demonstrations.

**Priority score (illustrative):**
- Business impact: 30%
- Urgency: 25%
- Relationship risk: 20%
- Commercial exposure: 15%
- Recurrence / duration: 10%

Each dimension is scored 1–5. The weighted score is not a probability of churn or incident severity.

**Local automation:** Keyword-based sentiment cues, recurring-issue flags, deterministic scoring and templated next-action recommendations. These are transparent heuristics, not genuine AI/LLM inference.

**Human controls:** No client messages are sent, tickets closed, refunds approved or technical changes executed. A manager must validate evidence, override priorities when appropriate and approve all communications.

**Production limitations:** No live Gmail, CRM, ticketing or LinkedIn integrations; no authentication, role-based access or audit logging. Real customer data should only be used with approved security and privacy controls.
""")
    st.download_button("Download clients CSV", clients.to_csv(index=False).encode(), "clients.csv", "text/csv")
    st.download_button("Download inbox CSV", inbox.to_csv(index=False).encode(), "inbox_records.csv", "text/csv")
