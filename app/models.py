from flask_login import UserMixin
from app import db, lm, bcrypt
from random import randint
from config import basedir_join
from os import remove
from re import search


@lm.user_loader
def get_user(ident):
    return User.query.get(int(ident))


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key = True)
    username      = db.Column(db.String(64), unique = True)
    password      = db.Column(db.String(64))
    color         = db.Column(db.String(16), unique = True)
    
    
    def generate_unique_color():
        color = 'rgb({},{},{})'.format(*(randint(0, 256) for i in range(3)))
        return color if User.get_user_by(color=color) is None else generate_unique_color()
    
    
    def get_user_by(username=None, color=None):
        if username is not None:
            return User.query.filter_by(username=username).first()
        if color is not None:
            return User.query.filter_by(color=color).first()

    
    def is_authenticated(self, password):
        if bcrypt.check_password_hash(self.password, password):
            self.color = User.generate_unique_color()
            db.session.commit()
            return True
        else:
            return False
            
    def is_added_to_chat(self, title):
        return any(True for user in Chat.get_chat_by(title=title).users_in_chat if user.username == self.username)
    
    
    def register_user(username, password):
        user = User(username = username,
                    password = bcrypt.generate_password_hash(password).decode('utf-8'),
                    color    = User.generate_unique_color())
        db.session.add(user)
        db.session.commit()
        return user


class Chat(db.Model):
    __tablename__ = 'chats'
    id            = db.Column(db.Integer, primary_key = True)
    title         = db.Column(db.String(64), unique=True)
    users_in_chat = db.relationship("User", secondary=db.Table('users_in_chat',
                                                          db.Column('chat_id', db.Integer, db.ForeignKey('chats.id')),
                                                          db.Column('user_id', db.Integer, db.ForeignKey('users.id'))))
    
    
    def get_chat_by(title=None, user=None):
        if title is not None:
            return Chat.query.filter_by(title=title).first()
        if user is not None:
            return (chat for chat in Chat.query.all() if user.username in (user.username for user in chat.users_in_chat))

    
    def contains_user(self, user):
        return True if user in self.users_in_chat else False
    
    
    def create_chat(title, current_user):
        chat = Chat(title=title)
        chat.users_in_chat.append(current_user)
        db.session.add(chat)
        db.session.commit()
    
    
    def remove_user_from_chat(title, current_user):
        chat = Chat.get_chat_by(title=title)
        chat.users_in_chat.remove(current_user)
        if not chat.users_in_chat:
            db.session.delete(chat)
            remove(basedir_join('chat-logs/{}.log'.format(title))['path'])
        db.session.commit()


    def invite_user_in_chat(title, username):
        username_validated = True if search(r'^$|[, ]', username) is None else False
        invited_user = User.get_user_by(username=username)
        if invited_user is not None:
            chat = Chat.get_chat_by(title=title)
            chat.users_in_chat.append(invited_user)
            db.session.commit()
            return username_validated, True
        else:
            return username_validated, False
