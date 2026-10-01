"""Create the main and test databases if they don't exist."""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

conn = psycopg2.connect(host="localhost", user="postgres", password="postgres", port=5432)
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
cur = conn.cursor()

for db_name in ["eve_healthcare", "eve_healthcare_test"]:
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
    if not cur.fetchone():
        cur.execute(f'CREATE DATABASE "{db_name}"')
        print(f"Created database: {db_name}")
    else:
        print(f"Database already exists: {db_name}")

conn.close()
print("Done.")
