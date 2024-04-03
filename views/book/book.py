from flask import request
from flask import Blueprint
import logging
from sqlalchemy import desc

from db.model import db
from db.model import Book
from db.model import BookEdge
from db.model import EdgeName
from db.model import BookRating
from db.model import BookCollection
from widget.recommender.recomender import PersonalRecommender
from widget.jwt_auth import check_token
from widget.datetime import get_time_str
from widget.response_type import ErrorResponse
from widget.response_type import SuccessResponse
from widget.response_type import NotLoginResponse
from widget.response_type import NotFoundResponse
from widget.response_type import FormatErrorResponse
from widget.response_type import DatabaseErrorResponse


book_bp = Blueprint("book", __name__, url_prefix="/book")


@book_bp.post("/book_info/")
def book_info():
    token = request.headers.get('Authorization')
    res = check_token(token)
    if res == None:
        return NotLoginResponse().json()

    uuid = res["uuid"]

    try:
        data = request.get_json()
    except Exception as e:
        return FormatErrorResponse().json()

    if "book_id" not in data or data["book_id"] == None:
        return FormatErrorResponse().json()

    if not isinstance(data["book_id"], int) or \
       int(data["book_id"]) < 0:
        return FormatErrorResponse(
                message="book_id must be positive integer",
            ).json()

    book = Book.query.filter_by(id=int(data["book_id"])).first()
    if book == None:
        return NotFoundResponse().json()

    return SuccessResponse(book_info={
        "book_id"           : book.id,
        "book_name"         : book.name,
        "author"            : book.author,
        "publishing_house"  : book.publishing_house,
        "publishing_date"   : get_time_str(book.publishing_date),
    }).json()


@book_bp.post("/books_info/")
def books_info():
    token = request.headers.get('Authorization')
    res = check_token(token)
    if res == None:
        return NotLoginResponse().json()

    uuid = res["uuid"]

    try:
        data = request.get_json()
    except Exception as e:
        return FormatErrorResponse().json()

    if "start" not in data or data["start"] == None:
        return FormatErrorResponse().json()
    if "end" not in data or data["end"] == None:
        return FormatErrorResponse().json()

    if  not isinstance(data["start"], int) or \
        not isinstance(data["end"], int) or \
        int(data["start"]) < 0 or \
        int(data["end"]) < 0:
        return FormatErrorResponse(
                message="book_id must be positive integer",
            ).json()

    books = Book.query.filter(
            Book.id >= data["start"],
            Book.id < data["end"],
        ).all()

    ret_data = [{
        "book_id"           : book.id,
        "book_name"         : book.name,
        "author"            : book.author,
        "publishing_house"  : book.publishing_house,
        "publishing_date"   : get_time_str(book.publishing_date),
    } for book in books]

    return SuccessResponse(books_info=ret_data).json()


# 添加/修改评分
@book_bp.post("/update_rating/")
def update_rating():
    token = request.headers.get('Authorization')
    res = check_token(token)
    if res == None:
        return NotLoginResponse().json()

    uuid = res["uuid"]

    try:
        data = request.get_json()
    except Exception as e:
        return FormatErrorResponse().json()

    if "book_id" not in data or data["book_id"] == None:
        return FormatErrorResponse().json()
    if "rating" not in data or data["rating"] == None:
        return FormatErrorResponse().json()

    # book_id = data["book_id"]
    # rating    = data["rating"]

    book_rating = BookRating.query.filter_by(
            uuid    = uuid,
            book_id = data["book_id"],
        ).first()
    if book_rating == None:
        book_rating = BookRating(
            uuid        = uuid,
            book_id     = data["book_id"],
            rating      = data["rating"],
        )
        db.session.add(book_rating)
    book_rating.rating = data["rating"]

    # 遍历用户评分过的书, 然后 添加/更新 BookEdge
    book_ratings = BookRating.query.filter_by(uuid=uuid).all()
    for item in book_ratings:
        bid_a = data["book_id"]
        bid_b = item.book_id
        if bid_a == bid_b:
            continue
        elif bid_a > bid_b:
            bid_a, bid_b = bid_a, bid_a

        book_edge = BookEdge.filter_by(
                book_id_a = bid_a,
                book_id_b = bid_b,
            ).first()
        if book_edge == None:
            book_edge = BookEdge(
                book_id_a = bid_a,
                book_id_b = bid_b,
                weight = book_rating.rating,
                cnt = 0,
                average_weight = 0.0,
            )
        edge_name_exsits = EdgeName.filter_by(
                book_id_a   = bid_a,
                book_id_b   = bid_b,
                uuid        = uuid,
            ).first()
        if edge_name_exsits == None:
            db.session.add(EdgeName(
                    book_id_a = bid_a,
                    book_id_b = bid_b,
                    uuid      = uuid,
                ))
            book_edge.cnt += 1

        book_edge.weight += item.rating
        book_edge.average_weight = book_edge.weight / book_edge.cnt

        db.session.add(book_edge)

    try:
        db.session.commit()
    except Exception as e:
        logging.error(str(e))
        db.session.rollback()
        return DatabaseErrorResponse().json()

    return SuccessResponse().json()


# 查看所有评分
@book_bp.post("/get_all_ratings/")
def get_all_ratings():
    token = request.headers.get('Authorization')
    res = check_token(token)
    if res == None:
        return NotLoginResponse().json()

    uuid = res["uuid"]

    ratings = BookRating.query.filter_by(uuid=uuid).all()

    ret_data = []
    for item in ratings:
        res = Book.query.filter_by(id=item.book_id).first()
        ret_data.append({
            "book_id"   : res.book_id,
            "book_name" : res.book_name,
            "author"    : res.author,
            "rating"    : item.rating,
        })

    return SuccessResponse(all_ratings=ret_data).json()


# 删除评分
@book_bp.post("/delete_rating/")
def delete_rating():
    token = request.headers.get('Authorization')
    res = check_token(token)
    if res == None:
        return NotLoginResponse().json()

    uuid = res["uuid"]

    try:
        data = request.get_json()
    except Exception as e:
        return FormatErrorResponse().json()

    if "book_id" not in data or data["book_id"] == None:
        return FormatErrorResponse().json()

    book_rating = BookRating.query.filter_by(
            uuid    = uuid,
            book_id = data["book_id"],
        ).first()
    if book_rating == None:
        return NotFoundResponse(message="book not found").json()

    # BookEdge中删除weight, edge_cnt, 更新average_weight, 从EdgeName中删除
    ratings = BookRating.query.filter_by(uuid=uuid).all()
    for item in ratings:
        bid_a = data["book_id"]
        bid_b = item.book_id
        if bid_a == bid_b:
            continue
        elif bid_a > bid_b:
            bid_a, bid_b = bid_a, bid_a

        book_edge = BookEdge.filter_by(
                book_id_a = bid_a,
                book_id_b = bid_b,
            ).first()
        book_edge.weight -= book_rating.rating + item.rating

        edge_name = EdgeName.filter_by(
                book_id_a   = bid_a,
                book_id_b   = bid_b,
                uuid        = uuid,
            ).first()
        db.session.delete(edge_name)
        book_edge.cnt -= 1
        book_edge.average_weight = book_edge.weight / book_edge.cnt

    db.session.delete(book_rating)

    try:
        db.session.commit()
    except Exception as e:
        logging.error(str(e))
        db.session.rollback()
        return DatabaseErrorResponse().json()

    return SuccessResponse().json()


# 图书收藏
@book_bp.post("/collect/")
def collect():
    token = request.headers.get('Authorization')
    res = check_token(token)
    if res == None:
        return NotLoginResponse().json()

    uuid = res["uuid"]

    try:
        data = request.get_json()
    except Exception as e:
        return FormatErrorResponse().json()

    if "book_id" not in data or data["book_id"] == None:
        return FormatErrorResponse().json()

    res = BookCollection.query.filter_by(
            uuid    = uuid,
            book_id = data["book_id"],
        ).first()
    if res != None:
        return ErrorResponse(message="book already colleted").json()

    res = BookCollection(
        uuid    = uuid,
        book_id = data["book_id"],
    )
    db.session.add(res)

    try:
        db.session.commit()
    except Exception as e:
        logging.error(str(e))
        db.session.rollback()
        return DatabaseErrorResponse().json()

    return SuccessResponse().json()


# 获取所有收藏
@book_bp.post("/get_all_collections/")
def get_all_collections():
    token = request.headers.get('Authorization')
    res = check_token(token)
    if res == None:
        return NotLoginResponse().json()

    uuid = res["uuid"]

    collecitons = BookCollection.query.filter_by(uuid = uuid).all()

    ret_data = []
    for item in collecitons:
        res = Book.query.filter_by(id=item.book_id).first()
        ret_data.append({
            "book_id"   : res.book_id,
            "book_name" : res.book_name,
            "author"    : res.author,
        })

    return SuccessResponse(all_collections=ret_data).json()


# 热点推荐
@book_bp.post("/hot_recommendations/")
def hot_recommendations():
    token = request.headers.get('Authorization')
    res = check_token(token)
    if res == None:
        return NotLoginResponse().json()

    try:
        data = request.get_json()
    except Exception as e:
        return FormatErrorResponse().json()

    if "top_x" not in data or data["top_x"] == None:
        return FormatErrorResponse().json()

    top_books = BookEdge.query.order_by(
            desc(BookEdge.average_weight)
        ).limit(data["top_x"] * 2).all()

    book_ids = []
    for item in top_books:
        if item.book_id_a not in book_ids:
            book_ids.append(item.book_id_a)
        if len(book_ids) >= data["top_x"]:
            break

        if item.book_id_b not in book_ids:
            book_ids.append(item.book_id_b)
        if len(book_ids) >= data["top_x"]:
            break

    ret_data = []
    for book_id in book_ids:
        res = Book.query.filter_by(id=book_id).first()
        ret_data.append({
            "book_id"   : res.book_id,
            "book_name" : res.book_name,
            "author"    : res.author,
        })

    return SuccessResponse(all_collections=ret_data).json()


# 个人推荐
@book_bp.post("/personal_recommendations/")
def personal_recommendations():
    token = request.headers.get('Authorization')
    res = check_token(token)
    if res == None:
        return NotLoginResponse().json()

    uuid = res["uuid"]

    try:
        data = request.get_json()
    except Exception as e:
        return FormatErrorResponse().json()

    if "top_x" not in data or data["top_x"] == None:
        return FormatErrorResponse().json()

    book_ids = []

    ratings = BookRating.filter_by(uuid=uuid).order_by(
            desc(BookRating.rating)
        ).all()
    book_ids += [item.book_id for item in ratings]

    collections = BookCollection.filter_by(uuid=uuid).all()
    book_ids += [item.book_id for item in collections
                 if item.book_id not in book_ids]

    recomender = PersonalRecommender(book_ids)

    res_ids = recomender.get_recommended_books(int(data["top_x"]))

    ret_data = []
    for book_id in res_ids:
        res = Book.query.filter_by(id=book_id).first()
        ret_data.append({
            "book_id"   : res.book_id,
            "book_name" : res.book_name,
            "author"    : res.author,
        })

    return SuccessResponse(all_collections=ret_data).json()
