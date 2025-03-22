from run import app, db
import os
import sqlite3

# Create a context for the app
with app.app_context():
    # Print the database URI to verify location
    print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    # Get the absolute path of the database file
    db_path = os.path.abspath('gestione_corsi.db')
    print(f"Absolute database path: {db_path}")
    
    # Remove the database file completely
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed existing database file: {db_path}")
    
    # Create all tables from scratch
    db.create_all()
    print("All database tables created successfully!")
    
    # Verify which tables were created
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get list of all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("\nTables created in the database:")
    for table in tables:
        print(f"- {table[0]}")
    
    # Check if the nota table exists and has the correct structure
    cursor.execute("PRAGMA table_info(nota);")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    print("\nColumns in nota table:", column_names)
    
    # If data_modifica column is missing, drop and recreate the table
    if 'nota' in [table[0] for table in tables] and 'data_modifica' not in column_names:
        print("\nThe 'data_modifica' column is missing. Recreating the nota table...")
        
        # Drop the existing table
        cursor.execute("DROP TABLE IF EXISTS nota;")
        
        # Create the table with the correct structure
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
        print("Recreated 'nota' table with data_modifica column.")
        
        # Verify the structure of the recreated table
        cursor.execute("PRAGMA table_info(nota);")
        columns = cursor.fetchall()
        print("\nStructure of recreated 'nota' table:")
        for col in columns:
            print(f"- {col[1]} ({col[2]})")
    
    conn.close()
    
    print("\nMigration completed. Try running the application now.")