from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
import shutil
import sqlite3

# Create a minimal app for migrations
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gestione_corsi.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Import models to ensure they're registered with SQLAlchemy
from models import Progetto, User, Corso, Iscrizione, Test, Nota, RisultatoTest, Attestato, Evento, DisponibilitaDocente

def init_db():
    with app.app_context():
        # Get the absolute path of the database file
        db_path = os.path.abspath('gestione_corsi.db')
        print(f"Database path: {db_path}")
        
        # Check if the database exists
        if not os.path.exists(db_path):
            print("Database non trovato. Creazione nuovo database...")
            db.create_all()
            print("Database creato con successo!")
            
            # Create an admin user
            from models import User
            admin = User(
                username='admin',
                email='admin@example.com',
                nome='Admin',
                cognome='User',
                role='admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Utente admin creato con successo!")
        else:
            print("Database esistente trovato. Aggiornamento tabelle...")
            
            # Connect to the database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if the disponibilita_docente table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='disponibilita_docente';")
            if cursor.fetchone():
                print("Rimozione tabella disponibilita_docente esistente...")
                cursor.execute("DROP TABLE disponibilita_docente;")
                conn.commit()
                print("Tabella disponibilita_docente rimossa con successo!")
            
            # Create the disponibilita_docente table with the correct structure
            print("Creazione tabella disponibilita_docente...")
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
            )
            ''')
            conn.commit()
            print("Tabella disponibilita_docente creata con successo!")
            
            # Check if the evento table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='evento';")
            if not cursor.fetchone():
                print("Creazione tabella evento...")
                db.create_all()
                print("Tabella evento creata con successo!")
            else:
                print("La tabella evento esiste già.")
            
            conn.close()
            print("Aggiornamento completato!")

if __name__ == '__main__':
    init_db()