from typing import (
    Any,
    Sequence,
)

from flask_login import current_user
from sqlalchemy import (
    func,
    select,
)

from ..models import (
    Admin,
    Category,
    Comment,
    Link,
)
from .extensions import db


def register_template_handlers(app) -> None:
    @app.context_processor
    def make_template_context() -> dict[str, Any]:
        admin: Admin | None = db.session.scalar(select(Admin))
        categories: Sequence[Category] = db.session.scalars(select(Category).order_by(Category.name)).all()
        links: Sequence[Link] = db.session.scalars(select(Link).order_by(Link.name)).all()

        if current_user.is_authenticated:
            unread_comments = db.session.scalars(select(func.count(Comment.id)).filter_by(reviewed=False)).one()
        else:
            unread_comments = None

        return dict(
            admin=admin,
            categories=categories,
            links=links,
            unread_comments=unread_comments,
        )
