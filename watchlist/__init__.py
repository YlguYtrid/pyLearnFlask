import os
import sys

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

if sys.platform.startswith('win'):
    prefix = 'sqlite:///'
else:
    prefix = 'sqlite:////'

app = Flask(__name__)

app.config.update(
    SECRET_KEY=os.getenv('SECRET_KEY', 'dev'),
    SQLALCHEMY_DATABASE_URI=prefix + os.path.join(os.path.dirname(__file__), os.getenv('DATABASE_FILE', 'data.db')),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
)

db = SQLAlchemy(app)
login_manager = LoginManager(app)


@login_manager.user_loader
def load_user(user_id):
    from .models import User

    return db.session.get(User, int(user_id))


login_manager.login_view = 'login'


@app.context_processor
def inject_user():
    from .models import User

    user: User | None = db.session.scalar(db.select(User))
    return dict(user=user)


from . import commands, errors, views
