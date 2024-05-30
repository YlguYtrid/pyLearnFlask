from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user,
)
from sqlalchemy import select
from werkzeug.wrappers.response import Response

from ..core.extensions import db
from ..forms import LoginForm
from ..models import Admin
from ..utils import redirect_back

bp_auth = Blueprint('auth', __name__)


@bp_auth.route('/login', methods=['GET', 'POST'])
def login() -> Response | str:
    if current_user.is_authenticated:
        return redirect(url_for('blog.index'))
    form = LoginForm()
    match request.method:
        case 'GET':
            pass
        case 'POST':
            if form.validate_on_submit():
                admin: Admin | None = db.session.scalar(select(Admin))
                if admin:
                    if admin == form:
                        login_user(admin, form.remember.data)
                        flash('Welcome back.', 'info')
                        return redirect_back()

                    flash('Invalid username or password.', 'warning')
                else:
                    flash('No account found.', 'warning')
    return render_template('auth/login.html', form=form)


@bp_auth.route('/logout')
@login_required
def logout() -> Response:
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect_back()
