import datetime
from datetime import date
from datetime import time
from datetime import datetime, timedelta
from peewee import *

from flask_login import UserMixin
from flask_bcrypt import generate_password_hash

DATABASE = SqliteDatabase('petfinder.db')

class User(UserMixin, Model):
    __table_args__ = {'extend_existing': True} 
    
    username = CharField()
    firstname = CharField()
    lastname = CharField()
    password = CharField(max_length=100)
    email = CharField(unique=True)
    joined_at = DateTimeField(default=date.today().strftime("%Y-%m-%d"))
    verfied = BooleanField(default=False)
    class Meta:
        database = DATABASE
        order_by = ('-timestamp',)
    
    #  function that creates a new user
    @classmethod
    def create_user(cls, username,firstname, lastname , password, email,):
        try:
            cls.create(
                username = username,
                firstname = firstname,
                lastname = lastname,
                email = email,
                password = generate_password_hash(password)
            )
        except IntegrityError:
            raise ValueError("User already exists")


class Pet(Model):
    __table_args__ = {'extend_existing': True} 
    
    name = CharField()
    status = CharField()
    location = CharField()
    lat = DoubleField()
    long = DoubleField()
    image = CharField()
    description = CharField(max_length=100)
    breed = CharField()
    distinct = CharField()
    user = ForeignKeyField(User, backref="pets")

    class Meta:
        database = DATABASE
        order_by = ('-timestamp',)
    
    # @classmethod
    # def create_pet(cls, name,status, location , image, description, breed,distinct,):
    #     try:
    #         cls.create(
    #             name = name,
    #             status = status,
    #             location = location,
    #             image = image,
    #             description = description,
    #             breed = breed,
    #             distinct = distinct
    #         )
    #     except IntegrityError:
    #         raise ValueError("Exact Pet already exists")






def initialize():
    DATABASE.connect()
    DATABASE.create_tables([User,Pet], safe=True)
    DATABASE.close()