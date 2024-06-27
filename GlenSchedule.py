from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = "hello"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.permanent_session_lifetime = timedelta(days=5)

db = SQLAlchemy(app)


class users(db.Model):
    _id = db.Column("id", db.Integer, primary_key=True)
    name = db.Column("name", db.String(100), nullable=False)
    email = db.Column("email", db.String(100), nullable=False)
    password = db.Column("password", db.String(100), nullable=False)

    def __init__(self, name, password, email):
        self.name = name
        self.password = password
        self.email = email

@app.route('/')
def index():
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
    return render_template("view.html", values=users.query.all())


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session.permanent = True
        user = request.form.get('user')

        if not user:
            flash('Username is required.', 'error')
            return redirect(url_for('login'))

        session['user'] = user

        found_user = users.query.filter_by(name=user).first()
        if found_user:
            session['email'] = found_user.email
            flash('You were logged in successfully!', 'success')
            return redirect(url_for('user'))
        else:
            flash('User does not exist. Please register.', 'error')
            return redirect(url_for('register'))
    else:
        if "user" in session:
            flash('Already logged in!', 'info')
            return redirect(url_for('user'))
        return render_template("login.html")


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        if not name or not email or not password:
            flash('All fields are required.', 'error')
            return redirect(url_for('register'))

        if users.query.filter_by(name=name).first():
            flash('Username already exists!', 'error')
            return redirect(url_for('register'))

        new_user = users(name, password, email)
        db.session.add(new_user)
        db.session.commit()
        flash('You have been registered successfully!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/user', methods=["GET", "POST"])
def user():
    email = None
    if "user" in session:
        user = session['user']

        if request.method == 'POST':
            email = request.form['email']
            session['email'] = email
            found_user = users.query.filter_by(name=user).first()
            found_user.email = email
            db.session.commit()
            flash('Email was Saved!', 'success')
        else:
            if 'email' in session:
                email = session['email']
        return render_template('user.html', email=email)
    else:
        flash('You are not logged in!', 'error')
        return redirect(url_for('login'))


@app.route('/logout')
def logout():
    if 'user' in session:
        user = session['user']
        flash(f'You have been logged out, {user}', "info")
        session.pop('user', None)
        session.pop('email', None)
    else:
        flash('You were not logged in!', 'error')
    return redirect(url_for('login'))


@app.route('/delete')
def delete():
    for user in users.query.all():
        db.session.delete(user)
    db.session.commit()
    flash('Users Deleted!', 'info')
    return render_template("index.html")


@app.route('/reset_db')
def reset_db():
    db.drop_all()
    db.create_all()
    flash('Database has been reset!', 'info')
    return redirect(url_for('index'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
