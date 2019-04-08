from flask_wtf import FlaskForm as Form

from models import User


from wtforms import TextField, TextAreaField, SubmitField, StringField, PasswordField, IntegerField, HiddenField
from wtforms import SelectField

from wtforms.validators import (DataRequired, Regexp, ValidationError, Email, Length, EqualTo)

# Imports for file/photo uploader
from flask_wtf.file import FileField, FileRequired, FileAllowed


def name_exists(form, field):
    if User.select().where(User.username == field.data). exists():
        raise ValidationError("Username is not available!")

def email_exists(form, field):
    if User.select().where(User.email == field.data).exists():
        raise ValidationError("Email already exists!")
    


class RegisterForm(Form):
    username = StringField(
        'Username',
        validators=[
            DataRequired(),
            Regexp(
                r'^[a-zA-Z0-9_]+$',
                message=("Username should be one word, letters, numbers, and underscores only")
            ),
            name_exists
        ])
    email = StringField(
        'Email',
        validators = [
            DataRequired(),
            Email(),
            email_exists
        ])
    password = PasswordField(
        'Password',
        validators = [
            DataRequired(),
            Length(min=2),
            EqualTo('Password2', message='Passwords must match')
        ])
    Password2 = PasswordField(
        'Confirm Password',
        validators = [DataRequired()]
    )
    firstname = StringField(
        'First Name',
        validators = [
            DataRequired()
        ])
    
    lastname = StringField(
        'Last Name',
        validators = [
            DataRequired()
        ])
    submit = SubmitField(
        'Register'
    )
    



class LoginForm(Form):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login', validators=[DataRequired()])



class PetForm(Form):
    name = TextField("Pet Name", validators=[DataRequired()])
    status = SelectField('Lost or found', choices=[('Lost', 'Lost'), ('Found','Found')])
    description = TextAreaField("Tell me about your pet",validators=[DataRequired()])
    location = TextField('Where was your pet last scene', validators=[DataRequired()])
    lat = HiddenField('lat')
    long = HiddenField('long')
    pet_image = FileField('Pet Image',validators=[FileRequired(), FileAllowed(['jpg','png', 'gif'],'jpg & png images only') ] )
    breed = TextField('Pet Type', validators=[DataRequired()])
    distinct = TextField('Unique property for your pet', validators=[DataRequired()])
    submit = SubmitField('Add Pet', validators=[DataRequired()])
    


class EditPetForm(Form):
    name = TextField("Pet Name")
    status = SelectField('Lost or found', choices=[('Lost', 'Lost'), ('Found','Found')])
    description = TextAreaField("Tell me about your pet")
    location = TextField('Where was your pet last scene')
    lat = HiddenField('lat')
    long = HiddenField('long')
    image = TextField('pic of your lost pet')
    breed = TextField('Pet Type')
    distinct = TextField('Unique property for your pet')
    submit = SubmitField('Edit Pet')



class FoundPetForm(Form):
    distinct = TextField('What is the unique property of this pet?', validators=[DataRequired()])
    submit = SubmitField('Found Pet')
