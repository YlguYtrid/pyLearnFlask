import click

from . import app, db
from .models import Message


@app.cli.command()
@click.option('--drop', is_flag=True, help='Create after drop.')
def initdb(drop) -> None:
    """Initialize the database."""
    if drop:
        click.confirm('This operation will delete the database, do you want to continue?', abort=True)
        db.drop_all()
        click.echo('Drop tables.')
    db.create_all()
    click.echo('Initialized database.')


@app.cli.command()
@click.option('--count', default=20, help='Quantity of messages, default is 20.')
def forge(count) -> None:
    """Generate fake messages."""
    from faker import Faker

    fake = Faker()
    click.echo('Working...')
    for _ in range(count):
        message = Message(
            name=fake.name(),
            body=fake.sentence(),
            timestamp=fake.date_time_this_year(),
        )
        db.session.add(message)
    db.session.commit()
    click.echo(f'{count} fake messages were created.')
