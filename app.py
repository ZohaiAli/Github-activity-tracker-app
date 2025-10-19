
import streamlit as st
import requests
from datetime import datetime
from collections import Counter
import matplotlib.pyplot as plt
import pandas as pd
import time

# -------------------------------
# App Configuration & Modern Theme
# -------------------------------
st.set_page_config(page_title="GitHub Pro Dashboard", page_icon="🐙", layout="wide")

st.markdown("""
    <style>
    body {
        background: #0a0f1a;
        color: #e6eef8;
        font-family: 'Inter', sans-serif;
    }
    .stApp {
        background: radial-gradient(circle at top left, #101932, #050910);
    }
    .main-title {
        font-size: 42px;
        font-weight: 800;
        background: linear-gradient(90deg, #60a5fa, #a78bfa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .sub-title {
        color: #94a3b8;
        font-size: 16px;
        margin-bottom: 20px;
    }
    .card {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.08);
        backdrop-filter: blur(14px);
        padding: 20px;
        border-radius: 14px;
        transition: all 0.2s ease-in-out;
    }
    .card:hover {
        border-color: rgba(255,255,255,0.15);
        transform: translateY(-2px);
    }
    .metric {
        font-size: 24px;
        font-weight: 700;
        color: #ffffff;
    }
    .label {
        font-size: 13px;
        color: #a0aec0;
        margin-top: -4px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='main-title'>🐙 GitHub Pro Dashboard</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>Analyze your GitHub profile — repositories, activity, PRs, and more.</div>", unsafe_allow_html=True)

# -------------------------------
# User Input + Sidebar
# -------------------------------
col_input1, col_input2 = st.columns([3, 1])
with col_input1:
    username = st.text_input("👤 GitHub Username", placeholder="e.g. ZohaibAli", label_visibility="collapsed")
with col_input2:
    show = st.button("🚀 Load Dashboard", use_container_width=True)

st.sidebar.header("⚙️ Settings")
refresh = st.sidebar.slider("Auto-refresh interval (sec)", 30, 300, 60)
st.sidebar.caption("Tip: Lower interval for live updates. May hit GitHub rate limits.")

HEADERS = {}

# -------------------------------
# Helper Function
# -------------------------------
def fetch_json(url, params=None):
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=15)
        if r.status_code == 200:
            return r.json()
        elif r.status_code == 403:
            st.error("🚫 API rate limit reached. Try again later.")
        elif r.status_code == 404:
            st.error("❌ User not found.")
        else:
            st.error(f"GitHub API Error {r.status_code}")
    except requests.RequestException as e:
        st.error(f"Network error: {e}")
    return None

def short_repo_url(repo_url):
    return "/".join(repo_url.split("/")[-2:])

# -------------------------------
# Dashboard Logic
# -------------------------------
if show:
    if not username.strip():
        st.warning("Please enter a valid GitHub username.")
        st.stop()

    # API Endpoints
    user_url = f"https://api.github.com/users/{username}"
    repos_url = f"https://api.github.com/users/{username}/repos?type=owner&per_page=100"
    events_url = f"https://api.github.com/users/{username}/events/public"

    with st.spinner("🔄 Fetching user data..."):
        user = fetch_json(user_url)
        if not user:
            st.stop()

    repos = fetch_json(repos_url) or []
    events = fetch_json(events_url) or []

    # -------------------------------
    # Profile Section
    # -------------------------------
    st.markdown("### 👤 Profile Overview")
    col1, col2, col3 = st.columns([1, 2, 2])
    with col1:
        st.image(user["avatar_url"], width=120)
    with col2:
        st.markdown(f"**{user.get('name', username)}**")
        st.write(f"📍 {user.get('location', '—')}")
        st.write(f"🧠 {user.get('bio', '—')}")
    with col3:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.write(f"**Followers:** {user.get('followers', 0)}")
        st.write(f"**Following:** {user.get('following', 0)}")
        st.write(f"**Public Repos:** {user.get('public_repos', 0)}")
        st.markdown('</div>', unsafe_allow_html=True)

    st.divider()

    # -------------------------------
    # Repositories Overview
    # -------------------------------
    st.subheader("📦 Repositories")

    if repos:
        repo_df = pd.DataFrame([
            {
                "Name": r["name"],
                "⭐ Stars": r["stargazers_count"],
                "🍴 Forks": r["forks_count"],
                "Last Updated": r["updated_at"][:10],
                "Description": r["description"] or ""
            } for r in repos
        ])
        st.dataframe(repo_df, use_container_width=True, hide_index=True)

        lang_counter = Counter()
        with st.spinner("Analyzing language usage..."):
            for r in repos:
                lang_url = r.get("languages_url")
                if lang_url:
                    lang_data = fetch_json(lang_url)
                    if lang_data:
                        for lang, bytes_count in lang_data.items():
                            lang_counter[lang] += bytes_count
                    time.sleep(0.05)

        if lang_counter:
            st.markdown("### 💻 Language Breakdown")
            sorted_langs = sorted(lang_counter.items(), key=lambda x: x[1], reverse=True)
            langs, vals = zip(*sorted_langs[:10])
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.barh(langs[::-1], vals[::-1])
            ax.set_xlabel("Bytes of Code")
            ax.set_title("Top 10 Languages")
            st.pyplot(fig)
        else:
            st.info("No language data available.")
    else:
        st.warning("No public repositories found.")

    st.divider()

    # -------------------------------
    # Recent Activity
    # -------------------------------
    st.subheader("📅 Recent Activity")

    if events:
        dates = [datetime.fromisoformat(e["created_at"].replace("Z", "+00:00")).date() for e in events]
        types = [e["type"].replace("Event", "") for e in events]
        c_by_day = Counter(dates)
        c_by_type = Counter(types)

        fig1, ax1 = plt.subplots(figsize=(8, 3))
        ax1.bar(sorted(c_by_day.keys()), [c_by_day[d] for d in sorted(c_by_day.keys())])
        ax1.set_title("Events per Day")
        st.pyplot(fig1)

        fig2, ax2 = plt.subplots(figsize=(4, 4))
        ax2.pie(c_by_type.values(), labels=c_by_type.keys(), autopct="%1.1f%%")
        ax2.set_title("Event Types Distribution")
        st.pyplot(fig2)

    else:
        st.info("No public events found.")

    st.divider()

    # -------------------------------
    # PRs & Issues Today
    # -------------------------------
    st.subheader("🔎 Today's Pull Requests & Issues")

    today = datetime.utcnow().date().isoformat()
    pr_q = f"https://api.github.com/search/issues?q=author:{username}+type:pr+created:{today}"
    issue_q = f"https://api.github.com/search/issues?q=author:{username}+type:issue+created:{today}"

    pr_data = fetch_json(pr_q)
    issue_data = fetch_json(issue_q)

    if pr_data and pr_data.get("total_count", 0) > 0:
        st.write("**Pull Requests Created Today:**")
        for pr in pr_data["items"][:10]:
            st.markdown(f"- [{pr['title']}]({pr['html_url']}) — `{short_repo_url(pr['repository_url'])}`")
    else:
        st.caption("No PRs created today.")

    if issue_data and issue_data.get("total_count", 0) > 0:
        st.write("**Issues Created Today:**")
        for issue in issue_data["items"][:10]:
            st.markdown(f"- [{issue['title']}]({issue['html_url']}) — `{short_repo_url(issue['repository_url'])}`")
    else:
        st.caption("No issues created today.")

    st.success("✅ Dashboard Loaded Successfully!")

else:
    st.info("Enter a GitHub username and click **Load Dashboard 🚀** to get started.")
