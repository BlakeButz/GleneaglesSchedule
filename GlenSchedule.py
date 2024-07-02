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

    def __init__(self, name, username, email, password):
        self.name = name
        self.username = username
        self.email = email
        self.password = generate_password_hash(password)


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
        return render_template('index.html', user=user)  # Pass the user object to the template
    else:
        return render_template('index.html')


@app.route('/schedule')
def schedule():
    file_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'updated_schedule.xlsx')
    try:
        df = pd.read_excel(file_path)
        data = df.to_html()
    except FileNotFoundError as e:
        print(e)  # Print the error to help with debugging
        data = "File not found."
    return render_template('schedule.html', data=data)


@app.route("/view")
def view():
    users = Users.query.all()
    return render_template("view.html", users=users)


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

        new_user = Users(username=username, name=full_name, email=email, password=password)
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

    return render_template('user.html', user=user, time_off_requests=time_off_requests)


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/delete', methods=['GET', 'POST'])
def delete():
    for time in TimeOffRequest.query.all():
        db.session.delete(time)
    for user in Users.query.all():
        db.session.delete(user)
    db.session.commit()
    flash('Users Deleted!', 'info')

    return redirect(url_for('logout'))


@app.route('/request_time_off', methods=['GET', 'POST'])
def request_time_off():
    if 'user' not in session:
        flash('You need to log in to view this page.', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        date = request.form['date']
        period = request.form['period']

        # Convert date to a datetime object for storage (if needed)
        try:
            date = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format. Please use YYYY-MM-DD.', 'danger')
            return redirect(url_for('request_time_off'))

        username = session['user']
        user = Users.query.filter_by(username=username).first()

        if user:
            new_request = TimeOffRequest(user_id=user.id, date=date, period=period)
            db.session.add(new_request)
            db.session.commit()

            flash('Time off request submitted successfully.', 'success')
            return redirect(url_for('request_time_off'))
        else:
            flash('User not found.', 'danger')
            return redirect(url_for('request_time_off'))

    return render_template('request_time_off.html')

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



@app.route('/reset_db')
def reset_db():
    db.drop_all()
    db.create_all()
    flash('Database has been reset!', 'info')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
