from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from dotenv import load_dotenv
import os, json
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.ext.mutable import Mutable

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DRIVER') + os.getenv('DB_USERNAME') + ':' +  os.getenv('DB_PASSWORD') + '@' + os.getenv('DB_URL') + ':' + os.getenv('DB_PORT') + '/' + os.getenv('DB_NAME')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

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

class PostModel(db.Model):
    __tablename__ = "posts"

    user_id = db.Column(db.Integer())
    post_id = db.Column(db.Integer(), primary_key=True)
    post_url = db.Column(db.String())
    date = db.Column(db.Integer())
    caption = db.Column(db.String())

    def __init__(self, user_id, post_url, date, caption):
        self.user_id = user_id
        self.post_url = post_url
        self.date = date
        self.caption = caption

    def __repr__(self):
        return f"<Post {self.user_id}>"