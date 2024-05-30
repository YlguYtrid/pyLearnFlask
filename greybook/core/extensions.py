import click
from flask import Flask
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_debugtoolbar import DebugToolbarExtension
from flask_login import LoginManager
from flask_mailman import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

extensions: list = [
    bootstrap := Bootstrap5(),
    ckeditor := CKEditor(),
    csrf := CSRFProtect(),
    debugtoolbar := DebugToolbarExtension(),
    db := SQLAlchemy(),
    login_manager := LoginManager(),
    mail := Mail(),
    migrate := Migrate(),
]


def register_extensions(app: Flask) -> None:
    for extension in extensions:
        match extension:
            case Migrate():
                extension.init_app(app, db=db)
            case _:
                extension.init_app(app)


@login_manager.user_loader
def load_user(id: str):
    match id:
        case int():
            click.echo(f'id is int: {id}')
        case str():
            click.echo(f'id is str: {id}')
        case _:
            click.echo(f'id is not int or str: {id}')
    from ..models import Admin

    user = db.session.get(Admin, int(id))
    return user


login_manager.login_view = 'auth.login'  # type: ignore
# login_manager.login_message = 'Your custom message'
login_manager.login_message_category = 'warning'
