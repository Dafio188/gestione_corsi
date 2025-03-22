import sqlite3
from werkzeug.security import generate_password_hash
import os

def create_admin():
    # Path to the database file
    db_path = os.path.join('instance', 'database.db')
    
    # Ensure the instance directory exists
    os.makedirs('instance', exist_ok=True)
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if the user table exists, if not create it
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        nome TEXT NOT NULL,
        cognome TEXT NOT NULL,
        role TEXT NOT NULL,
        codice_fiscale TEXT,
        unita_org TEXT
    )
    ''')
    
    # Check if admin already exists
    cursor.execute("SELECT * FROM user WHERE email = ?", ('admin@admin.com',))
    admin = cursor.fetchone()
    
    if admin:
        print("Admin user already exists!")
    else:
        # Create admin user
        hashed_password = generate_password_hash('admin123')
        cursor.execute('''
        INSERT INTO user (email, password, nome, cognome, role, codice_fiscale, unita_org)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('admin@admin.com', hashed_password, 'Admin', 'Master', 'admin', 'ADMIN0000000000', 'Admin Unit'))
        
        conn.commit()
        print("Admin user created successfully!")
    
    conn.close()

if __name__ == '__main__':
    create_admin()