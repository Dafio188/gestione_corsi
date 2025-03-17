from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

# ✅ Inizializza le estensioni
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # ✅ Configurazione chiave segreta
    app.config['SECRET_KEY'] = 'davide'

    # ✅ Configurazione database SQLite
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///database.db"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # ✅ Inizializza le estensioni con `app`
    db.init_app(app)
    migrate.init_app(app, db)

    # ✅ IMPORTA e REGISTRA i Blueprint PRIMA di configurare Flask-Login
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.routes.dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')

    from app.routes.progetti import progetti_bp
    app.register_blueprint(progetti_bp, url_prefix='/progetti')

    from app.routes.corsi import corsi_bp
    app.register_blueprint(corsi_bp, url_prefix='/corsi')

    from app.routes.discenti import discenti_bp
    app.register_blueprint(discenti_bp, url_prefix='/discenti')

    from app.routes.test import test_bp
    app.register_blueprint(test_bp, url_prefix='/test')

    from app.routes.attestati import attestati_bp
    app.register_blueprint(attestati_bp, url_prefix='/attestati')

    from app.routes.report import report_bp
    app.register_blueprint(report_bp, url_prefix='/report')

    from app.routes.iscrizioni import iscrizioni_bp
    app.register_blueprint(iscrizioni_bp)

    # ✅ Aggiungiamo la nuova rotta per l'importazione discenti
    from app.routes.import_discenti import import_discenti_bp
    app.register_blueprint(import_discenti_bp, url_prefix='/importa_discenti')

    # ✅ SOLO ORA configuriamo Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"  # 🔹 Questo deve venire DOPO la registrazione del Blueprint

    @login_manager.user_loader
    def load_user(user_id):
        from app.models.models import Discente
        return Discente.query.get(int(user_id))

    return app
