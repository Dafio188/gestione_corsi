import os
from run import app, db
import sqlite3
from sqlalchemy import text

# Create a context for the app
with app.app_context():
    # Get the database path
    db_path = 'gestione_corsi.db'
    abs_path = os.path.abspath(db_path)
    print(f"Database path: {abs_path}")
    
    # Remove the database file if it exists
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed existing database file: {db_path}")
    
    # Create all tables from scratch
    db.create_all()
    print("All database tables created successfully!")
    
    # Verify the database structure
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    
    # Get all tables
    tables = inspector.get_table_names()
    print(f"\nTables created: {tables}")
    
    # Create the nota table directly with SQLAlchemy
    print("\nRecreating the nota table with all required columns...")
    try:
        # Drop existing tables if they exist
        db.session.execute(text("DROP TABLE IF EXISTS nota"))
        db.session.execute(text("DROP TABLE IF EXISTS note"))
        db.session.commit()
        
        # Create the nota table with all required columns
        db.session.execute(text('''
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
        '''))
        db.session.commit()
        print("✓ Successfully created nota table with all required columns")
        
        # Verify the structure of all tables
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check nota table
        cursor.execute("PRAGMA table_info(nota);")
        columns = cursor.fetchall()
        print("\nColumns in recreated nota table:")
        for col in columns:
            print(f"- {col[1]} ({col[2]})")
        
        # Check corso table
        print("\nVerifying corso table structure...")
        cursor.execute("PRAGMA table_info(corso);")
        corso_columns = cursor.fetchall()
        print("\nColumns in corso table:")
        for col in corso_columns:
            print(f"- {col[1]} ({col[2]})")
        
        # Check if the new fields exist in corso table
        corso_column_names = [col[1] for col in corso_columns]
        if 'indirizzo' not in corso_column_names or 'orario' not in corso_column_names or 'link_webinar' not in corso_column_names:
            print("\nRecreating corso table with all required columns...")
            
            # Get all existing corso data if needed
            # cursor.execute("SELECT * FROM corso")
            # existing_corsi = cursor.fetchall()
            
            # Drop and recreate corso table with all fields
            db.session.execute(text("DROP TABLE IF EXISTS corso"))
            db.session.commit()
            
            # Create corso table with all required columns
            db.session.execute(text('''
            CREATE TABLE corso (
                id INTEGER PRIMARY KEY,
                titolo VARCHAR(100) NOT NULL,
                descrizione TEXT,
                ore_totali FLOAT NOT NULL,
                data_inizio TIMESTAMP NOT NULL,
                data_fine TIMESTAMP NOT NULL,
                progetto_riferimento VARCHAR(100),
                progetto_id INTEGER,
                docente_id INTEGER NOT NULL,
                modalita VARCHAR(20) NOT NULL DEFAULT 'in_house',
                indirizzo VARCHAR(255),
                orario VARCHAR(100),
                link_webinar VARCHAR(255),
                FOREIGN KEY (progetto_id) REFERENCES progetto (id),
                FOREIGN KEY (docente_id) REFERENCES user (id)
            )
            '''))
            db.session.commit()
            
            # Verify the updated structure
            cursor.execute("PRAGMA table_info(corso);")
            updated_columns = cursor.fetchall()
            print("\nColumns in recreated corso table:")
            for col in updated_columns:
                print(f"- {col[1]} ({col[2]})")
            
            print("✓ Successfully recreated corso table with all required columns")
        
        conn.close()
        
    except Exception as e:
        print(f"Error recreating tables: {e}")
        db.session.rollback()
    
    print("\nDatabase recreation completed.")