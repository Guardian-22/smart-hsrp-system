# backend/db/init_db.py

# Run this command => python backend/db/init_db.py 
import sqlite3
import os

def initialize():
    # Get the directory where THIS script is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path to the database and schema in the same folder as this script
    db_path = os.path.join(current_dir, "smart_hsrp.db")
    schema_path = os.path.join(current_dir, "schema.sql")

    if not os.path.exists(schema_path):
        print(f"❌ Error: {schema_path} not found.")
        return

    try:
        with sqlite3.connect(db_path) as conn:
            with open(schema_path, "r") as f:
                schema_script = f.read()
            conn.executescript(schema_script)
        print(f"✅ Successfully created database at: {db_path}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    initialize()
