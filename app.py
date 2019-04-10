import os
import functools
from flask import Flask, g, jsonify, request
from flask import render_template, flash, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import check_password_hash
from flask_mail import Mail
from flask_mail import Message
# Image uploader imports
from flask_uploads import UploadSet, configure_uploads, IMAGES

# from secret import EMAIL_PASSWORD, SENDER_EMAIL, URL_SAFE_SECRET, APP_SECRET_KEY

from itsdangerous import URLSafeTimedSerializer, SignatureExpired

import forms
import models

DEBUG = True
PORT = 8000  

app = Flask(__name__,instance_relative_config=True)



# Sets upload destinations for image uploader
app.config.from_pyfile('flask.cfg')

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = SENDER_EMAIL 
app.config['MAIL_PASSWORD'] = EMAIL_PASSWORD
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)


app.secret_key = APP_SECRET_KEY


s = URLSafeTimedSerializer(URL_SAFE_SECRET)

# APP_ROOT = os.path.dirname(os.path.abspath(__file__))

login_manager = LoginManager()
## sets up our login for the app
login_manager.init_app(app)
login_manager.login_view = 'login'


# Sets variable images to uploader
images = UploadSet('images', IMAGES)
configure_uploads(app, images)



# def check_if_user_verified_email(f):
#     f = check_if_user_verified_email(f)
#     @functools.wrap(f)
#     def wrapped (*args, **kwargs):
#         if current_user.verfied == False:
#             flash(f'Please Verify your email to use Petfinder')
#             return redirect(url_for('index'))
#             result = f(*args, **kwargs)

#             return result
#     return wrapped 



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

def check_if_user_verified_email(user):
    if user.verfied == False:
        print(user.verfied)
        flash(f'Please Verify your email to use Petfinder')
        return redirect('/')




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
        # # Sets variable filename to image file of uploaded 'pet_image' from form
        filename = images.save(request.files['user_image'])
        # # Sets variable url to change image url to match filename
        url = images.url(filename)
        flash('Yay you registered', 'success')
        models.User.create_user( # calling the create_user function from the user model and passing in the form data
            username=form.username.data,
            firstname=form.firstname.data,
            lastname=form.lastname.data,
            email=form.email.data,
            password=form.password.data,
            image_filename = filename,
            image_url = url
            )
        email = form.email.data
        name = form.firstname.data
        
        # Verify email logic

        #creats token
        token = s.dumps(email,salt='email-confirm')

        #sends message to user that registered for an email
        msg = Message('Confirm Email', sender=SENDER_EMAIL, recipients=[email])

        # temp_user = models.User.select().where(models.User.email=email).get()

        #creates link to the confirm_email template
        link = url_for('confirm_email', token=token, _external=True)

        #sends message to user that registered for an email
        msg.body = f'Hello {name}! Thank you for signing up for petfinder. Please confirm your email using this link {link}'
        mail.send(msg)

        print(f'the email is {email} and the token is {token}')
        flash(f" Hello {name}!Please check your email inbox and verify your email. Your token will expire in 60 minutes", "registersuccess")
        return redirect(url_for('pets')) # once the submissin is succesful, user is redirected to the index function which routes back to the home page
    return render_template('register.html', form=form)

## =======================================================
## CONFIRMED EMAIL ROUTE
## =======================================================
@app.route('/confirm_email/<token>')
def confirm_email(token):
    try:
        email = s.loads(token, salt='email-confirm', max_age=3600)
    except SignatureExpired:
        return render_template('token_expired.html')
    else:
        temp_user = models.User.select().where(models.User.email== email).get()
        temp_user.verfied = True
        temp_user.save()
    return render_template('confirmed_email.html')




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
                flash("Login Successful", "loginsuccess")
                return redirect('/pets')
            else:
                flash("Your email or password doesn't match. Please try again", "loginerror")
    
    return render_template('login.html', form=form)


## =======================================================
## LOGOUT ROUTE
## =======================================================

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You've been logged out", "success")
    return redirect(url_for('index'))

## =======================================================
##  ALL PETS ROUTE
## =======================================================

@app.route('/pets', methods=('GET','POST'))
@login_required
def pets():
    print(current_user.verfied)
    check_if_user_verified_email(current_user)

    form = forms.PetForm()
    pets = models.Pet.select()
#   pets = models.Pet.select().where(models.Pet.user == current_user.id)
    user = models.User.get(current_user.id)
    if form.validate_on_submit():
        models.Pet.create(
        name=form.name.data.strip(),
        status=form.status.data.strip(), 
        user = current_user.id,
        location = form.location.data.strip(),
        image = form.image.data.strip(),
        description = form.description.data.strip(),
        breed = form.breed.data.strip(),
        distinct = form.distinct.data.strip()
        )
        return render_template('pets.html', pets = pets,form = form)
    return render_template('pets.html', pets = pets,form = form, user = user)


## =======================================================
##  LOST PETS ROUTE
## =======================================================
@app.route('/lost_pets', methods=('GET','POST'))
@login_required
def lostpets():
    pets = models.Pet.select().where(models.Pet.status =='Lost')
    return render_template('pets.html', pets = pets)

## =======================================================
##  WAITING PETS ROUTE
## =======================================================
@app.route('/waiting_pets', methods=('GET','POST'))
@login_required
def waiting_pets():
    pets = models.Pet.select().where(models.Pet.status =='waiting')
    return render_template('pets.html', pets = pets)


## =======================================================
## ADD PET ROUTE
## =======================================================

@app.route("/addpet", methods=['GET', 'POST'])
@login_required
def add_pet():
    form = forms.PetForm()
    pets = models.Pet.select().where(models.Pet.user == current_user.id)
    if form.validate_on_submit():
        # # Sets variable filename to image file of uploaded 'pet_image' from form
        filename = images.save(request.files['pet_image'])
        # # Sets variable url to change image url to match filename
        url = images.url(filename)

        models.Pet.create(
        name=form.name.data.strip(),
        status=form.status.data.strip(), 
        user = current_user.id,
        location = form.location.data.strip(),
        description = form.description.data.strip(),
        breed = form.breed.data.strip(),
        distinct = form.distinct.data.strip(),
        lat = form.lat.data.strip(),
        long = form.long.data.strip(),
        image_filename = filename,
        image_url = url
        )
        # return render_template("pets.html", pets = pets,form = form)
        flash("Pet Successfuly added to our database", "petsuccess")
        return redirect(url_for('pets'))
    return render_template('add_pets.html', pets = pets,form = form)


## =======================================================
## SHOW PET ROUTE
## =======================================================
@app.route("/showpet/<petid>", methods=["GET", "POST"])
@login_required
def show_pet(petid):
    # grabbing a specific pet by id
    pet = models.Pet.get(models.Pet.id == petid)
    # grabbing the user who created that pet 
    user = models.User.get(models.User.id == pet.user_id)

    allcomments = models.Comment.select()
    print(allcomments)

    subComments = models.SubComment.select()

    print(subComments)

    # grabbing all comments associated with a specific pet
    comments = models.Comment.select().where(models.Comment.pet_id == petid)
    
    print(f' this is the id of the {user}')
    user2 = models.User.select()
    
    print(pet)
    return render_template("show_pet.html", pet=pet, user = user, comments = comments, subComments =subComments)


## =======================================================
## EDIT PET ROUTE
## =======================================================
@app.route("/editpet/<petid>", methods=["GET", "POST"])
@login_required
def edit_pet(petid):
    pet = models.Pet.get(models.Pet.id == petid)
    user = models.User.get(models.User.id == pet.user_id)
    print(pet)
    form = forms.EditPetForm()
    if form.validate_on_submit():
        pet.name = form.name.data
        pet.status = form.status.data
        pet.location = form.location.data
        pet.description = form.description.data
        pet.breed = form.breed.data
        pet.distinct = form.distinct.data
        lat = form.lat.data.strip()
        long = form.long.data.strip()
        pet.save()
        pets = models.Pet.select().where(models.Pet.user == current_user.id)
        unique_pet = form.name.data
        flash(f'{unique_pet}s infomation was successfuly updated', "editpet")
        return redirect(f'/showpet/{pet}')
        # return render_template("show_pet.html",form=form, pet=pet, user = user)
    
    form.name.data = pet.name
    form.status.data = pet.status
    form.location.data = pet.location
    form.description.data = pet.description
    form.breed.data = pet.breed
    form.distinct.data = pet.distinct
    return render_template("edit_pet.html", form=form, pet=pet)

## =======================================================
## DELETE PET ROUTE
## =======================================================
@app.route("/deletepet/<petid>")
@login_required
def delete_pet(petid):
    pet = models.Pet.get(models.Pet.id == petid)
    user= current_user.id
    print(user)
    print(pet.user_id)
    #checking db to see if the current user actually created the pet by id, if so then user can delete the pet
    if user == pet.user_id:
        unique_pet = pet.name
        pet.delete_instance()
        flash(f'{unique_pet} was deleted', "deletepet")
        return redirect(url_for('pets'))

    else:
        flash(f' Sorry{current_user.username}, you do not have permission to delete {pet.name} from our Database,"deletepet')
        return redirect(url_for('pets'))


## =======================================================
## FOUND PET ROUTE
## =======================================================
@app.route("/foundpet/<petid>", methods=["GET", "POST"])
@login_required
def found_pet(petid):
    pet = models.Pet.get(models.Pet.id == petid)
    user = models.User.get(models.User.id == pet.user_id)

    #grabbing the pet owner's name 
    pet_owner_email = user.email
    pet_owner_name = user.firstname

    # current logged in user
    user2 = models.User.get(models.User.id == current_user.id)
    pet_finder_name = user2.firstname + user2.lastname

    print(pet_owner_email)  

    form =forms.FoundPetForm()
    if form.validate_on_submit():
        distinct_guess = form.distinct.data
        print(distinct_guess)
        print(pet.distinct)
        #changes status to waiting if the current user knows the distinct feature of the pet and sends the original pet owner an email
        if distinct_guess == pet.distinct:
            pet.status = "Waiting"
            print(pet.status)
            flash("Looks like you found this pet. We will notify the owner that there is a potential match!", 'success')

            msg = Message("Hello, your pet may have been found!",sender=SENDER_EMAIL,recipients=[pet_owner_email])
            msg.body = f'Hi {pet_owner_name}, {pet_finder_name} has mentioned that they have found your pet. Please reach out and schedule a meetup for your pet!'
            mail.send(msg)

            #updating the status of the pet
            pet.save()
        elif distinct_guess != pet.distinct: 
            flash(" Your guess does not match our database", 'error')
        # return redirect(url_for('pets'))
        return render_template("found_pet.html", form=form, pet=pet) 
    return render_template("found_pet.html", form=form, pet=pet)       

## =======================================================
## ADD COMMENT ROUTE
## =======================================================
@app.route("/add_comment/<petid>", methods=["GET", "POST"])
@login_required
def add_comment(petid):
    form = forms.CommentForm()
    specific_pet_id = petid
    if form.validate_on_submit():
        models.Comment.create(
        user = current_user.id,
        pet = specific_pet_id,
        text=form.text.data.strip()
        )   
        flash('Comment Created!', "editpet")
        return redirect(f'/showpet/{specific_pet_id}')

    return render_template("add_comment.html", form=form)

## =======================================================
## DELETE COMMENT ROUTE
## =======================================================
@app.route("/delete_comment/<commentid>/<petid>", methods=["GET", "POST"])
@login_required
def delete_comment(commentid, petid):
    specific_pet_id = petid
    comment = models.Comment.get(models.Comment.id == commentid)
    user = current_user.id
    print(f'this is the comment object {comment}')

    #checking to see if the current user equals the id of the user who created the comment
    if user == comment.user_id:
        flash(' Your Comment was deleted!', "editpet")
        comment.delete_instance()
    return redirect(f'/showpet/{specific_pet_id}')
    
## =======================================================
## EDIT COMMENT ROUTE
## =======================================================
@app.route("/edit_comment/<commentid>/<petid>", methods=["GET", "POST"])
@login_required
def edit_comment(commentid, petid):
    form = forms.CommentForm()
    specific_pet_id = petid
    comment = models.Comment.get(models.Comment.id == commentid)
    user = current_user.id
    #checking to see if the user actually made the comment , if not , then redirect back to the show page
    if user != comment.user_id:
        return redirect(f'/showpet/{specific_pet_id}')

    if form.validate_on_submit():
        if user == comment.user_id: # if the user id matches the user id in the comment table , then the user can edit the comment
            comment.text = form.text.data
            comment.save()
            return redirect(f'/showpet/{specific_pet_id}')
            

    form.text.data = comment.text
    return render_template("add_comment.html", form=form)

## =======================================================
## SUB COMMENT ROUTE
## =======================================================
@app.route("/sub_comment/<commentid>/<petid>", methods=["GET", "POST"])
@login_required
def add_sub_comment(petid, commentid):
    form = forms.CommentForm()
    specific_pet_id = petid
    comment_id = models.Comment.get(models.Comment.id == commentid)
    if form.validate_on_submit():
        models.SubComment.create(
        user = current_user.id,
        comment = comment_id,
        text=form.text.data.strip(),
        pet = specific_pet_id
        ) 
        flash('Comment Created!', "editpet")
        return redirect(f'/showpet/{specific_pet_id}')
    
    return render_template("add_comment.html", form=form)


## =======================================================
## DELETE SUBCOMMENT ROUTE
## =======================================================
@app.route("/delete_subcomment/<subcommentid>/<petid>", methods=["GET", "POST"])
@login_required
def delete_subcomment(subcommentid, petid):
    specific_pet_id = petid
    subcomment = models.SubComment.get(models.SubComment.id == subcommentid)
    user = current_user.id
    print(f'this is the comment object {subcomment}')

    #checking to see if the current user equals the id of the user who created the subcomment
    if user == subcomment.user_id:
        flash(' Your Comment was deleted!', "editpet")
        subcomment.delete_instance()
    return redirect(f'/showpet/{specific_pet_id}')


## =======================================================
## EDIT SUBCOMMENT ROUTE
## =======================================================
@app.route("/edit_subcomment/<subcommentid>/<petid>", methods=["GET", "POST"])
@login_required
def edit_subcomment(subcommentid, petid):
    form = forms.CommentForm()
    specific_pet_id = petid
    subcomment = models.SubComment.get(models.SubComment.id == subcommentid)
    user = current_user.id
    #checking to see if the user actually made the comment , if not , then redirect back to the show page
    if user != subcomment.user_id:
        return redirect(f'/showpet/{specific_pet_id}')

    if form.validate_on_submit():
        if user == subcomment.user_id: # if the user id matches the user id in the comment table , then the user can edit the comment
            subcomment.text = form.text.data
            subcomment.save()
            return redirect(f'/showpet/{specific_pet_id}')
            

    form.text.data = subcomment.text
    return render_template("add_comment.html", form=form)


if 'ON_HEROKU' in os.environ:
    print('hitting ')
    models.initialize()


if __name__ == '__main__':
    models.initialize()
    try:
        models.User.create_user(
            username='EricCartman',
            firstname='jimbo',
            lastname='fisher',
            email="jim@jim.com",
            password='password',
            image_filename = " ",
            image_url = "./static/images/default-user-image.png"
            )
    except ValueError:
        pass

    app.run(debug=DEBUG, port=PORT)