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
    uuid            = db.Column(db.String(80), unique=True, nullable=False)
    secret_key      = db.Column(db.String(256), default="")


class Book(db.Model):
    """
    书籍表
    """
    __tablename__       = 'books'
    id                  = db.Column(db.Integer, primary_key=True)
    book_name           = db.Column(db.String(80), nullable=False)
    author              = db.Column(db.String(80), default="")
    publishing_house    = db.Column(db.String(80), default="")
    publishing_date     = db.Column(db.String(80), default="")


class BookCollection(db.Model):
    """
    书籍收藏表, 存用户收藏的图书
    """
    __tablename__       = 'book_collections'
    id                  = db.Column(db.Integer, primary_key=True)
    uuid                = db.Column(db.String(80), nullable=False)
    book_id             = db.Column(db.String(80), nullable=False)


class BookRating(db.Model):
    """
    书籍评分表, 存用户对书籍的评分
    """
    __tablename__       = 'book_ratings'
    id                  = db.Column(db.Integer, primary_key=True)
    uuid                = db.Column(db.String(80), nullable=False)
    book_id             = db.Column(db.String(80), nullable=False)
    rating              = db.Column(db.Float, default=0.0)


class BookEdge(db.Model):
    """
    所有用户评分图, 每条数据是一条边, 连接同一个用户关联另一本书
    - 单向边, book_id_a <= book_id_b
    - weight: 边权, 值为每个用户对两本书的评分和
    - average_weight: 平均边权, 值为 weight / edge_cnt
    """
    __tablename__       = 'book_edges'
    id                  = db.Column(db.Integer, primary_key=True)
    book_id_a           = db.Column(db.Integer, nullable=False)
    book_id_b           = db.Column(db.Integer, nullable=False)
    weight              = db.Column(db.Float, default=0.0)

    edge_cnt            = db.Column(db.Integer, default=0)
    average_weight      = db.Column(db.Float, default=0.0)


class EdgeName(db.Model):
    """
    用户个人评分图, 无权重, 用来记录两本书的边数
    - 单向边, book_id_a <= book_id_b
    """
    __tablename__       = 'edge_names'
    id                  = db.Column(db.Integer, primary_key=True)
    uuid                = db.Column(db.String(80), nullable=False)
    book_id_a           = db.Column(db.Integer, nullable=False)
    book_id_b           = db.Column(db.Integer, nullable=False)


class BookComment(db.Model):
    """
    用户对书籍的评论
    """
    __tablename__       = 'book_comment'
    id                  = db.Column(db.Integer, primary_key=True)
    uuid                = db.Column(db.String(80), nullable=False)
    book_id             = db.Column(db.Integer, nullable=False)
    comment             = db.Column(db.Text, nullable=False)
