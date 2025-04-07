from flask import Flask
from flask_migrate import Migrate
from run import app, db
import os
import shutil
import sqlite3

# Initialize Flask-Migrate
migrate = Migrate(app, db)

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python migrate.py [init|migrate|upgrade|revision|heads|current|reset]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    # Create application context
    with app.app_context():
        if command == 'init':
            from flask_migrate import init
            init(directory='migrations')
            print("Migration repository created.")
        
        elif command == 'migrate':
            from flask_migrate import migrate
            message = "Initial migration" if len(sys.argv) < 3 else sys.argv[2]
            migrate(message=message)
            print(f"Migration created with message: {message}")
        
        elif command == 'upgrade':
            from flask_migrate import upgrade
            # Check if a specific revision was provided
            if len(sys.argv) > 2:
                revision = sys.argv[2]
                upgrade(revision=revision)
                print(f"Database upgraded to revision: {revision}")
            else:
                upgrade()
                print("Database upgraded to latest revision.")
        
        elif command == 'revision':
            from flask_migrate import revision
            # Create a new empty revision
            if len(sys.argv) > 2:
                message = sys.argv[2]
                revision(message=message)
                print(f"Created new empty revision with message: {message}")
            else:
                revision(message="Empty revision")
                print("Created new empty revision.")
        
        elif command == 'heads':
            from flask_migrate import heads
            # Show current heads
            print("Current migration heads:")
            for head in heads():
                print(f"- {head}")
        
        elif command == 'current':
            from flask_migrate import current
            # Show current revision
            print(f"Current revision: {current()}")
        
        elif command == 'reset':
            # Reset the migration state completely
            if os.path.exists('migrations'):
                # Ask for confirmation
                confirm = input("This will delete all migrations and database. Are you sure? (y/n): ")
                if confirm.lower() != 'y':
                    print("Reset cancelled.")
                    sys.exit(0)
                
                # Delete migrations folder
                shutil.rmtree('migrations')
                print("Migrations folder deleted.")
                
                # Delete the database file
                db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
                if os.path.exists(db_path):
                    os.remove(db_path)
                    print("Database file deleted.")
                
                print("Reset complete. Now run:")
                print("1. python migrate.py init")
                print("2. python migrate.py migrate")
                print("3. python migrate.py upgrade")
            else:
                print("No migrations folder found.")
        
        else:
            print(f"Unknown command: {command}")
            print("Available commands: init, migrate, upgrade, revision, heads, current, reset")

conn = sqlite3.connect('gestione_corsi.db')
cursor = conn.cursor()
cursor.execute('DROP TABLE IF EXISTS disponibilita_docente;')
cursor.execute('''
CREATE TABLE disponibilita_docente (
    id INTEGER PRIMARY KEY,
    docente_id INTEGER NOT NULL,
    data DATE NOT NULL,
    ora_inizio TIME NOT NULL,
    ora_fine TIME NOT NULL,
    corso_id INTEGER,
    note TEXT,
    stato VARCHAR(20) DEFAULT 'disponibile',
    FOREIGN KEY (docente_id) REFERENCES user (id),
    FOREIGN KEY (corso_id) REFERENCES corso (id)
);
''')
conn.commit()
conn.close()
print('Tabella disponibilita_docente ricreata con successo!')