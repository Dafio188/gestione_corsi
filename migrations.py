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

def reset_database():
    """Reset database completely"""
    # Remove existing database file if it exists
    db_path = os.path.join(os.path.dirname(__file__), 'gestione_corsi.db')
    if os.path.exists(db_path):
        print("Removing existing database file...")
        os.remove(db_path)
    
    # Remove migrations directory if it exists
    migrations_path = os.path.join(os.path.dirname(__file__), 'migrations')
    if os.path.exists(migrations_path):
        print("Removing existing migrations directory...")
        shutil.rmtree(migrations_path)

def create_tables():
    """Create all tables directly without migrations"""
    # Import models to ensure they're registered with SQLAlchemy
    from models import Progetto, User, Corso, Iscrizione, Test, Nota, RisultatoTest, Attestato
    
    with app.app_context():
        print("Creating tables directly...")
        db.create_all()
        
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
        
        try:
            db.session.commit()
            print("Admin user created successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"Error creating admin user: {e}")
        
        print("Tables created successfully!")

if __name__ == '__main__':
    # Reset database first
    reset_database()
    
    # Create tables directly without using migrations
    create_tables()
    
    print("Database setup completed successfully!")