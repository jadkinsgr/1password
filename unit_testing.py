#Just testing row count
import os
import unittest
import app
from db_utils import connect_to_db

# Set env vars so connect_to_db() works
os.environ["DATABASE_HOST"] = "localhost"
os.environ["DATABASE_NAME"] = "mydatabase"
os.environ["DATABASE_USER"] = "user"
os.environ["DATABASE_PASSWORD"] = "password"

class FunctionalTest(unittest.TestCase):

    def test_recent_changes_populated(self):
        conn, cur = connect_to_db()
        cur.execute("SELECT COUNT(*) FROM recent_changes;")
        count = cur.fetchone()[0]

        print(f"Row count in recent_changes: {count}")
        self.assertGreater(count, 0)

        cur.close()
        conn.close()

if __name__ == "__main__":
    unittest.main()