from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import timedelta, datetime
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd

app = Flask(__name__)
app.secret_key = "hello"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.permanent_session_lifetime = timedelta(hours=12)

db = SQLAlchemy(app)


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def __init__(self, name, username, email, password, is_admin=False):
        self.name = name
        self.username = username
        self.email = email
        self.password = generate_password_hash(password)
        self.is_admin = is_admin



class TimeOffRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    period = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('Users', backref=db.backref('time_off_requests', lazy=True))


@app.route('/')
def index():
    if 'user' in session:
        username = session['user']
        user = Users.query.filter_by(username=username).first()
        is_admin = user.is_admin
        return render_template('index.html', user=user, is_admin=is_admin)  # Pass the user object to the template
    else:
        return render_template('index.html')


@app.route('/schedule')
def schedule():
    if 'user' not in session:
        flash('You need to log in to view this page.', 'danger')
        return redirect(url_for('login'))

    file_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'updated_schedule.xlsx')
    try:
        df = pd.read_excel(file_path)
        data = df.to_html()
    except FileNotFoundError as e:
        print(e)  # Print the error to help with debugging
        data = "File not found."

    username = session['user']
    user = Users.query.filter_by(username=username).first()
    is_admin = user.is_admin
    return render_template('schedule.html', data=data, is_admin=is_admin)



@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        flash('You are already logged in!', 'info')
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = Users.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user'] = user.username  # Store username in session
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password. Please try again.', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user' in session:
        flash('You are already logged in!', 'info')
        return redirect(url_for('index'))

    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        username = request.form.get('username')

        if not first_name or not last_name or not email or not password or not username:
            flash('All fields are required.', 'error')
            return redirect(url_for('register'))

        full_name = f"{first_name} {last_name}"

        if Users.query.filter_by(username=username).first():
            flash('Username already exists!', 'danger')
            return redirect(url_for('register'))

        if Users.query.filter_by(email=email).first():
            flash('Email address already registered!', 'danger')
            return redirect(url_for('register'))

        # Check if this is the first user to be registered
        is_admin = Users.query.count() == 0

        new_user = Users(name=full_name, username=username, email=email, password=password, is_admin=is_admin)
        db.session.add(new_user)
        db.session.commit()
        flash('You have been registered successfully!', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')



@app.route('/user', methods=['GET', 'POST'])
def user():
    if 'user' not in session:
        flash('You need to log in to view this page.', 'danger')
        return redirect(url_for('login'))

    username = session['user']
    user = Users.query.filter_by(username=username).first()

    if request.method == 'POST':
        email = request.form['email']
        user.email = email
        db.session.commit()
        flash('Email updated successfully.', 'success')

    time_off_requests = TimeOffRequest.query.filter_by(user_id=user.id).all()
    formatted_requests = [
        {'id': request.id, 'date': request.date.strftime('%m-%d-%Y'), 'period': request.period} for request in time_off_requests
    ]


    return render_template('user.html', user=user, time_off_requests=formatted_requests, is_admin = user.is_admin)


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/request_time_off', methods=['GET', 'POST'])
def request_time_off():
    if 'user' not in session:
        flash('You need to log in to view this page.', 'danger')
        return redirect(url_for('login'))

    username = session['user']
    user = Users.query.filter_by(username=username).first()
    is_admin = user.is_admin

    if request.method == 'POST':
        date = request.form['date']
        period = request.form['period']

        try:
            date = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format. Please use YYYY-MM-DD.', 'danger')
            return redirect(url_for('request_time_off'))



        new_request = TimeOffRequest(user_id=user.id, date=date, period=period)
        db.session.add(new_request)
        db.session.commit()

        flash('Time off request submitted successfully.', 'success')
        return redirect(url_for('request_time_off'))

    return render_template('request_time_off.html', is_admin=is_admin)

@app.route('/delete_time_off/<int:time_off_id>', methods=['POST'])
def delete_time_off(time_off_id):
    if 'user' not in session:
        flash('You need to log in to perform this action.', 'danger')
        return redirect(url_for('login'))

    time_off_request = TimeOffRequest.query.get(time_off_id)
    if not time_off_request:
        flash('Time off request not found.', 'danger')
    else:
        db.session.delete(time_off_request)
        db.session.commit()
        flash('Time off request deleted successfully.', 'success')

    return redirect(url_for('user'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'user' not in session:
        flash('You need to log in to view this page.', 'danger')
        return redirect(url_for('login'))

    username = session['user']
    user = Users.query.filter_by(username=username).first()

    if not user.is_admin:
        flash('You do not have permission to view this page.', 'danger')
        return redirect(url_for('index'))

    users = Users.query.all()
    user_data = []
    for user in users:
        time_off_requests = TimeOffRequest.query.filter_by(user_id=user.id).all()
        formatted_requests = [
            {'id': request.id, 'date': request.date.strftime('%m-%d-%Y'), 'period': request.period} for request in time_off_requests
        ]
        user_data.append({'user': user, 'time_off_requests': formatted_requests})

    return render_template('admin.html', user_data=user_data, is_admin=user.is_admin)



@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if 'user' not in session:
        flash('You need to log in to perform this action.', 'danger')
        return redirect(url_for('login'))

    current_user = Users.query.filter_by(username=session['user']).first()
    if not current_user.is_admin:
        flash('You do not have permission to perform this action.', 'danger')
        return redirect(url_for('index'))

    user_to_delete = Users.query.get(user_id)
    if not user_to_delete:
        flash('User not found.', 'danger')
        return redirect(url_for('admin'))

    # Delete user's time off requests
    TimeOffRequest.query.filter_by(user_id=user_id).delete()

    db.session.delete(user_to_delete)
    db.session.commit()
    flash('User deleted successfully.', 'success')
    return redirect(url_for('admin'))


@app.route('/reset_db')
def reset_db():
    db.drop_all()
    db.create_all()
    flash('Database has been reset!', 'info')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
