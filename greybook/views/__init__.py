from flask import Flask

from .admin import bp_admin
from .auth import bp_auth
from .blog import bp_blog


def register_blueprints(app: Flask) -> None:
    app.register_blueprint(bp_admin, url_prefix='/admin')
    app.register_blueprint(bp_auth, url_prefix='/auth')
    app.register_blueprint(bp_blog)
