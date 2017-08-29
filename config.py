import os


def basedir_join(path):
    path = os.path.join(os.path.abspath(os.path.dirname(__file__)), path)
    return {  'path': path,
            'exists': os.path.exists(path)}


SECRET_KEY                     = os.environ.get('SECRET_KEY') or '05^68hhppn9vdd2yrmte7p^&uqczqc1@(z^vj1e&^e4(t01d#)'
CSRF_ENABLED                   = True
WTF_CSRF_ENABLED               = True
SQLALCHEMY_DATABASE_URI        = 'sqlite:///' + basedir_join('app.db')['path']
SQLALCHEMY_TRACK_MODIFICATIONS = True
