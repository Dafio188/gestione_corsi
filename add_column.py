from extensions import db
from models import Corso, User, Progetto, Iscrizione, Test, Nota, RisultatoTest, Attestato
from run import app
import os
from sqlalchemy import inspect, text

def add_piattaforma_column():
    with app.app_context():
        try:
            # Now try to add the column directly without creating tables
            with db.engine.connect() as conn:
                # First check if the corso table exists (note: singular, not plural)
                inspector = inspect(db.engine)
                tables = inspector.get_table_names()
                
                if 'corso' in tables:
                    # Check if the column already exists
                    result = conn.execute(text("PRAGMA table_info(corso)"))
                    columns = [row[1] for row in result.fetchall()]
                    
                    if 'piattaforma' not in columns:
                        conn.execute(text("ALTER TABLE corso ADD COLUMN piattaforma VARCHAR(200)"))
                        conn.commit()
                        print("Column 'piattaforma' added successfully to 'corso' table.")
                    else:
                        print("Column 'piattaforma' already exists in 'corso' table.")
                else:
                    print("Table 'corso' does not exist. Cannot add column.")
                    print("Available tables:", tables)
        except Exception as e:
            print(f"Error: {e}")
            print("Please check your database configuration and table structure.")

if __name__ == '__main__':
    add_piattaforma_column()