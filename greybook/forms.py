from calendar import c
from typing import Self

from flask import (
    current_app,
    url_for,
)
from flask_ckeditor import CKEditorField
from flask_login import current_user
from flask_wtf import FlaskForm
from sqlalchemy import (
    ScalarResult,
    select,
)
from wtforms import (
    BooleanField,
    HiddenField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
    ValidationError,
)
from wtforms.validators import (
    URL,
    DataRequired,
    Email,
    Length,
    Optional,
)

from .core.extensions import db


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(1, 20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(1, 120)])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Log In')


class SettingForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(1, 30)])
    blog_title = StringField('Blog Title', validators=[DataRequired(), Length(1, 60)])
    blog_sub_title = StringField('Blog Sub Title', validators=[DataRequired(), Length(1, 100)])
    about = CKEditorField('About Page', validators=[DataRequired()])
    custom_footer = TextAreaField('Custom Footer (HTML)', validators=[Optional()])
    custom_css = TextAreaField('Custom CSS', validators=[Optional()])
    custom_js = TextAreaField('Custom JS', validators=[Optional()])
    submit = SubmitField()


class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(1, 60)])
    category = SelectField('Category', coerce=int, default=1)
    body = CKEditorField('Body', validators=[DataRequired()])
    submit = SubmitField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Category

        categories: ScalarResult[Category] = db.session.scalars(select(Category).order_by(Category.name))
        self.category.choices: list[tuple[int, str]] = [(category.id, category.name) for category in categories]  # type: ignore

    @classmethod
    def from_model(cls, post) -> Self:
        return cls(
            title=post.title,
            category=post.category_id,
            body=post.body,
        )


class CategoryForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(1, 30)])
    submit = SubmitField()

    def validate_name(self, field: StringField) -> None:
        from .models import Category

        if db.session.scalar(select(Category).filter_by(name=field.data)):
            raise ValidationError('Name already in use.')


class CommentForm(FlaskForm):
    author = StringField('Name', validators=[DataRequired(), Length(1, 30)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(1, 254)])
    site = StringField('Site', validators=[Optional(), URL(), Length(0, 255)])
    body = TextAreaField('Comment', validators=[DataRequired()])
    submit = SubmitField()


class AdminCommentForm(CommentForm):
    author = HiddenField()
    email = HiddenField()
    site = HiddenField()

    def admin_init(self):
        """
        Initialize the form with admin data.
        """
        self.author.data = current_user.name
        self.email.data = current_app.config['GREYBOOK_ADMIN_EMAIL']
        self.site.data = url_for('.index')


class LinkForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(1, 30)])
    url = StringField('URL', validators=[DataRequired(), URL(), Length(1, 255)])
    submit = SubmitField()
