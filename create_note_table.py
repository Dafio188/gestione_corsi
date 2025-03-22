from run import app, db
from models import Nota

# Create a context for the app
with app.app_context():
    # Drop the existing note table if it exists
    Nota.__table__.drop(db.engine, checkfirst=True)
    
    # Create the note table with the correct foreign keys
    Nota.__table__.create(db.engine)
    print("Note table recreated successfully with proper foreign keys.")