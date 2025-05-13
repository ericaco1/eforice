import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)

# Create app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "eforice_default_secret")

# Configure WSGI app
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///eforice.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024 * 1024  # 1GB max upload size

# Configure file upload settings
app.config["UPLOAD_FOLDER"] = os.path.join(os.getcwd(), "uploads")
if not os.path.exists(app.config["UPLOAD_FOLDER"]):
    os.makedirs(app.config["UPLOAD_FOLDER"])

# Initialize extensions
db.init_app(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info"

# Create database tables
with app.app_context():
    # Import models to ensure they're registered with SQLAlchemy
    from models import User, File, Folder, StorageClass
    db.create_all()

    # Check if admin user exists, if not create one
    from models import User
    from werkzeug.security import generate_password_hash
    admin = User.query.filter_by(username="EUGACIRE").first()
    if not admin:
        admin = User(
            username="EUGACIRE",
            email="ericague90@gmail.com",
            password_hash=generate_password_hash("ERICACOCO1!"),
            is_admin=True,
            is_approved=True,
            storage_limit=10 * 1024 * 1024 * 1024  # 10GB for admin
        )
        db.session.add(admin)
        db.session.commit()
        logging.info("Admin user created")

# Load user
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))
