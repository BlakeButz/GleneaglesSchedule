from flask import Flask, render_template, request, redirect, url_for, session, flash, current_app
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "hello"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.permanent_session_lifetime = timedelta(minutes=5)

db = SQLAlchemy(app)

class users(db.Model):
    _id = db.Column("id", db.Integer, primary_key=True)
    name = db.Column("name", db.String(100), nullable=False)
    email = db.Column("email", db.String(100), nullable=False)

    def __init__(self, name, email):
        self.name = name
        self.email = email



@app.route('/')
def index():
    return render_template('index.html')

@app.route("/view")
def view():
    return render_template("view.html", values=users.query.all())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session.permanent = True
        user = request.form['user']  # Ensure 'user' matches the form field name
        session['user'] = user

        found_user = users.query.filter_by(name=user).first()
        if found_user:
            session['email'] = found_user.email
        else:
            usr = users(user, "")
            db.session.add(usr)
            db.session.commit()

        flash('You were logged in successfully!', 'success')
        return redirect(url_for('user', user=user))
    else:
        if "user" in session:
            flash('Already logged in!', 'info')
            return redirect(url_for('user', user=session['user']))
        return render_template("login.html")


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
            flash('Email was Saved!')
        else:
            if 'email' in session:
                email = session['email']
        return render_template('user.html', email=email)
    else:
        flash('You are not logged in!')
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    if 'user' in session:
        user = session['user']
        flash(f'You have been logged out, {user}', "info")
        session.pop('user', None)
        session.pop('email', None)
    else:
        flash('You were not logged in!')
    return redirect(url_for('login'))

@app.route('/delete')
def delete():
    for user in users.query.all():
        db.session.delete(user)
    db.session.commit()
    flash('Users Deleted!')
    return render_template("index.html")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
