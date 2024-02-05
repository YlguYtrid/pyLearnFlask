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
app.config['SQLALCHEMY_DATABASE_URI'] = prefix + os.path.join(os.path.dirname(app.root_path), 'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['SECRET_KEY'] = 'dshbig^&(*DT&C796asfase^&R56%^&*d568)'

db = SQLAlchemy(app)
login_manager = LoginManager(app)


@login_manager.user_loader
def load_user(user_id):
    from watchlist.models import User

    return db.session.get(User, int(user_id))


login_manager.login_view = 'login'


@app.context_processor
def inject_user():
    from watchlist.models import User

    user = User.query.first()
    return dict(user=user)


from watchlist import commands, errors, views