import sqlite3

DB_FILE = "user.db"
SQL_FILE = "user.sql"

def initialize_database():
    """Create the database and tables based on db.sql."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        with open(SQL_FILE, 'r') as sql_file:
            sql_script = sql_file.read()
        cursor.executescript(sql_script)
        print("Database initialized successfully!")

if __name__ == "__main__":
    initialize_database()
