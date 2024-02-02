from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__       = 'users'
    id                  = db.Column(db.Integer, primary_key=True)
    uuid                = db.Column(db.String(80), unique=True, nullable=False)
    username            = db.Column(db.String(80), unique=True, nullable=False)
    password            = db.Column(db.String(80), nullable=False)
    email               = db.Column(db.String(50))
    registration_time   = db.Column(db.DateTime, default="1970-01-01 00:00:00")


class UserSecretKey(db.Model):
    __tablename__   = "user_secret_key"
    id              = db.Column(db.Integer, primary_key=True)
    uuid            = db.Column(db.String(80), unique=True, nullable=False)
    secret_key      = db.Column(db.String(256), default="")
