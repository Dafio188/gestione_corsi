import os
from flask import Flask
from extensions import db
from models import User, Progetto, Corso, Iscrizione, Test, RisultatoTest, Attestato, Nota
from werkzeug.security import generate_password_hash

# Create a minimal Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gestione_corsi.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Delete existing database file if it exists
def reset_db():
    with app.app_context():
        # Drop all tables first to ensure clean state
        db.drop_all()
        print("Dropped all existing tables")
        
        # Remove the database file if it exists
        db_file = 'gestione_corsi.db'
        if os.path.exists(db_file):
            os.remove(db_file)
            print(f"Removed existing database: {db_file}")
        
        # Create all tables
        db.create_all()
        print("Created new database with all tables")
        
        # Check if admin user already exists
        existing_admin = User.query.filter_by(email='admin@example.com').first()
        if existing_admin:
            db.session.delete(existing_admin)
            db.session.commit()
            print("Removed existing admin user")
        
        # Create admin user
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
        print("Created admin user (username: admin, password: admin123)")
        
        print("Database reset complete!")

if __name__ == '__main__':
    reset_db()