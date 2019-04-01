from flask import Flask, g
from flask import render_template, flash, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import check_password_hash

import forms
import models

DEBUG = True
PORT = 8000

app = Flask(__name__)
app.secret_key = 'This is not the secret key'

login_manager = LoginManager()
## sets up our login for the app
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(userid):
    try:
        return models.User.get(models.User.id == userid)
    except models.DoesNotExist:
        return None

@app.before_request
def before_request():
    # Connect to the database before each request
    g.db = models.DATABASE
    g.db.connect()



@app.after_request
def after_request(response):
    # Close the database connection after each request
    g.db.close()
    return response

## =======================================================
## ROOT ROUTE
## =======================================================

@app.route('/')
def index():
    return render_template('landing.html')

## =======================================================
## REGISTER ROUTE
## =======================================================

@app.route('/register', methods=('GET', 'POST'))
def register():
    form = forms.RegisterForm()  # importing the RegisterFrom from forms.py
    if form.validate_on_submit(): # if the data in the form is valid,  then we are gonna create a user
        flash('Yay you registered', 'success')
        models.User.create_user( # calling the create_user function from the user model and passing in the form data
            username=form.username.data,
            firstname=form.firstname.data,
            lastname=form.lastname.data,
            email=form.email.data,
            password=form.password.data,
            )
        return redirect(url_for('index')) # once the submissin is succesful, user is redirected to the index function which routes back to the home page
    return render_template('register.html', form=form)


## =======================================================
## LOGIN ROUTE
## =======================================================

@app.route('/login', methods=('GET', 'POST'))
def login():
    form = forms.LoginForm()
    if form.validate_on_submit():
        try:
            user = models.User.get(models.User.email == form.email.data) # comparing the user email in the database to the one put in the form
        except models.DoesNotExist:
            flash("your email or password doesn't exist in our database")
        else:   # using the check_password_hash method bc we hashed the user's password when they registered. comparing the user's password in the database to the password put into the form
            if check_password_hash(user.password, form.password.data):
                ## creates session
                login_user(user) # this method comes from the flask_login package
                flash("You've been logged in", "success")
                return redirect('/profile')
            else:
                flash("your email or password doesn't match", "error")
    
    return render_template('login.html', form=form)


if __name__ == '__main__':
    models.initialize()
    try:
        models.User.create_user(
            username='EricCartman',
            firstname='jimbo',
            lastname='fisher',
            email="jim@jim.com",
            password='password'
            )
    except ValueError:
        pass

    app.run(debug=DEBUG, port=PORT)