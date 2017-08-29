import os, unittest
from app import app, main, lm, db
from app.models import User, get_user_by
from config import basedir_join
from sqlalchemy.exc import IntegrityError


class TestCase(unittest.TestCase):
    def setUp(self):
        app.config.from_pyfile(basedir_join('config.py')['path'])
        app.register_blueprint(main)
        lm.init_app(app)
        lm.login_view                         = 'main.login'
        self.app                              = app.test_client()
        app.config['TESTING']                 = True
        app.config['WTF_CSRF_ENABLED']        = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + basedir_join('test.db')['path']
        db.create_all()
    
    
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        os.remove(basedir_join('test.db')['path'])
    
    
    def test_application_structure(self):
        for element in ('app/',
                        'app/static/',
                        'app/static/style.css',
                        'app/templates/',
                        'app/templates/index.html',
                        'app/templates/base.html',
                        'app/templates/login.html',
                        'app/templates/menu.html',
                        'app/templates/chat.html',
                        'app/templates/404.html',
                        'app/templates/500.html',
                        'chat-logs/',
                        'config.py',
                        'run.py',
                        'tests.py'):
            self.assertTrue(basedir_join(element)['exists'],\
                            '"{}" is not exists'.format(element))
    
    
    def test_user_adding_in_db_and_unique_existence(self):
        first_user = User(username = 'user', password = 'pass')
        self.assertNotEqual(first_user, None, 'User entity is not created')
        db.session.add(first_user)
        db.session.commit()
        # Checked that first user object successfully created
        
        first_user = get_user_by(username = 'user')
        self.assertNotEqual(first_user, None, 'User is not added in DB')
        self.assertEqual((first_user.username, first_user.password), ('user', 'pass'),\
                         'DB and registration user data are not equal')
        # Checked that first user successfully added in database without registration information corruption
        
        second_user = User(username = 'user', password = '111111')
        db.session.add(second_user)
        self.assertRaises(IntegrityError, lambda: db.session.commit())
        # Checked that impossible to add second user due to identical usernames
    
    
    def test_user_registration(self):
        """ Registration testing through the server\client request and responses """
        def wrap_function(method, path, contains_string, error_message, data = None):
            if method == 'get':
                response = self.app.get(path, follow_redirects = True)
            if method == 'post':
                response = self.app.post(path, data = data, follow_redirects = True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(contains_string, str(response.data), error_message)
        
        wrap_function(method          = 'get',
                      path            = '/login',
                      contains_string = '<div class="h1">Sign in</div>',
                      error_message   = 'Not valid login page')
        
        wrap_function(method          = 'get',
                      path            = '/username_check?username=wr,o ng',
                      contains_string = '"username_validated": false',
                      error_message   = 'Not valid username validation')
        
        wrap_function(method          = 'post',
                      path            = '/login',
                      data            =  {'username': 'newcomer', 'password': 'password'},
                      contains_string = '<div id="chatlist" class="container"></div>',
                      error_message   = 'Not valid registration and authentication')
        
        wrap_function(method          = 'get',
                      path            = '/logout',
                      contains_string = '<div class="h1">Sign in</div>',
                      error_message   = 'Not valid logout')
        
        wrap_function(method          = 'get',
                      path            = '/username_check?username=newcomer',
                      contains_string = '"username_exists": true',
                      error_message   = 'User is not registered')
        
        wrap_function(method          = 'post',
                      path            = '/login',
                      data            =  {'username': 'newcomer', 'password': 'wrong_password'},
                      contains_string = '<div class="h3">Wrong password</div>',
                      error_message   = 'Not valid password checking')


if __name__ == '__main__':
    unittest.main()
