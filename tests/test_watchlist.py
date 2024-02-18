import pytest

from watchlist import app, db
from watchlist.commands import forge, initdb
from watchlist.models import Movie, User


@pytest.fixture(scope='session')
def setup_method():
    with app.app_context():
        app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI='sqlite:///:memory:')
        db.create_all()
        user = User(name='Test', username='test')
        user.set_password('123')
        movie = Movie(title='Test Movie Title', year='2019')
        db.session.add_all([user, movie])
        db.session.commit()

        global client, runner

        client = app.test_client()
        runner = app.test_cli_runner()

    yield

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.mark.usefixtures('setup_method')
class TestWatchlist:
    def login(self):
        client.post('/login', data=dict(username='test', password='123'), follow_redirects=True)

    def test_app_exist(self):
        assert app is not None

    def test_app_is_testing(self):
        assert app.config['TESTING'] is True

    def test_404_page(self):
        response = client.get('/nothing')
        assert response.status_code == 404
        assert b'404' in response.data
        assert b'Page Not Found' in response.data
        assert b'Go Back' in response.data

    def test_index_page(self):
        response = client.get('/')
        assert response.status_code == 200
        assert b"Test's Watchlist" in response.data
        assert b'Test Movie Title' in response.data

    def test_login_protect(self):
        response = client.get('/')
        data = response.get_data(as_text=True)
        assert 'Login' in data
        assert 'Logout' not in data
        assert 'Settings' not in data
        assert '<form method="post">' not in data
        assert 'Delete' not in data
        assert 'Edit' not in data

        response = client.post('/')
        data = response.get_data(as_text=True)
        assert 'Login' not in data
        assert 'Logout' not in data
        assert 'Settings' not in data
        assert '<form method="post">' not in data
        assert 'Delete' not in data
        assert 'Edit' not in data

    def test_login(self):
        response = client.post('/login', data=dict(username='test', password='123'), follow_redirects=True)
        data = response.get_data(as_text=True)
        assert 'Login success.' in data
        assert 'Logout' in data
        assert 'Settings' in data
        assert 'Delete' in data
        assert 'Edit' in data
        assert '<form method="post">' in data

        response = client.post('/login', data=dict(username='test', password='456'), follow_redirects=True)
        data = response.get_data(as_text=True)
        assert 'Login success' not in data
        assert 'Invalid username or password.' in data

        response = client.post('/login', data=dict(username='wrongname', password='123'), follow_redirects=True)
        data = response.get_data(as_text=True)
        assert 'Login success' not in data
        assert 'Invalid username or password.' in data

        response = client.post('/login', data=dict(username='', password='123'), follow_redirects=True)
        data = response.get_data(as_text=True)
        assert 'Login success' not in data
        assert 'Invalid input.' in data

        response = client.post('/login', data=dict(username='test', password=''), follow_redirects=True)
        data = response.get_data(as_text=True)
        assert 'Login success' not in data
        assert 'Invalid input.' in data

    def test_logout(self):
        self.login()

        response = client.get('/logout', follow_redirects=True)
        data = response.get_data(as_text=True)
        assert 'Goodbye.' in data
        assert 'Login' in data
        assert 'Logout' not in data
        assert 'Settings' not in data
        assert 'Delete' not in data
        assert 'Edit' not in data
        assert '<form method="post">' not in data

    def test_settings(self):
        self.login()

        response = client.get('/settings')
        data = response.get_data(as_text=True)
        assert 'Settings' in data
        assert 'Your Name' in data

        response = client.post('/settings', data=dict(name='Grey Li'), follow_redirects=True)
        data = response.get_data(as_text=True)
        assert 'Settings updated.' in data
        assert 'Grey Li' in data

        response = client.post('/settings', data=dict(name=''), follow_redirects=True)
        data = response.get_data(as_text=True)
        assert 'Settings updated.' not in data
        assert 'Invalid input.' in data

    def test_create_item(self):
        self.login()
        response = client.post('/', data=dict(title='New Movie', year='2019'), follow_redirects=True)
        data = response.get_data(as_text=True)
        assert 'Item created.' in data
        assert 'New Movie' in data

        response = client.post('/', data=dict(title='', year='2019'), follow_redirects=True)
        data = response.get_data(as_text=True)
        assert 'Item created.' not in data
        assert 'Invalid input.' in data

        response = client.post('/', data=dict(title='New Movie', year=''), follow_redirects=True)
        data = response.get_data(as_text=True)
        assert 'Item created.' not in data
        assert 'Invalid input.' in data

    def test_update_item(self):
        self.login()
        response = client.get('/movie/edit/1')
        data = response.get_data(as_text=True)
        assert 'Edit item' in data
        assert 'Test Movie Title' in data
        assert '2019' in data

        response = client.post('/movie/edit/1', data=dict(title='New Movie Title', year='2019'), follow_redirects=True)
        data = response.get_data(as_text=True)
        assert 'Item updated.' in data
        assert 'New Movie Title' in data

        response = client.post('/movie/edit/1', data=dict(title='', year='2019'), follow_redirects=True)
        data = response.get_data(as_text=True)
        assert 'Item updated.' not in data
        assert 'Invalid input.' in data

        response = client.post('/movie/edit/1', data=dict(title='New Movie Title Again', year=''), follow_redirects=True)
        data = response.get_data(as_text=True)
        assert 'Item updated.' not in data
        assert 'New Movie Title Again' not in data
        assert 'Invalid input.' in data

    def test_delete_item(self):
        self.login()

        response = client.post('/movie/delete/1', follow_redirects=True)
        data = response.get_data(as_text=True)
        assert 'Item deleted.' in data
        assert 'Test Movie Title' not in data

    def test_forge_command(self):
        result = runner.invoke(forge)
        assert result.exit_code == 0
        assert 'Done.' in result.output
        with app.app_context():
            assert db.session.scalar(db.select(db.func.count(Movie.id))) != 0

    def test_initdb_command(self):
        result = runner.invoke(initdb)
        assert 'Initialized database.' in result.output

    def test_admin_command(self):
        with app.app_context():
            db.drop_all()
            db.create_all()
            result = runner.invoke(args=['admin', '--username', 'grey', '--password', '123'])
        assert result.exit_code == 0
        assert 'Creating user...' in result.output
        assert 'Done.' in result.output
        with app.app_context():
            assert db.session.scalar(db.select(db.func.count(User.id))) == 1
            assert db.first_or_404(db.select(User)).username == 'grey'
            assert db.first_or_404(db.select(User)).validate_password('123')

    def test_admin_command_update(self):
        with app.app_context():
            result = runner.invoke(args=['admin', '--username', 'peter', '--password', '456'])
        assert 'Updating user...' in result.output
        assert 'Done.' in result.output
        with app.app_context():
            assert db.session.scalar(db.select(db.func.count(User.id))) == 1
            assert db.first_or_404(db.select(User)).username == 'peter'
            assert db.first_or_404(db.select(User)).validate_password('456')
