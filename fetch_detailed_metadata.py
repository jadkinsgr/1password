import os
import psycopg2
import requests
import json
from db_utils import connect_to_db

BASE_URL = "https://openlibrary.org"

BOOK_KEY = "/books/OL50210272M"
WORK_KEY = "/works/OL37247684W"

def create_custom_tables(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS book_metadata_detailed (
            id SERIAL PRIMARY KEY,
            key TEXT UNIQUE,
            data JSON
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS work_metadata_detailed (
            id SERIAL PRIMARY KEY,
            key TEXT UNIQUE,
            data JSON
        );
    """)

def fetch_and_store_metadata(cur, conn, key, table):
    url = f"{BASE_URL}{key}.json"
    print(f"Fetching: {url}")
    resp = requests.get(url)
    if resp.status_code != 200:
        print(f"Failed to fetch {url}: {resp.status_code}")
        return

    data = resp.json()
    cur.execute(f"""
        INSERT INTO {table} (key, data)
        VALUES (%s, %s)
        ON CONFLICT (key) DO NOTHING;
    """, (key, json.dumps(data)))
    conn.commit()

def main():
    conn, cur = connect_to_db()
    create_custom_tables(cur)
    conn.commit()

    fetch_and_store_metadata(cur, conn, BOOK_KEY, "book_metadata_detailed")
    fetch_and_store_metadata(cur, conn, WORK_KEY, "work_metadata_detailed")

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()