import os


def basedir_join(path):
    path = os.path.join(os.path.abspath(os.path.dirname(__file__)), path)
    return {  'path': path,
            'exists': os.path.exists(path)}


SQLALCHEMY_DATABASE_URI = 'sqlite:///' + basedir_join('app.db')['path']
SQLALCHEMY_TRACK_MODIFICATIONS = True
CSRF_ENABLED = True
WTF_CSRF_ENABLED = True
SECRET_KEY = os.environ.get('SECRET_KEY') or 'pn9vd0uqc1e&^e4(t01dtzqce5^68hhpd2yrm7p^&#)@(z^vj1'
