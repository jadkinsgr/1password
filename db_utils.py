import os
import psycopg2

def connect_to_db():
    conn = psycopg2.connect(
        host=os.environ["DATABASE_HOST"],
        dbname=os.environ["DATABASE_NAME"],
        user=os.environ["DATABASE_USER"],
        password=os.environ["DATABASE_PASSWORD"],
    )
    cur = conn.cursor()
    return conn, cur

def create_tables(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS recent_changes (
            id SERIAL PRIMARY KEY,
            kind TEXT,
            change_key TEXT,
            data JSON
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id SERIAL PRIMARY KEY,
            key TEXT UNIQUE,
            data JSON
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS works (
            id SERIAL PRIMARY KEY,
            key TEXT UNIQUE,
            data JSON
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS authors (
            id SERIAL PRIMARY KEY,
            key TEXT UNIQUE,
            data JSON
        );
    """)