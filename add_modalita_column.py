from run import app, db
from sqlalchemy import text

def upgrade_database():
    with app.app_context():
        # Use SQLAlchemy's text() and connection.execute() instead of engine.execute()
        with db.engine.connect() as conn:
            conn.execute(text('ALTER TABLE corso ADD COLUMN modalita VARCHAR(20) DEFAULT "in_house" NOT NULL'))
            conn.commit()
        print("Successfully added modalita column to corso table")

if __name__ == "__main__":
    upgrade_database()