from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

# ✅ Definizione delle estensioni SENZA creare l'app
db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__, instance_relative_config=True, template_folder='templates', static_folder='static')

    # Configurazione chiave segreta
    app.config['SECRET_KEY'] = 'davide'

    # Configurazione database SQLite
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///database.db"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # ✅ Inizializza le estensioni con `app`
    db.init_app(app)
    login_manager.init_app(app)
    migrate = Migrate(app, db)

    login_manager.login_view = "auth.login"

    @login_manager.user_loader
    def load_user(user_id):
        from app.models.models import Discente
        return Discente.query.get(int(user_id))

    @app.context_processor
    def inject_user():
        return dict(current_user=login_manager._user_callback)

    # ✅ IMPORTA e REGISTRA i Blueprint
    from app.routes.dashboard import dashboard_bp
    from app.routes.progetti import progetti_bp
    from app.routes.corsi import corsi_bp
    from app.routes.discenti import discenti_bp
    from app.routes.test import test_bp
    from app.routes.attestati import attestati_bp
    from app.routes.report import report_bp
    from app.routes.iscrizioni import iscrizioni_bp

    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(progetti_bp, url_prefix='/progetti')
    app.register_blueprint(corsi_bp, url_prefix='/corsi')
    app.register_blueprint(discenti_bp, url_prefix='/discenti')
    app.register_blueprint(test_bp, url_prefix='/test')
    app.register_blueprint(attestati_bp, url_prefix='/attestati')
    app.register_blueprint(report_bp, url_prefix='/report')
    app.register_blueprint(iscrizioni_bp, url_prefix='/iscrizioni')
    
    return app
