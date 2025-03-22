from flask import Flask
from extensions import db  # Import the db instance from your extensions file
import os

# Create a minimal app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gestione_corsi.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the db with this app
db.init_app(app)

# Import models
from models import Progetto, User, Corso, Iscrizione, Test, Nota, RisultatoTest, Attestato

def create_tables():
    with app.app_context():
        # Drop existing database file if it exists
        db_path = os.path.join(os.path.dirname(__file__), 'gestione_corsi.db')
        if os.path.exists(db_path):
            os.remove(db_path)
            print("Existing database removed.")
        
        # Remove migrations folder if it exists
        migrations_path = os.path.join(os.path.dirname(__file__), 'migrations')
        if os.path.exists(migrations_path):
            import shutil
            shutil.rmtree(migrations_path)
            print("Existing migrations folder removed.")
        
        # Create all tables from scratch
        db.create_all()
        print("Database tables created successfully!")
        
        # Check if admin user exists before creating
        existing_admin = User.query.filter_by(username='admin').first()
        if not existing_admin:
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
        else:
            print("Admin user already exists.")

if __name__ == "__main__":
    create_tables()