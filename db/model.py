from flask_sqlalchemy import SQLAlchemy
from widget.datetime import now_time

db = SQLAlchemy()


class User(db.Model):
    __tablename__       = 'users'
    id                  = db.Column(db.Integer, primary_key=True)
    uuid                = db.Column(db.String(80), unique=True, nullable=False)

    username            = db.Column(db.String(80), unique=True, nullable=False)
    password            = db.Column(db.String(80), nullable=False)
    email               = db.Column(db.String(50))
    registration_time   = db.Column(db.DateTime, default=now_time)


class UserSecretKey(db.Model):
    __tablename__   = "user_secret_key"
    id              = db.Column(db.Integer, primary_key=True)
    username        = db.Column(db.String(80), unique=True, nullable=False)
    secret_key      = db.Column(db.String(256), default="")


class Book(db.Model):
    __tablename__       = 'books'
    id                  = db.Column(db.Integer, primary_key=True)
    book_name           = db.Column(db.String(80), unique=True, nullable=False)
    author              = db.Column(db.String(80), default="")
    publishing_house    = db.Column(db.String(80), default="")
    publishing_date     = db.Column(db.String(80), default="")


class BookCollection(db.Model):
    __tablename__       = 'book_collections'
    id                  = db.Column(db.Integer, primary_key=True)
    uuid                = db.Column(db.String(80), unique=True, nullable=False)
    book_id             = db.Column(db.String(80), unique=True, nullable=False)


class BookRating(db.Model):
    __tablename__       = 'book_ratings'
    id                  = db.Column(db.Integer, primary_key=True)
    uuid                = db.Column(db.String(80), unique=True, nullable=False)
    book_id             = db.Column(db.String(80), unique=True, nullable=False)
    rating              = db.Column(db.Float, default=0.0)


class BookEdge(db.Model):
    """
    用户评分图
    """
    __tablename__       = 'book_edges'
    id                  = db.Column(db.Integer, primary_key=True)
    book_id_a           = db.Column(db.Integer, nullable=False)
    book_id_b           = db.Column(db.Integer, nullable=False)
    weight              = db.Column(db.Float, default=0.0)
    edge_cnt            = db.Column(db.Integer, default=0)
    average_weight      = db.Column(db.Float, default=0.0)

    # @property
    # def average_weight(self) -> float:
    #     if self.edge_cnt == 0:
    #         return 0.0
    #     return self.weight / self.edge_cnt


class EdgeName(db.Model):
    __tablename__       = 'edge_names'
    id                  = db.Column(db.Integer, primary_key=True)
    book_id_a           = db.Column(db.Integer, nullable=False)
    book_id_b           = db.Column(db.Integer, nullable=False)
    uuid                = db.Column(db.String(80), nullable=False)
