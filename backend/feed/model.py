from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from dotenv import load_dotenv
import os, json
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.ext.mutable import Mutable

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DRIVER') + os.getenv('DB_USERNAME') + ':' + os.getenv('DB_PASSWORD') + '@' + os.getenv('DB_URL') + ':' + os.getenv('DB_PORT') + '/' + os.getenv('DB_NAME')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class MutableList(Mutable, list):
    def append(self, value):
        list.append(self, value)
        self.changed()

    @classmethod
    def coerce(cls, key, value):
        if not isinstance(value, MutableList):
            if isinstance(value, list):
                return MutableList(value)
            return Mutable.coerce(key, value)
        else:
            return value

class UsersModel(db.Model):
    __tablename__ = "users"

    username = db.Column(db.String())
    password = db.Column(db.String())
    name = db.Column(db.String())
    display_pic = db.Column(db.String())
    email = db.Column(db.String())
    bio = db.Column(db.String())
    is_celebrity = db.Column(db.Boolean())
    user_id = db.Column(db.Integer(), primary_key=True)
    following = db.Column(MutableList.as_mutable(db.ARRAY(db.Integer)))
    followers = db.Column(MutableList.as_mutable(db.ARRAY(db.Integer)))
    celebrity_list = db.Column(MutableList.as_mutable(db.ARRAY(db.Integer)))

    def __init__(self, username, name, password, display_pic, email, bio, is_celebrity, following, followers, celebrity_list):
        self.username = username
        self.name = name
        self.display_pic = display_pic
        self.email = email
        self.bio = bio
        self.is_celebrity = is_celebrity
        self.password = password
        self.following = following
        self.followers = followers
        self.celebrity_list = celebrity_list

    def __repr__(self):
        return f"<Users {self.name}>"

class AlchemyEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj.__class__, DeclarativeMeta):
            # an SQLAlchemy class
            fields = {}
            for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
                data = obj.__getattribute__(field)
                try:
                    json.dumps(data) # this will fail on non-encodable values, like other classes
                    fields[field] = data
                except TypeError:
                    fields[field] = None
            # a json-encodable dict
            return fields

        return json.JSONEncoder.default(self, obj)