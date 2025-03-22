from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import os

# Create a minimal app for migrations
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gestione_corsi.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Import models to ensure they're registered with SQLAlchemy
from models import Progetto, User, Corso, Iscrizione, Test, Nota, RisultatoTest, Attestato

# Initialize Flask-Migrate
migrate = Migrate(app, db)

if __name__ == '__main__':
    # Import Flask-Migrate commands
    from flask_migrate import cli as migrate_cli
    
    # Register the db command with the Flask app
    app.cli.add_command(migrate_cli.db)
    
    # Run the app
    app.run()