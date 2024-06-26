from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug import Response

from . import app, db
from .models import Movie, User


@app.route('/', methods=['GET', 'POST'])
def index() -> str | Response:
    if request.method == 'GET':
        movies = db.session.scalars(db.select(Movie)).all()
        return render_template('index.html', movies=movies)

    if not current_user.is_authenticated:
        return redirect(url_for('index'))

    title = request.form['title']
    year = request.form['year']
    if not title or not year or len(year) > 4 or len(title) > 60:
        flash('Invalid input.')
        return redirect(url_for('index'))

    movie = Movie(title=title, year=year)  # type: ignore
    db.session.add(movie)
    db.session.commit()
    flash('Item created.')
    return redirect(url_for('index'))


@app.route('/movie/edit/<int:movie_id>', methods=['GET', 'POST'])
@login_required
def edit(movie_id) -> str | Response:
    movie = db.get_or_404(Movie, movie_id)
    if request.method == 'GET':
        return render_template('edit.html', movie=movie)

    title = request.form['title']
    year = request.form['year']
    if not title or not year or len(year) > 4 or len(title) > 60:
        flash('Invalid input.')
        return redirect(url_for('edit', movie_id=movie_id))

    movie.title = title
    movie.year = year
    db.session.commit()
    flash('Item updated.')
    return redirect(url_for('index'))


@app.route('/movie/delete/<int:movie_id>', methods=['POST'])
@login_required
def delete(movie_id) -> Response:
    movie = db.get_or_404(Movie, movie_id)
    db.session.delete(movie)
    db.session.commit()
    flash('Item deleted.')
    return redirect(url_for('index'))


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings() -> str | Response:
    if request.method == 'GET':
        return render_template('settings.html')

    name = request.form['name']
    if not name or len(name) > 20:
        flash('Invalid input.')
        return redirect(url_for('settings'))

    user = db.first_or_404(db.select(User))
    user.name = name
    db.session.commit()
    flash('Settings updated.')
    return redirect(url_for('index'))


@app.route('/login', methods=['GET', 'POST'])
def login() -> str | Response:
    if request.method == 'GET':
        return render_template('login.html')

    username = request.form['username']
    password = request.form['password']
    if not username or not password:
        flash('Invalid input.')
        return redirect(url_for('login'))

    user = db.first_or_404(db.select(User))
    if user and username == user.username and user.validate_password(password):
        login_user(user)
        flash('Login success.')
        return redirect(url_for('index'))

    flash('Invalid username or password.')
    return redirect(url_for('login'))


@app.route('/logout')
@login_required
def logout() -> Response:
    logout_user()
    flash('Goodbye.')
    return redirect(url_for('index'))
