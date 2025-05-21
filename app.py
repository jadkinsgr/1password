import requests
import json
from datetime import datetime, timedelta
from db_utils import connect_to_db, create_tables

BASE_URL = "https://openlibrary.org"
KINDS_TO_KEEP = {"add-cover", "add-book", "edit-book", "merge-authors"}

DATE_START = datetime(2023, 12, 1)
DATE_END = datetime(2023, 12, 3)
LIMIT = 1000

def fetch_recent_changes_for_day(date_str):
    results = []
    for kind in KINDS_TO_KEEP:
        offset = 0
        while True:
            url = f"{BASE_URL}/recentchanges/{date_str}/{kind}.json"
            params = {"limit": LIMIT, "offset": offset}
            resp = requests.get(url, params=params)
            if resp.status_code != 200:
                print(f"Error fetching {url}: {resp.status_code}")
                break
            data = resp.json()
            if not data:
                break
            results.extend(data)
            if len(data) < LIMIT:
                break
            offset += LIMIT
    return results

def fetch_book_data(book_key):
    url = f"{BASE_URL}{book_key}.json"
    resp = requests.get(url)
    if resp.status_code == 200:
        return resp.json()
    else:
        print(f"Failed to fetch book data for {book_key}")
        return None

def main():
    conn, cur = connect_to_db()
    create_tables(cur)
    conn.commit()

    current_date = DATE_START
    all_changes = []

    print(f"Starting extraction from {DATE_START.date()} to {DATE_END.date()}")

    while current_date <= DATE_END:
        date_str = current_date.strftime("%Y/%m/%d")
        daily_changes = fetch_recent_changes_for_day(date_str)
        print(f"Fetched {len(daily_changes)} changes for {date_str}")
        all_changes.extend(daily_changes)
        current_date += timedelta(days=1)

    print(f"Inserting {len(all_changes)} recent changes into database...")
    for entry in all_changes:
        kind = entry.get("kind")
        change_key = entry.get("key")
        cur.execute("""
            INSERT INTO recent_changes (kind, change_key, data)
            VALUES (%s, %s, %s)
            ON CONFLICT DO NOTHING;
        """, (kind, change_key, json.dumps(entry)))

    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()