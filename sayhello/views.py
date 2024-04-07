from flask import flash, redirect, render_template, url_for
from werkzeug import Response

from . import app, db
from .forms import HelloForm
from .models import Message


@app.route('/', methods=['GET', 'POST'])
def index() -> Response | str:
    form = HelloForm()
    if form.validate_on_submit():
        message = Message(
            name=form.name.data,
            body=form.body.data,
        )
        db.session.add(message)
        db.session.commit()
        flash('Your message have been sent to the world!')
        return redirect(url_for('index'))

    messages = db.session.execute(db.select(Message).order_by(Message.timestamp.desc())).scalars().all()
    return render_template('index.html', form=form, messages=messages)
