import os
from calendar import c

import click
from flask import (
    Flask,
    current_app,
)
from sqlalchemy import select

from ..fakes import (
    fake_admin,
    fake_categories,
    fake_comments,
    fake_links,
    fake_posts,
    fake_replies,
)
from ..models import (
    Admin,
    Category,
)
from .extensions import db


def register_commands(app: Flask) -> None:
    @app.cli.command()
    @click.option('--drop', is_flag=True, help='Create after drop.')
    def initdb(drop: bool) -> None:
        """Initialize the database."""
        if drop:
            click.confirm('This operation will delete the database, do you want to continue?', abort=True)
            db.drop_all()
            click.echo('Dropped tables.')
        db.create_all
        click.echo('Initialized database.')

    @app.cli.command()
    @click.option('--username', prompt=True, help='The username used to login.')
    @click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='The password used to login.')
    def init(
        username: str,
        password: str,
    ) -> None:
        """Initialize the blog."""
        db.create_all()
        click.echo('Initialized the database...')
        admin: Admin | None = db.session.scalar(select(Admin))

        if admin is not None:
            admin.username = username  # type: ignore
            admin.password = password
            click.echo('Updated administrator account.')
        else:
            admin = Admin(
                username=username,
                blog_title='Blog Title',
                blog_sub_title='Blog Sub Title',
                name='Admin',
                about='Anything about you.',
            )  # type: ignore
            admin.password = password
            db.session.add(admin)
            click.echo('Created the administrator account.')

        category: Category | None = db.session.scalar(select(Category))
        if category is None:
            category = Category(name='Default')  # type: ignore
            db.session.add(category)
            click.echo('Created the default category.')
        db.session.commit()
        upload_path: str = os.path.join(current_app.config['GREYBOOK_UPLOAD_PATH'])
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)
            click.echo('Created the upload folder.')
        click.echo('Initialized the blog.')

    @app.cli.command()
    @click.option('--category', default=10, help='Quantity of categories, default is 10.')
    @click.option('--post', default=50, help='Quantity of posts, default is 50.')
    @click.option('--comment', default=200, help='Quantity of comments, default is 200.')
    @click.option('--reply', default=50, help='Quantity of replies, default is 50.')
    def fake(
        category: int,
        post: int,
        comment: int,
        reply: int,
    ) -> None:
        """Generate fake data."""
        db.drop_all()
        db.create_all()
        click.echo('Initialized the database...')

        fake_admin()
        click.echo('Generated the administrator.')

        fake_categories(category)
        click.echo(f'Generated {category} categories.')

        fake_posts(post)
        click.echo(f'Generated {post} posts.')

        fake_comments(comment)
        click.echo(f'Generated {comment} comments.')

        fake_replies(reply)
        click.echo(f'Generated {reply} replies.')

        fake_links()
        click.echo('Generated links.')

        click.echo('Finished generating fake data.')
