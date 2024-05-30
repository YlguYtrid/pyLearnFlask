import os
import re
from datetime import (
    UTC,
    datetime,
)
from typing import (
    NoReturn,
    Self,
)

from flask import (
    current_app,
    url_for,
)
from flask.cli import F
from flask_login import UserMixin
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.orm.relationships import _RelationshipDeclared
from werkzeug.security import (
    check_password_hash,
    generate_password_hash,
)

from .core.extensions import db
from .forms import (
    CategoryForm,
    CommentForm,
    LinkForm,
    LoginForm,
    PostForm,
)


def utcnow() -> datetime:
    """
    Returns
    -------
    datetime
        The current time in UTC timezone.
    """
    return datetime.now(UTC)


class Admin(UserMixin, db.Model):
    id = Column(Integer, primary_key=True)
    username = Column(String(20), unique=True)
    password_hash = Column(String(128))
    blog_title = Column(String(60))
    blog_sub_title = Column(String(100))
    name = Column(String(30))
    about = Column(Text)
    custom_footer = Column(Text)
    custom_css = Column(Text)
    custom_js = Column(Text)

    @property
    def password(self) -> NoReturn:
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)  # type: ignore

    def __eq__(self, form: LoginForm) -> bool:
        return self.username == form.username.data and self.check_password(form.password.data)  # type: ignore


class Category(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(30), unique=True, nullable=False)

    posts = relationship('Post', back_populates='category')

    @classmethod
    def from_form(cls, form: CategoryForm) -> Self:
        return cls(name=form.name.data)  # type: ignore

    def edit_from_form(self, form: CategoryForm) -> None:
        """
        Edit the category name from the form.
        - After edited the category, no need to use 'db.session.commit()' to update the database.

        Parameters
        ----------
        name : str
        """
        self.name = form.name.data
        db.session.commit()

    def delete(self) -> bool:
        """
        Delete the category and move all its posts to the default category (id=1).
        - If the category.id is 1, it means it is the default category, so it cannot be deleted.
        - After deleted the category, no need to use 'db.session.commit()' to update the database.

        Returns
        -------
        bool
            True if the category is deleted successfully, otherwise False.
        """
        if self.id == 1:  # type: ignore
            return False
        default_category: Category | None = db.session.get(Category, 1)
        for post in self.posts:
            post.category = default_category
        db.session.delete(self)
        db.session.commit()
        return True


class Post(db.Model):
    id = Column(Integer, primary_key=True)
    title = Column(String(60), nullable=False)
    body = Column(Text)
    created_time = Column(DateTime, default=utcnow, index=True)
    updated_time = Column(DateTime, default=utcnow, index=True)
    no_comment = Column(Boolean, default=False)

    category_id = Column(Integer, ForeignKey('category.id'))

    category = relationship(Category, back_populates='posts')
    comments = relationship('Comment', back_populates='post', cascade='all, delete-orphan')

    @property
    def reviewed_comments_counts(self) -> int:
        return sum(comment.reviewed for comment in self.comments)

    @classmethod
    def from_form(cls, form: PostForm) -> Self:
        return cls(
            title=form.title.data,
            body=form.body.data,
            category_id=form.category.data,
        )  # type: ignore

    def edit_from_form(self, form: PostForm) -> None:
        """
        Edit the post from the form.
        - After edited the post, no need to use 'db.session.commit()' to update the database.

        Parameters
        ----------
        form : PostForm
        """
        self.title = form.title.data
        self.body = form.body.data
        self.category_id = form.category.data
        self.updated_time = utcnow()
        db.session.commit()

    def delete(self) -> None:
        """
        Delete the post, its comments, and its images from the file system.
        - After deleted the post, no need to use 'db.session.commit()' to update the database.
        """
        upload_path: str = current_app.config['GREYBOOK_UPLOAD_PATH']
        upload_url: str = url_for('blog.get_image', filename='')
        images: str = re.findall(rf'<img.*?src="{upload_url}(.*?)"', self.body)  # type: ignore
        for image in images:
            file_path: str = os.path.join(upload_path, image)
            if os.path.exists(file_path):
                os.remove(file_path)

        db.session.delete(self)
        db.session.commit()


class Comment(db.Model):
    id = Column(Integer, primary_key=True)
    author = Column(String(30))
    email = Column(String(254))
    site = Column(String(255))
    body = Column(Text)
    created_time = Column(DateTime, default=utcnow, index=True)
    updated_time = Column(DateTime, default=utcnow, index=True)
    reviewed = Column(Boolean, default=False)
    reviewed_time = Column(DateTime, default=utcnow, index=True)
    from_admin = Column(Boolean, default=False)

    replied_id = Column(Integer, ForeignKey('comment.id'))
    post_id = Column(Integer, ForeignKey('post.id'))

    post = relationship(Post, back_populates='comments')
    replies = relationship('Comment', back_populates='replied', cascade='all, delete-orphan')
    replied = relationship('Comment', back_populates='replies', remote_side=[id])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.from_admin is True:
            with current_app.test_request_context():
                self.reviewed = True
                self.reviewed_time = self.updated_time
                self.author = os.getenv('GREYBOOK_ADMIN', 'Admin')
                self.email = os.getenv('GREYBOOK_ADMIN_EMAIL', 'admin@example.com')
                self.site = url_for('blog.index')

    @classmethod
    def from_form(cls, form: CommentForm, from_admin: bool, post_id: int) -> Self:
        return cls(
            author=form.author.data,
            email=form.email.data,
            site=form.site.data,
            body=form.body.data,
            from_admin=from_admin,
            post_id=post_id,
        )  # type: ignore

    def review(self) -> None:
        """
        Mark the comment as reviewed.
        """
        self.reviewed = True
        self.reviewed_time = utcnow()


class Link(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(30))
    url = Column(String(255))

    @classmethod
    def from_form(cls, form: LinkForm) -> Self:
        return cls(
            name=form.name.data,
            url=form.url.data,
        )  # type: ignore

    def edit_from_form(self, form: LinkForm) -> None:
        """
        Edit the link from the form.
        - After edited the link, no need to use 'db.session.commit()' to update the database.

        Parameters
        ----------
        form : LinkForm
        """
        self.name = form.name.data
        self.url = form.url.data
        db.session.commit()
