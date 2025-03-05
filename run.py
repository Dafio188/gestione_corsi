from flask import Flask
from flask_migrate import Migrate
from app.models.models import db
from app.routes.dashboard import dashboard_bp
from app.routes.progetti import progetti_bp
from app.routes.corsi import corsi_bp
from app.routes.discenti import discenti_bp
from app.routes.test import test_bp
from app.routes.attestati import attestati_bp
from app.routes.report import report_bp
import os

def create_app():
    """Creazione e configurazione dell'app Flask"""
    app = Flask(__name__, instance_relative_config=True, template_folder='app/templates', static_folder='app/static')

    app.config['SECRET_KEY'] = 'davide'  # Usa una chiave segreta più sicura in produzione

    # Creiamo la cartella 'instance' se non esiste
    os.makedirs(app.instance_path, exist_ok=True)

    # Configurazione del database SQLite nella cartella 'instance'
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(app.instance_path, 'database.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inizializzazione database e migrazioni
    db.init_app(app)
    migrate = Migrate(app, db)

    # **Registrazione delle Blueprint**
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(progetti_bp, url_prefix='/progetti')
    app.register_blueprint(corsi_bp, url_prefix='/corsi')
    app.register_blueprint(discenti_bp, url_prefix='/discenti')
    app.register_blueprint(test_bp, url_prefix='/test')
    app.register_blueprint(attestati_bp, url_prefix='/attestati')
    app.register_blueprint(report_bp, url_prefix='/report')

    return app

# Creazione dell'applicazione
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)

