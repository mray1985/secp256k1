import sqlite3

# Create database
conn = sqlite3.connect("app_data.db")
cursor = conn.cursor()

# Paste your SQL schema here
with open("schema.sql", "r") as f:
    schema = f.read()
cursor.executescript(schema)

conn.commit()
print("Database created successfully.")
