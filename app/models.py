from flask_login import UserMixin
from app import db, lm, bcrypt
from random import randint
from config import basedir_join
from os import remove
from re import search


@lm.user_loader
def get_user(ident):
    return User.query.get(int(ident))

    
def get_user_by(username = None, color = None):
    if username is not None:
        return User.query.filter_by(username = username).first()
    if color is not None:
        return User.query.filter_by(color = color).first()


def register_user(username, password):
    user = User(username = username,\
                password = bcrypt.generate_password_hash(password).decode('utf-8'))
    user.color = user.generate_unique_color()
    db.session.add(user)
    db.session.commit()


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key = True)
    username      = db.Column(db.String(64),   unique = True)
    password      = db.Column(db.String(64))
    color         = db.Column(db.String(16),   unique = True)
    
    
    def generate_unique_color(self):
        color = 'rgb({},{},{})'.format(*(randint(0, 256) for i in range(3)))
        if get_user_by(color = color) is None:
            return color
        else:
            self.generate_unique_color()
    
    
    def is_authenticated(self, password):
        if bcrypt.check_password_hash(self.password, password):
            self.color = self.generate_unique_color()
            db.session.commit()
            return True
        else:
            return False
    
    
    def is_added_to_chat(self, title):
        users_in_chat = get_chat_by(title = title).users_in_chat
        return any(tuple(filter(lambda u: u.username == self.username, users_in_chat)))


def get_chat_by(title = None, user = None):
    if title is not None:
        return Chat.query.filter_by(title = title).first()
    if user is not None:
        return tuple(filter(lambda chat: user in chat.users_in_chat, Chat.query.all()))


def create_chat(title, current_user):
    chat = Chat(title = title)
    chat.users_in_chat.append(current_user)
    db.session.add(chat)
    db.session.commit()


class Chat(db.Model):
    __tablename__ = 'chats'
    id            = db.Column(db.Integer, primary_key = True)
    title         = db.Column(db.String(64),   unique = True)
    users_in_chat = db.relationship('User',\
                                    secondary = db.Table('users_in_chat',\
                                                         db.Column('chat_id',\
                                                                   db.Integer,\
                                                                   db.ForeignKey('chats.id')),\
                                                         db.Column('user_id',\
                                                                   db.Integer,\
                                                                   db.ForeignKey('users.id'))))
    
    
    def contains_user(self, user):
        return True if user in self.users_in_chat else False
    
    
    def remove_user(self, current_user):
        self.users_in_chat.remove(current_user)
        if not self.users_in_chat:
            db.session.delete(self)
            remove(basedir_join('chat-logs/{}.log'.format(self.title))['path'])
        db.session.commit()
    
    
    def invite_user(self, username):
        username_validated = True if search(r'^$|[, ]', username) is None else False
        invited_user       = get_user_by(username = username)
        if invited_user is not None:
            self.users_in_chat.append(invited_user)
            db.session.commit()
            return username_validated, True
        else:
            return username_validated, False
