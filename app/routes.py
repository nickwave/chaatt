from flask import render_template, jsonify, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from app import app, main, socketio
from app.forms import LoginForm, CreateChatForm
from app.models import get_user_by, register_user, get_chat_by, create_chat
from re import search


@main.route('/favicon')
@main.route('/favicon.ico')
def favicon():
    return redirect(url_for('static', filename = 'favicon.ico'))


@main.route('/')
@main.route('/index')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.menu'))
    else:
        return redirect(url_for('main.login'))


@main.route('/logout')
@login_required
def logout():
    for chat in get_chat_by(user = current_user):
        socketio.emit('redirect_via_route',\
                     {'redirect_url': url_for('main.login'),\
                      'username'    : current_user.username}, room = chat.title)
    logout_user()
    return redirect(url_for('main.login'))


@main.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html', title        = 'Sign In',\
                                             form         = LoginForm(),\
                                             current_user = current_user)
    else:
        username = request.form['username']
        password = request.form['password']
        if not True in (search(r'^$|[, ]', field) for field in (username, password)):
            user = get_user_by(username = username)
            if user is None:
                register_user(username, password)
                user = get_user_by(username = username)
                login_user(user)
                return redirect(url_for('main.menu'))
            elif user.is_authenticated(password):
                login_user(user)
                return redirect(url_for('main.menu'))
            else:
                return redirect(url_for('main.login')),\
                       flash('Wrong password')
        else:
            return redirect(url_for('main.login')),\
                   flash('Username or password is not valid')


@main.route('/username_check')
def username_check():
    username           = request.args.get('username', type = str)
    username_validated = True if not search(r'^$|[, ]', username) else False
    username_exists    = True if get_user_by(username=username) else False
    return jsonify(username           = username,\
                   username_validated = username_validated,\
                   username_exists    = username_exists)


@main.route('/get_chatlist')
@login_required
def get_chatlist():
    chatlist = (chat.title for chat in get_chat_by(user=current_user))
    return jsonify(chatlist = tuple(chatlist))


@main.route('/menu')
@login_required
def menu():
    return render_template('menu.html', title        = 'Menu',\
                                        form         = CreateChatForm(),\
                                        current_user = current_user)


@main.route('/chat_creation', methods = ['POST'])
@login_required
def chat_creation():
    title = request.form['title']
    if search(r'^$|[, ]', title):
        return redirect(url_for('main.menu')),\
               flash('Chat title contains unallowable characters')
    elif get_chat_by(title = title) is not None:
        return redirect(url_for('main.menu')),\
               flash('This chat already exists')
    else:
        return redirect(url_for('main.chat', title = title)),\
               create_chat(title, current_user)


@main.route('/chat/<string:title>')
@login_required
def chat(title):
    chat = get_chat_by(title = title)
    if chat is None or not chat.contains_user(current_user):
        return redirect(url_for('main.menu'))
    else:
        users = tuple((user for user in chat.users_in_chat))
        return render_template('chat.html', title        = title,\
                                            users        = users,\
                                            current_user = current_user)


@main.route('/decline_chat/<string:title>')
@login_required
def decline_chat(title):
    get_chat_by(title = title).remove_user(current_user)
    return redirect(url_for('main.menu'))


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', title        = 'Error - 404',\
                                       current_user = current_user), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html', title        = 'Error - 500',\
                                       current_user = current_user), 500
