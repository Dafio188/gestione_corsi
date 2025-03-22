import sqlite3
import os

def update_schema():
    # Path to the database file
    db_path = os.path.join('instance', 'database.db')
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check what tables exist in the database
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [table[0] for table in cursor.fetchall()]
    print("Tables in database:", tables)
    
    # Create corso table if it doesn't exist
    if 'corso' not in tables:
        print("Creating corso table...")
        cursor.execute('''
        CREATE TABLE corso (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titolo TEXT NOT NULL,
            descrizione TEXT,
            ore_totali REAL NOT NULL,
            data_inizio TIMESTAMP NOT NULL,
            data_fine TIMESTAMP NOT NULL,
            progetto_riferimento TEXT,
            progetto_id INTEGER,
            docente_id INTEGER NOT NULL,
            modalita TEXT NOT NULL DEFAULT 'in_house',
            indirizzo TEXT,
            link TEXT,
            FOREIGN KEY (docente_id) REFERENCES user (id),
            FOREIGN KEY (progetto_id) REFERENCES progetto (id)
        )
        ''')
        print("Corso table created successfully!")
    else:
        # Check if the columns already exist
        cursor.execute("PRAGMA table_info(corso)")
        columns = [column[1] for column in cursor.fetchall()]
        print("Columns in corso table:", columns)
        
        # Add indirizzo column if it doesn't exist
        if 'indirizzo' not in columns:
            cursor.execute("ALTER TABLE corso ADD COLUMN indirizzo TEXT")
            print("Added 'indirizzo' column to corso table")
        
        # Add link column if it doesn't exist
        if 'link' not in columns:
            cursor.execute("ALTER TABLE corso ADD COLUMN link TEXT")
            print("Added 'link' column to corso table")
    
    conn.commit()
    conn.close()
    print("Schema update completed!")

if __name__ == '__main__':
    update_schema()