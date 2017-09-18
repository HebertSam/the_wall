from flask import Flask, flash, redirect, render_template, session, request
from mysqlconnection import MySQLConnector
import re, os, md5, binascii

app = Flask(__name__)
mysql = MySQLConnector(app, 'the_wall')
app.secret_key = '12345'
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
PASS_REGEX = re.compile(r'^[a-zA-Z0-9]{8,}')

@app.route('/')
def index():
    if session['user']:
        return redirect('/wall')
    else:
        return render_template('index.html')


@app.route('/register', methods=['POST'])
def register():
    # salt = binascii.b2a_hex(os.urandom(15))
    query1 = "select email from users"
    query2 = "insert into users (first_name, last_name, email, password, created_at, updated_at) values (:first_name, :last_name, :email, :password, now(), now())"

    data = {
        'first_name': request.form['first_name'],
        'last_name': request.form['last_name'],
        'email': request.form['email'],
        'password': md5.new(request.form['password']).hexdigest(),
    }
    print data

    for i in data:
        if len(data[i]) < 2:
            flash('please fill out all fields')
            return redirect('/')
    
    if not EMAIL_REGEX.match(data['email']):
        flash('please enter a valid email')
        return redirect('/')
    
    emails = mysql.query_db(query1)

    for email in emails:
        if email['email'] == data['email']:
            flash('that email has already been used please try another')
            return redirect('/')

    if not PASS_REGEX.match(request.form['password']):
        flash('the password you entered was not strong enough please try again')
        return redirect('/')

    elif data['password'] != md5.new(request.form['con_password']).hexdigest():
        flash('your passwords did not match please try again')
        return redirect('/')

    mysql.query_db(query2, data)

    return redirect('/wall')
@app.route('/login', methods=['post'])
def login():

    query3 = "select email, password, id, first_name from users where users.email = :email LIMIT 1"

    email = {'email': request.form['login_email']}
    password = request.form['login_password']

    user = mysql.query_db(query3, email)

    if len(user) != 0:
        encrypted_password = md5.new(password).hexdigest()
        if user[0]['password'] == encrypted_password:
            session['user'] = user[0]['id']
            session['user_name'] = user[0]['first_name']
            print session['user_name']
            print session['user']
            return redirect('/wall')
        else:
            flash('invalid password')
            return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/wall')
def wall():

    message_data = mysql.query_db('select concat(users.first_name, " ", users.last_name) as user_name, users.id as user_id, messages.message as message, messages.updated_at as time, messages.users_id, messages.id as message_id, comments.comment, comments.messages_id as com_message_id, comments.users_id as comm_user_id, comments.update_at, comments.id as comment_id from users join messages on users.id = messages.users_id join comments on messages_id = comments.messages_id')

    user_data = mysql.query_db('select concat(users.first_name, " ", users.last_name) as user_name, users.id as user_id from users')
    print user_data
  
    
    return render_template('wall.html', message_data=message_data, user_data=user_data)

@app.route('/message', methods=['post'])
def post_message():

    message_query = 'insert into messages(message, users_id, created_at, updated_at) values(:message, :user, now(), now())'

    message_data = {
        'message': request.form['message'],
        'user': session['user']
    }

    print mysql.query_db(message_query, message_data)

    return redirect('/wall')

@app.route('/comment', methods=['post'])
def post_comment():

    comment_query = 'insert into comments(comment, messages_id, users_id, created_at, update_at) values(:comment, :message_id, :user, now(), now())'

    comment_data = {
        'comment': request.form['comment'],
        'message_id': request.form['message_id'],
        'user': session['user']
    }
    mysql.query_db(comment_query, comment_data)
    return redirect('/wall')

@app.route('/message_delete')
def message_delete():

    message_delete_query = 'delete from messages where message.id = :message_id'

    message_id = {'message_id': request.form['message_id']}

    mysql.query_db(message_delete_query, message_id)

@app.route('/comment_delete')
def comment_delete():

    comment_delete_query = 'delete from comments where comments.id = :comment_id'

    comment_id = {'comment_id': request.form['comment_id']}

    mysql.query_db(comment_delete_query, comment_id)

app.run(debug=True)