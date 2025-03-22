import os
import shutil
import sys
import sqlite3
import traceback

# Import the app and db from your main application
from run import app, db

# Import models to ensure they're registered with SQLAlchemy
from models import Progetto, User, Corso, Iscrizione, Test, Nota, RisultatoTest, Attestato

# Initialize Flask-Migrate
from flask_migrate import Migrate, init, migrate, upgrade, current
migrate = Migrate(app, db)

# Function to add link_webinar column directly to the database
def add_link_webinar_column():
    try:
        # Check if database file exists
        db_path = 'gestione_corsi.db'
        
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # List all tables in the database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall()]
        print(f"Tables in database: {tables}")
        
        # Check if the corso table exists (case-insensitive)
        table_name = None
        for table in tables:
            if table.lower() == 'corso':
                table_name = table
                break
        
        if not table_name:
            print("The 'corso' table does not exist in the database.")
            print("This suggests your database is not properly set up.")
            print("Please make sure your application has been run at least once to create the database.")
            return False
        
        # Check if the column already exists
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"Columns in {table_name} table: {columns}")
        
        if 'link_webinar' not in columns:
            # Add the link_webinar column
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN link_webinar VARCHAR(255)")
            conn.commit()
            print(f"link_webinar column added to {table_name} table.")
        else:
            print(f"link_webinar column already exists in {table_name} table.")
        
        conn.close()
        return True
    except Exception as e:
        print(f"Error adding link_webinar column: {e}")
        traceback.print_exc()
        return False

# Main execution
if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'add_column':
            print("Adding link_webinar column directly to the database...")
            if add_link_webinar_column():
                print("Column added successfully.")
            else:
                print("Failed to add column.")
        else:
            print(f"Unknown command: {command}")
            print("Available commands: add_column")
    else:
        print("Please provide a command: add_column")