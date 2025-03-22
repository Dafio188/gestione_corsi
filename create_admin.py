from run import app, db, User
from werkzeug.security import generate_password_hash

def create_admin():
    with app.app_context():
        # Create all database tables
        db.create_all()
        
        # Check if admin already exists
        admin = User.query.filter_by(email='admin@admin.com').first()
        if admin:
            print("Admin user already exists!")
            return
        
        # Create admin user with codice_fiscale and unita_org
        admin = User(
            email='admin@admin.com',
            password=generate_password_hash('admin123'),
            nome='Admin',
            cognome='Master',
            role='admin',
            codice_fiscale='ADMIN0000000000',
            unita_org='Admin Unit'
        )
        
        db.session.add(admin)
        db.session.commit()
        print("Admin user created successfully!")

if __name__ == '__main__':
    create_admin()