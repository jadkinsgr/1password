import os
import requests
import psycopg2
from datetime import datetime, timedelta
import json

BASE_URL = "https://openlibrary.org"
KINDS_TO_KEEP = {"add-cover", "add-book", "edit-book", "merge-authors"}

#dates that were provided in the take home assignment
DATE_START = datetime(2023, 12, 1)
DATE_END = datetime(2023, 12, 3)
LIMIT = 1000

#Passed from docker-compose.yml
def connect_to_db():
    conn = psycopg2.connect(
        host=os.environ["DATABASE_HOST"],
        dbname=os.environ["DATABASE_NAME"],
        user=os.environ["DATABASE_USER"],
        password=os.environ["DATABASE_PASSWORD"],
    )
    cur = conn.cursor()
    return conn, cur

#request one
def create_tables(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS recent_changes (
            id SERIAL PRIMARY KEY,
            kind TEXT,
            change_key TEXT,
            data JSON
        );
    """)
#request two
    cur.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id SERIAL PRIMARY KEY,
            key TEXT UNIQUE,
            data JSON
        );
    """)

#Request three
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

#driver code to execute the functions above - placed into main so that is modular and can be called from other modules if needed
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

    print("Fetching and inserting related book data...")
    for entry in all_changes:
        change_key = entry.get("key")
        if change_key and change_key.startswith("/books/"):
            book_data = fetch_book_data(change_key)
            if book_data:
                cur.execute("""
                    INSERT INTO books (key, data)
                    VALUES (%s, %s)
                    ON CONFLICT (key) DO NOTHING;
                """, (change_key, json.dumps(book_data)))

    conn.commit()

    print("Done.")
    cur.close()
    conn.close()

#executes if called from command line - or can be imported as a module elsewhere
if __name__ == "__main__":
    main()