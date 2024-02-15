from flask import Blueprint, request, redirect, url_for, render_template, session, current_app, g
from .user import User
from functools import wraps


def check_access(f):

    @wraps(f)
    def wrapper(*args, **kwargs):
        if g.user is None and User.at_least_one_exists():
            current_app.logger.info(f'ACCESS DENIED: {request.url}')
            return redirect(url_for('auth.login', next_url=request.url))
        return f(*args, **kwargs)

    return wrapper


def make_bp(tmp_path: str):
    User.init(tmp_path)

    bp = Blueprint('auth', __name__, url_prefix='/auth')

    @bp.route('/register', methods=['GET', 'POST'])
    def register():
        next_url = request.args.get('next_url', url_for('content.get'))
        if request.method == 'POST':
            name = request.form.get('username')
            password = request.form.get('password')

            user = User(name)
            user.register(password)
            current_app.logger.info(f'REGISTER: {user.id}')
            return redirect(url_for('auth.login', next_url=next_url))

        return render_template('auth/register.html.jinja2', next_url=next_url)

    @bp.route('/login', methods=['GET', 'POST'])
    def login():
        next_url = request.args.get('next_url', url_for('content.get'))
        if request.method == 'POST':
            name = request.form.get('username')
            password = request.form.get('password')

            user = User(name)
            if user.login(password):
                session.clear()
                session['user_id'] = user.id
                current_app.logger.info(f'LOGIN: {user.id}')
                return redirect(next_url)

        return render_template('auth/login.html.jinja2', next_url=next_url)

    @bp.route('/logout')
    def logout():
        session.clear()
        if g.user is not None:
            g.user.logout()
        return redirect(url_for('content.get'))

    @bp.before_app_request
    def get_logged_in_user():
        user_id = session.get('user_id')

        g.user = None
        if user_id is not None:
            user = User(user_id)
            if user.is_online():
                g.user = user
            else:
                session.clear()

    return bp
