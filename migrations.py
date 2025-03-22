from flask import Flask
from extensions import db  # Import the db instance from extensions.py
from flask_migrate import Migrate
import os

import shutil
import sqlite3

# Create a minimal app for migrations
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gestione_corsi.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the db with this app
db.init_app(app)

# Function to reset migrations
def reset_migrations():
    """Reset migrations completely"""
    # Remove existing migrations directory if it exists
    migrations_path = os.path.join(os.path.dirname(__file__), 'migrations')
    if os.path.exists(migrations_path):
        print("Removing existing migrations directory...")
        shutil.rmtree(migrations_path)
    
    # Remove alembic_version table from database if it exists
    db_path = os.path.join(os.path.dirname(__file__), 'gestione_corsi.db')
    if os.path.exists(db_path):
        print("Removing alembic_version table from database...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS alembic_version")
        conn.commit()
        conn.close()

# Function to create tables directly without migrations
def create_tables():
    """Create all tables directly without migrations"""
    # Import models to ensure they're registered with SQLAlchemy
    from models import Progetto, User, Corso, Iscrizione, Test, Nota, RisultatoTest, Attestato
    
    with app.app_context():
        print("Creating tables directly...")
        db.create_all()
        print("Tables created successfully!")

if __name__ == '__main__':
    # Reset migrations first
    reset_migrations()
    
    # Create tables directly without using migrations
    create_tables()
    
    print("Database setup completed successfully!")