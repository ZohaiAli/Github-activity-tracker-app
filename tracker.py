import requests
import sqlite3
import time
from datetime import datetime
import matplotlib.pyplot as plt
from collections import Counter

# --- CONFIG ---
USERNAME = "hashmi102"  # ← yahan apna GitHub username daalein
CHECK_INTERVAL = 900  # seconds (900 = 15 minutes)

# --- DATABASE SETUP ---
conn = sqlite3.connect("github_activity.db")
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    event_type TEXT,
    event_time TEXT
)
""")
conn.commit()

def fetch_github_activity(username):
    """Fetch public GitHub events"""
    url = f"https://api.github.com/users/{username}/events/public"
    headers = {"Accept": "application/vnd.github.v3+json"}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        events = response.json()
        return [
            {
                "type": e["type"],
                "created_at": e["created_at"]
            } for e in events
        ]
    else:
        print("⚠️ Error fetching data:", response.status_code)
        return []

def save_activity(username, events):
    """Save new events into database"""
    for e in events:
        cur.execute("SELECT * FROM activity WHERE username=? AND event_time=? AND event_type=?", 
                    (username, e["created_at"], e["type"]))
        if not cur.fetchone():
            cur.execute("INSERT INTO activity (username, event_type, event_time) VALUES (?, ?, ?)",
                        (username, e["type"], e["created_at"]))
            conn.commit()

def show_graph(username):
    """Plot daily activity graph"""
    cur.execute("SELECT event_time FROM activity WHERE username=?", (username,))
    rows = cur.fetchall()
    
    if not rows:
        print("❌ No data to show. Run the tracker first.")
        return
    
    # Convert timestamps to dates
    dates = [datetime.fromisoformat(r[0].replace("Z", "+00:00")).date() for r in rows]
    count_by_day = Counter(dates)

    # Sort by date
    sorted_dates = sorted(count_by_day.keys())
    counts = [count_by_day[d] for d in sorted_dates]

    # Plot graph
    plt.figure(figsize=(10, 5))
    plt.bar(sorted_dates, counts)
    plt.title(f"GitHub Activity for {username}")
    plt.xlabel("Date")
    plt.ylabel("Number of Events")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def main():
    print(f"📡 Tracking GitHub activity for: {USERNAME}")
    while True:
        events = fetch_github_activity(USERNAME)
        save_activity(USERNAME, events)
        print(f"[{datetime.now()}] Saved {len(events)} events. Waiting for next check...")
        show_graph(USERNAME)
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
