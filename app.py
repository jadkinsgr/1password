import os
import requests
import time
import psycopg2
from datetime import datetime, timedelta
import json

#Adding Variables for the API# Base URL for the OpenLibrary API
BASE_URL = "https://openlibrary.org"

# Only ingest these kinds as per assignment instructions
KINDS_TO_KEEP = {"add-cover", "add-book", "edit-book", "merge-authors"}

#Adding Date range variables so they can be altered on the fly (or imputed from the user)
# Date range for extraction per assignment (Dec 1 - Dec 3, 2023), note on this one - the assignment says this date range but the example is 2024. So lets assume we want 2023 for the assignment but note it here.
DATE_START = datetime(2023, 12, 1)
DATE_END = datetime(2023, 12, 3)

# Max records per request (API limit)
LIMIT = 1000

# Function to get the last 1000 changes from the OpenLibrary API
def connect_to_db():
    conn = psycopg2.connect(
        host=os.environ["DATABASE_HOST"],
        dbname=os.environ["DATABASE_NAME"],
        user=os.environ["DATABASE_USER"],
        password=os.environ["DATABASE_PASSWORD"],
    )
    cur = conn.cursor()
    cur.execute("SELECT * FROM information_schema.tables;")
    rows = cur.fetchall()
    for row in rows:
        print(row)
    cur.close()
    conn.close()


def create_tables(cur):
    # Step 4a: Create tables to model recent changes and chosen dataset (books)
    # Use JSONB columns to store flexible JSON data from API responses
    cur.execute("""
    CREATE TABLE IF NOT EXISTS recent_changes (
        id SERIAL PRIMARY KEY,
        kind TEXT,
        change_key TEXT,
        data JSONB
    );
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS books (
        id SERIAL PRIMARY KEY,
        key TEXT UNIQUE,
        data JSONB
    );
    """)

def fetch_recent_changes_for_day(date_str):
    # Ingest Recent Changes API data for a given date with pagination and filtering by KINDS_TO_KEEP
    offset = 0
    results = []
    while True:
        url = f"{BASE_URL}/recentchanges/{date_str}.json"
        params = {"limit": LIMIT, "offset": offset}
        resp = requests.get(url, params=params)
        if resp.status_code != 200:
            print(f"Error fetching {url}: {resp.status_code}")
            break
        data = resp.json()
        if not data:
            break
        # Filter to only include changes of desired kinds per assignment instructions
        filtered = [entry for entry in data if entry.get("kind") in KINDS_TO_KEEP]
        results.extend(filtered)
        if len(data) < LIMIT:
            # No more pages to fetch
            break
        offset += LIMIT
    return results

def fetch_book_data(book_key):
    # Use the changes key from recent changes to fetch full book data
    url = f"{BASE_URL}{book_key}.json"
    resp = requests.get(url)
    if resp.status_code == 200:
        return resp.json()
    else:
        print(f"Failed to fetch book data for {book_key}")
        return None

def main():
    # This script is run inside docker container; commit often during development
    conn, cur = connect_to_db()

    # Create tables to load data into Postgres
    create_tables(cur)
    conn.commit()

    current_date = DATE_START
    all_changes = []

    print("Starting data extraction for date range Dec 1 - Dec 3, 2023...")

    while current_date <= DATE_END:
        date_str = current_date.strftime("%Y/%m/%d")
        daily_changes = fetch_recent_changes_for_day(date_str)
        print(f"Fetched {len(daily_changes)} recent changes for {date_str}")
        all_changes.extend(daily_changes)
        current_date += timedelta(days=1)

    # Load filtered recent changes data into Postgres
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

    # Load additional book dataset related to recent changes into Postgres
    print("Fetching and inserting related book data for recent changes...")
    for entry in all_changes:
        change_key = entry.get("key")
        # Only process if key references a book, per assignment directions
        if change_key and change_key.startswith("/books/"):
            book_data = fetch_book_data(change_key)
            if book_data:
                cur.execute("""
                    INSERT INTO books (key, data)
                    VALUES (%s, %s)
                    ON CONFLICT (key) DO NOTHING;
                """, (change_key, json.dumps(book_data)))
    conn.commit()

    print("Data ingestion and loading complete.")
    cur.close()
    conn.close()























if __name__ == "__main__":
    print("Data Engineering Take Home Assessment")
    connect_to_db()
