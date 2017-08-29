from flask import request, url_for
from flask_login import current_user
from flask_socketio import join_room, leave_room
from app import socketio
from app.models import get_chat_by
from config import basedir_join
from file_read_backwards import FileReadBackwards
from functools import wraps
from csv import reader, writer, QUOTE_ALL


def write_in_file(timestamp, username, message, title):
    cur_id, chat_log = 0, basedir_join('chat-logs/{}.log'.format(title))

    if chat_log['exists']:
        backward_reader = FileReadBackwards(chat_log['path'], 'utf-8')
        for row in reader(backward_reader, delimiter = ',',\
                                           quotechar = '"'):
            cur_id = int(row[0]) + 1
            break
    
    with open(chat_log['path'], 'a') as plain_writer:
        csvwriter = writer(plain_writer, delimiter = ',',\
                                         quotechar = '"',\
                                         quoting   = QUOTE_ALL)
        
        new_row   = (cur_id, timestamp, username,\
                     message.replace('<', '&le').replace('>', '&ge'))
        
        csvwriter.writerow(tuple(new_row))


def read_from_file(clients_cur_msg_id, title):
    messages        = []
    cur_msg_id      = None
    chat_log        = basedir_join('chat-logs/{}.log'.format(title))
    backward_reader = FileReadBackwards(chat_log['path'], 'utf-8')

    for row in reader(backward_reader, delimiter = ',',\
                                       quotechar = '"'):
        if cur_msg_id is None:
            cur_msg_id = row[0]
        if int(row[0]) == int(clients_cur_msg_id):
            break
        messages.append({'timestamp': row[1],
                         'username' : row[2],
                         'text'     : row[3]})
    
    return messages[::-1], cur_msg_id


def auth_required(initial_function):
    @wraps(initial_function)
    def decorated_function(message):
        if current_user.is_authenticated and\
           current_user.is_added_to_chat(message['title']):
            return initial_function(message)
        else:
            socketio.emit('redirect_via_event',\
                         {'redirect_url': url_for('main.menu')}, room = request.sid)
    return decorated_function


def control_message_processor(initial_function):
    @wraps(initial_function)
    def decorated_function(message):
        if message['control_message'] == 'join':
            join_room(message['title'])
        if message['control_message'] == 'leave':
            leave_room(message['title'])
        return initial_function(message)
    return decorated_function


@socketio.on('write_message')
@control_message_processor
@auth_required
def write_message(message):
    if message['control_message'] == 'join':
        author, text = 'System', '{} has joined the chat'.format(current_user.username)
    
    if message['control_message'] == 'message':
        author, text = current_user.username, message['message']
    
    if message['control_message'] == 'leave':
        author, text = 'System', '{} has left the chat'.format(current_user.username)
    
    write_in_file(message['timestamp'], author, text, message['title'])
    socketio.emit('chat_content_updated', room=message['title'])


@socketio.on('read_messages')
@control_message_processor
@auth_required
def read_messages(message):
    messages, cur_msg_id = read_from_file(message['cur_msg_id'], message['title'])
    
    users = tuple(map(lambda u: {'username': u.username, 'color': u.color},\
                      get_chat_by(title = message['title']).users_in_chat))
    
    socketio.emit('update_messages', {'messages'  : messages,
                                      'cur_msg_id': cur_msg_id,
                                      'users'     : users}, room = request.sid)


@socketio.on('invite_user')
@auth_required
def invite_user(message):
    chat  = get_chat_by(title = message['title'])
    users = tuple(map(lambda u: {'username': u.username, 'color': u.color},\
                      chat.users_in_chat))
    
    username_validated, user_exists = chat.invite_user(message['username'])
    
    socketio.emit('users_update', {'username'          : message['username'],
                                   'current_user'      : current_user.username,
                                   'username_validated': username_validated,
                                   'user_exists'       : user_exists,
                                   'users'             : users}, room = message['title'])
