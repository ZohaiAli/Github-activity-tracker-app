import streamlit as st
import requests
from datetime import datetime
from collections import Counter
import matplotlib.pyplot as plt
import pandas as pd
import time

# -------------------------
# Streamlit config + styles
# -------------------------
st.set_page_config(page_title="GitHub Pro Dashboard", page_icon="🐙", layout="wide")
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(180deg, #0a0f1a 0%, #0b1630 100%);
        color: #e6eef8;
    }
    .big-title {
        font-size:36px;
        font-weight:700;
        color: #ffffff;
    }
    .sub-title {
        color: #bcd3ff;
        margin-bottom: 12px;
    }
    .card {
        background: #071029;
        padding: 12px;
        border-radius: 8px;
        box-shadow: 0 4px 18px rgba(0,0,0,0.6);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="big-title">GitHub Pro Activity Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Track repositories, followers, PRs, issues & commits — live updates</div>', unsafe_allow_html=True)

# -------------------------
# Top input field (main screen)
# -------------------------
col_input1, col_input2 = st.columns([3, 1])
with col_input1:
    name = st.text_input("👤 Enter GitHub Name:", value="Name", placeholder="e.g. ZohaibAli")
with col_input2:
    show = st.button("Show Dashboard 🚀")

# Sidebar for refresh setting
st.sidebar.header("Settings")
refresh = st.sidebar.slider("Auto-refresh (seconds)", 30, 300, 60)
st.sidebar.info("Adjust refresh interval if you plan to auto-update data.")

HEADERS = {}

# -------------------------
# Helper functions
# -------------------------
def fetch_json(url, params=None):
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=15)
        if r.status_code == 200:
            return r.json()
        elif r.status_code == 403:
            st.error("🚫 API rate limit reached. Wait a few minutes before trying again.")
        elif r.status_code == 404:
            st.error("❌ User not found. Check the name again.")
        else:
            st.error(f"GitHub API error {r.status_code}: {r.text[:200]}")
    except requests.RequestException as e:
        st.error(f"Network error: {e}")
    return None

def short_repo_url(repo_url):
    return "/".join(repo_url.split("/")[-2:])

# -------------------------
# Dashboard main logic
# -------------------------
if show:
    username = name.strip()
    if not username:
        st.warning("Please enter a GitHub name.")
        st.stop()

    # Main API endpoints
    user_url = f"https://api.github.com/users/{username}"
    repos_url = f"https://api.github.com/users/{username}/repos?type=owner&per_page=100"
    events_url = f"https://api.github.com/users/{username}/events/public"

    with st.spinner("Fetching user data..."):
        user = fetch_json(user_url)
    if not user:
        st.stop()

    with st.spinner("Fetching repositories..."):
        repos = fetch_json(repos_url) or []

    with st.spinner("Fetching public events..."):
        events = fetch_json(events_url) or []

    # -------------------------
    # Profile + Quick Stats
    # -------------------------
    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.image(user.get("avatar_url"), width=120)
        st.markdown(f"### {user.get('login')}  ")
        st.markdown(f"**{user.get('name') or ''}**  ")
        st.markdown(f"📍 {user.get('location') or '—'}  ")
        st.markdown(f"📝 {user.get('bio') or '—'}  ")
        st.write(f"**Followers:** {user.get('followers',0)} | **Following:** {user.get('following',0)}")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Quick Stats")
        st.write(f"📦 Public Repositories: **{user.get('public_repos', 0)}**")
        st.write(f"⭐ Total Stars: **{sum(r.get('stargazers_count',0) for r in repos):,}**")
        st.write(f"🔁 Recent Events: **{len(events)}**")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # -------------------------
    # Repository Overview + Languages
    # -------------------------
    st.subheader("📦 Repository Overview")

    if repos:
        repo_rows = []
        for r in repos:
            repo_rows.append({
                "Name": r["name"],
                "Stars": r["stargazers_count"],
                "Forks": r["forks_count"],
                "Updated": r["updated_at"][:10],
                "Description": r["description"] or ""
            })
        st.dataframe(pd.DataFrame(repo_rows), use_container_width=True)

        # Language analysis
        lang_counter = Counter()
        with st.spinner("Fetching languages per repo..."):
            for r in repos:
                lang_url = r.get("languages_url")
                if lang_url:
                    lang_data = fetch_json(lang_url)
                    if lang_data:
                        for lang, bytes_count in lang_data.items():
                            lang_counter[lang] += bytes_count
                    time.sleep(0.05)

        if lang_counter:
            sorted_langs = sorted(lang_counter.items(), key=lambda x: x[1], reverse=True)
            total = sum(lang_counter.values())

            # Bar chart
            fig, ax = plt.subplots(figsize=(8,4))
            top_n = 10
            langs = [l for l,_ in sorted_langs[:top_n]][::-1]
            vals = [v for _,v in sorted_langs[:top_n]][::-1]
            ax.barh(langs, vals)
            ax.set_xlabel("Bytes of code")
            ax.set_title("Top Languages Used (Top 10)")
            st.pyplot(fig)

            # Table with percentages
            table_rows = []
            for i, (lang, val) in enumerate(sorted_langs):
                table_rows.append({
                    "Rank": i+1,
                    "Language": lang,
                    "Bytes": val,
                    "Usage %": f"{(val/total)*100:.2f}%"
                })
            st.write("### 💻 Language Breakdown")
            st.table(pd.DataFrame(table_rows))
        else:
            st.info("No language data available.")
    else:
        st.info("No public repositories found.")

    st.markdown("---")

    # -------------------------
    # Recent Activity
    # -------------------------
    st.subheader("📅 Recent GitHub Activity")
    if events:
        dates = [datetime.fromisoformat(e["created_at"].replace("Z","+00:00")).date() for e in events]
        types = [e["type"].replace("Event","") for e in events]
        c_by_day = Counter(dates)
        c_by_type = Counter(types)

        # Activity per day chart
        fig1, ax1 = plt.subplots(figsize=(8,3))
        ax1.bar(sorted(c_by_day.keys()), [c_by_day[d] for d in sorted(c_by_day.keys())])
        ax1.set_xlabel("Date")
        ax1.set_ylabel("Events")
        ax1.set_title("Activity Timeline")
        st.pyplot(fig1)

        # Event types pie
        fig2, ax2 = plt.subplots(figsize=(4,4))
        ax2.pie(c_by_type.values(), labels=c_by_type.keys(), autopct="%1.1f%%", startangle=140)
        ax2.set_title("Event Types")
        st.pyplot(fig2)

        # Recent events table
        st.markdown("### 🕒 Latest 20 Events")
        event_list = []
        for e in events[:20]:
            etype = e["type"].replace("Event","")
            repo_name = e.get("repo", {}).get("name", "")
            created = datetime.fromisoformat(e["created_at"].replace("Z","+00:00")).strftime("%Y-%m-%d %H:%M:%S")
            msg = ""
            if e["type"] == "PushEvent":
                commits = e.get("payload", {}).get("commits", [])
                if commits:
                    msgs = [c.get("message","").strip() for c in commits][:2]
                    msg = " | ".join(m[:80] for m in msgs)
            event_list.append({"Type": etype, "Repo": repo_name, "Time (UTC)": created, "Notes": msg})
        st.table(pd.DataFrame(event_list))
    else:
        st.info("No public events found.")

    st.markdown("---")

    # -------------------------
    # Today's PRs & Issues
    # -------------------------
    st.subheader("🔎 Today's Pull Requests & Issues")
    today = datetime.utcnow().date().isoformat()
    pr_q = f"https://api.github.com/search/issues?q=author:{username}+type:pr+created:{today}"
    issue_q = f"https://api.github.com/search/issues?q=author:{username}+type:issue+created:{today}"

    pr_data = fetch_json(pr_q)
    issue_data = fetch_json(issue_q)

    if pr_data and pr_data.get("total_count",0) > 0:
        st.write("**Pull Requests created today:**")
        for it in pr_data["items"][:10]:
            st.markdown(f"- [{it['title']}]({it['html_url']}) — `{short_repo_url(it['repository_url'])}`")
    else:
        st.write("No PRs today.")

    if issue_data and issue_data.get("total_count",0) > 0:
        st.write("**Issues created today:**")
        for it in issue_data["items"][:10]:
            st.markdown(f"- [{it['title']}]({it['html_url']}) — `{short_repo_url(it['repository_url'])}`")
    else:
        st.write("No Issues today.")

    st.success("✅ Dashboard loaded successfully!")
else:
    st.info("Enter a GitHub name above and click **Show Dashboard 🚀** to start.")
