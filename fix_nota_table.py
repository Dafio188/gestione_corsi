import sqlite3
import os
from run import app

# Get the database path from the app configuration
with app.app_context():
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    db_path = db_uri.replace('sqlite:///', '')
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} does not exist!")
    else:
        print(f"Fixing nota table in database: {db_path}")
        
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the nota table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='nota';")
        if not cursor.fetchone():
            print("The 'nota' table doesn't exist! Creating it...")
            cursor.execute('''
            CREATE TABLE nota (
                id INTEGER PRIMARY KEY,
                titolo VARCHAR(100) NOT NULL,
                contenuto TEXT,
                data_creazione TIMESTAMP,
                data_modifica TIMESTAMP,
                docente_id INTEGER NOT NULL,
                corso_id INTEGER,
                FOREIGN KEY (docente_id) REFERENCES user (id),
                FOREIGN KEY (corso_id) REFERENCES corso (id)
            )
            ''')
            conn.commit()
            print("Created 'nota' table with all required columns.")
        else:
            # Check if data_modifica column exists
            cursor.execute("PRAGMA table_info(nota);")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            print(f"Current columns in nota table: {column_names}")
            
            if 'data_modifica' not in column_names:
                print("Adding 'data_modifica' column to nota table...")
                try:
                    cursor.execute("ALTER TABLE nota ADD COLUMN data_modifica TIMESTAMP;")
                    conn.commit()
                    print("Successfully added 'data_modifica' column.")
                except Exception as e:
                    print(f"Error adding column: {e}")
            else:
                print("The 'data_modifica' column already exists.")
        
        conn.close()
        print("Database fix completed.")