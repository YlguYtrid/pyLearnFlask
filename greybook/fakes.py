import random
from datetime import datetime

from faker import Faker
from sqlalchemy import (
    func,
    select,
)

from .core.extensions import db
from .models import (
    Admin,
    Category,
    Comment,
    Link,
    Post,
)

fake = Faker()


def fake_admin() -> None:
    admin = Admin(
        username='admin',
        password='greybook',
        blog_title='Greybook',
        blog_sub_title='Just some random thoughts',
        name='Ylgu Ytrid',
        about='Hello, I am Ylgu Ytrid. This is an example ',
    )  # type: ignore
    db.session.add(admin)
    db.session.commit()


def fake_categories(count: int = 10) -> None:
    category = Category(name='Default')  # type: ignore
    db.session.add(category)
    words: list[str] = []
    for _ in range(count):
        while (word := fake.word().title()) in words:
            pass
        words.append(word)
    for word in words:
        category = Category(name=word)  # type: ignore
        db.session.add(category)
    db.session.commit()


def fake_posts(count: int = 50) -> None:
    category_count: int = db.session.scalars(select(func.count(Category.id))).one()
    for _ in range(count):
        category: Category = db.session.get(Category, random.randint(1, category_count))  # type: ignore
        created_time: datetime = fake.date_time_between_dates(datetime_start=datetime(2020, 1, 1), datetime_end=datetime(2024, 1, 1))
        updated_time: datetime = fake.date_time_between_dates(datetime_start=created_time, datetime_end=datetime(2024, 2, 1))
        post = Post(
            title=fake.sentence(),
            body=fake.text(2000),
            category=category,
            created_time=created_time,
            updated_time=updated_time,
        )  # type: ignore
        db.session.add(post)
    db.session.commit()


def fake_comments(count: int = 200) -> None:
    post_count: int = db.session.scalars(select(func.count(Post.id))).one()
    for _ in range(count):
        post: Post = db.session.get(Post, random.randint(1, post_count))  # type: ignore
        created_time: datetime = fake.date_time_between_dates(datetime_start=post.created_time, datetime_end=datetime(2024, 3, 1))
        updated_time: datetime = fake.date_time_between_dates(datetime_start=created_time, datetime_end=datetime(2024, 4, 1))
        comment = Comment(
            author=fake.name(),
            email=fake.email(),
            site=fake.url(),
            body=fake.sentence(),
            created_time=created_time,
            updated_time=updated_time,
            reviewed=bool(random.randrange(0, 10)),
            from_admin=not bool(random.randrange(0, 20)),
            post=post,
        )
        if not comment.from_admin and comment.reviewed:  # type: ignore
            reviewed_time: datetime = fake.date_time_between_dates(datetime_start=updated_time, datetime_end=datetime(2024, 4, 10))
            comment.reviewed_time = reviewed_time  # type: ignore
        db.session.add(comment)
    db.session.commit()


def fake_replies(count: int = 50) -> None:
    comment_count: int = db.session.scalars(select(func.count(Comment.id))).one()
    for _ in range(count):
        replied: Comment = db.session.get(Comment, random.randint(1, comment_count))  # type: ignore
        created_time: datetime = fake.date_time_between_dates(datetime_start=replied.created_time, datetime_end=datetime(2024, 4, 15))
        updated_time: datetime = fake.date_time_between_dates(datetime_start=created_time, datetime_end=datetime(2024, 4, 20))
        reply = Comment(
            author=fake.name(),
            email=fake.email(),
            site=fake.url(),
            body=fake.sentence(),
            created_time=created_time,
            updated_time=updated_time,
            reviewed=True,
            reviewed_time=updated_time,
            from_admin=not bool(random.randrange(0, 20)),
            replied=replied,
            post=replied.post,
        )
        db.session.add(reply)
    db.session.commit()


def fake_links() -> None:
    helloflask = Link(name='HelloFlask', url='https://helloflask.com')  # type: ignore
    github = Link(name='GitHub', url='https://github.com/greyli')  # type: ignore
    twitter = Link(name='Twitter', url='https://twitter.com/greylihui')  # type: ignore
    linkedin = Link(name='LinkedIn', url='https://www.linkedin.com/in/greyli/')  # type: ignore
    google = Link(name='Stack Overflow', url='https://stackoverflow.com/users/5511849/grey-li')  # type: ignore
    db.session.add_all([helloflask, github, twitter, linkedin, google])
    db.session.commit()
