from ..models import (
    Admin,
    Category,
    Comment,
    Post,
)
from .extensions import db


def register_shell_handlers(app):
    @app.shell_context_processor
    def make_shell_context():
        return dict(
            db=db,
            Admin=Admin,
            Post=Post,
            Category=Category,
            Comment=Comment,
        )
