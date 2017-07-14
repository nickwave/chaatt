from flask import render_template, jsonify, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from app import app, main, socketio
from app.forms import LoginForm, CreateChatForm
from app.models import User, Chat
from re import search


@main.route('/favicon')
@main.route('/favicon.ico')
def favicon():
    return redirect(url_for('static', filename='favicon.ico'))


@main.route('/')
@main.route('/index')
def index():
    return redirect(url_for('main.menu') if current_user.is_authenticated else url_for('main.login'))


@main.route('/logout')
@login_required
def logout():
    for chat in Chat.get_chat_by(user=current_user):
        socketio.emit('redirect_via_route', {'redirect_url': url_for('main.login'),
                                             'username'    : current_user.username}, room=chat.title)
    logout_user()
    return redirect(url_for('main.login'))


@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html', title        = 'Sign In',
                                             form         = LoginForm(), 
                                             current_user = current_user)
    else:
        username = request.form['username']
        password = request.form['password']
        if not True in (search(r'^$|[, ]', field) for field in (username, password)):
            user = User.get_user_by(username=username)
            if user is None:
                login_user(User.register_user(username, password))
                return redirect(url_for('main.menu'))
            elif user.is_authenticated(password):
                login_user(user)
                return redirect(url_for('main.menu'))
            else:
                return redirect(url_for('main.login')), flash('Wrong password')
        else:
            return redirect(url_for('main.login')), flash('Username or password is not valid')


@main.route('/username_check')
def username_check():
    username = request.args.get('username', type=str)
    return jsonify(username           = username,
                   username_validated = False if search(r'^$|[, ]', username) else True,
                   username_exists    = False if User.get_user_by(username=username) is None else True)


@main.route('/get_chatlist')
@login_required
def get_chatlist():
    return jsonify(chatlist=[chat.title for chat in Chat.get_chat_by(user=current_user)])


@main.route('/menu')
@login_required
def menu():
    return render_template('menu.html', title        = 'Menu',
                                        form         = CreateChatForm(),
                                        current_user = current_user)


@main.route('/chat_creation', methods=['POST'])
@login_required
def chat_creation():
    title = request.form['title']
    if search(r'^$|[, ]', title):
        return redirect(url_for('main.menu')), flash('Chat title contains unallowable characters')
    elif Chat.get_chat_by(title=title) is not None:
        return redirect(url_for('main.menu')), flash('This chat already exists')
    else:
        return redirect(url_for('main.chat', title=title)), Chat.create_chat(title, current_user)


@main.route('/chat/<string:title>')
@login_required
def chat(title):
    chat = Chat.get_chat_by(title=title)
    if chat is None or not chat.contains_user(current_user):
        return redirect(url_for('main.menu'))
    else:
        return render_template('chat.html', title        = title,
                                            users        = [user for user in chat.users_in_chat],
                                            current_user = current_user)


@main.route('/decline_chat/<string:title>')
@login_required
def decline_chat(title):
    Chat.remove_user_from_chat(title, current_user)
    return redirect(url_for('main.menu'))


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', title        = 'Error - 404',
                                       current_user = current_user), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html', title        = 'Error - 500',
                                       current_user = current_user), 500
