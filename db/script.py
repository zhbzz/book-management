import os
import uuid
import random
import string
from tqdm import tqdm

from config import HOME_DIR
from db.model import db
from db.model import User
from db.model import Book
from db.model import BookRating
from db.model import EdgeName
from db.model import BookEdge


BOOK_INFO_PATH = os.path.join(HOME_DIR, "data/ID_NAME_AUTHOR.CSV")
RATING_PATH = os.path.join(HOME_DIR, "data/RANK.CSV")


USER_UUID   = {}
# USER_BOOK   = {}
# BOOK_EDGE   = {}


def generate_user(_id):
    """
    如果id==_id的用户存在, 返回用户uuid,
    如果不存在, 生成id==_id的用户并返回uuid
    """
    # print(f"generate user: user_id {_id}.")

    if _id in USER_UUID:
        return USER_UUID[_id]

    res = User.query.filter_by(id=_id).first()
    if res != None:
        USER_UUID[_id] = res.uuid
        return USER_UUID[_id]

    def check_exist(uuid):
        exist = User.query.filter_by(uuid=uuid).first()
        if exist != None:
            return True
        return False

    user_uuid = uuid.uuid4()
    while check_exist(user_uuid):
        user_uuid = uuid.uuid4()
    res = User(
            id          = _id,
            uuid        = user_uuid,
            username    = "".join(random.choice(string.ascii_letters) for _ in range(6)),
            password    = "123456",
        )
    db.session.add(res)

    USER_UUID[_id] = res.uuid

    return USER_UUID[_id]


def add_rating(user_uuid, book_id, rating) -> bool:
    # print(f"add rating: user_uuid {user_uuid} bookid {book_id}.")
    res = BookRating.query.filter_by(
            uuid    = user_uuid,
            book_id = book_id,
        ).first()

    if res == None:
        res = BookRating(
            uuid    = user_uuid,
            book_id = book_id,
            rating  = rating,
        )
        db.session.add(res)
    else:
        res.rating = rating

    try:
        db.session.commit()
    except Exception as e:
        print("ERROR:", e)
        return False

    return True


def add_book_edge(user_uuid, book_id: int, rating):
    # print(f"add book_edge: user_uuid {user_uuid} bookid {book_id}.")

    ress = BookRating.query.filter_by(uuid=user_uuid).all()
    # ress = USER_BOOK[user_uuid]

    # print("add book_edge")
    # for res in tqdm(ress): # for every other book of this user
    for res in ress: # for every other book of this user
        other_book_id = int(res.book_id)
        if other_book_id == book_id:
            continue
        elif int(book_id) > int(other_book_id):
            book_id, other_book_id = other_book_id, book_id
        new_edge = EdgeName(
            uuid = user_uuid,
            book_id_a = book_id,
            book_id_b = other_book_id,
        )
        db.session.add(new_edge)

        # update BookEdge
        res = BookEdge.query.filter_by(
                book_id_a = book_id,
                book_id_b = other_book_id,
            ).first()
        if res == None:
            res = BookEdge(
                book_id_a = book_id,
                book_id_b = other_book_id,
                weight = rating,
                edge_cnt = 1,
                average_weight = rating,
            )
            db.session.add(res)
        else:
            res.weight += rating
            res.edge_cnt += 1
            res.average_weight = res.weight / res.edge_cnt

        try:
            db.session.commit()
        except Exception as e:
            print("ERROR:", e)
            return False

        # key = f"{book_id}_{other_book_id}"
        # if key not in BOOK_EDGE:
        #     BOOK_EDGE[f"{book_id}_{other_book_id}"] = {
        #         # "uuid"              : user_uuid,
        #         "weight"            : rating,
        #         "edge_cnt"          : 1,
        #         "average_weight"    : rating,
        #     }
        # else:
        #     tmp = BOOK_EDGE[f"{book_id}_{other_book_id}"]
        #     tmp["weight"] += rating
        #     tmp["edge_cnt"] += 1
        #     tmp["average_weight"] = tmp["weight"] / tmp["edge_cnt"]
        #     BOOK_EDGE[f"{book_id}_{other_book_id}"] = tmp
    # for every other book end

    return True



def add_books():
    # 添加书籍信息
    print("add books...")
    with open(BOOK_INFO_PATH) as f:
        _ = f.readline()
        books = f.readlines()
    for book in tqdm(books):
        info = book.strip().split(",")
        id = info[0]
        name = info[1]
        author = info[2]
        db.session.add(Book(
                id          = int(id),
                book_name   = name,
                author      = author,
            ))

    try:
        db.session.commit()
    except Exception as e:
        print("ERROR:", e)
        return


def pre_add():
    """
    需要在app.app_context()中调用
    预添加数据到数据库, 建议只在迁移时使用一次
    """
    # all_books = Book.query.all()
    # all_users = User.query.all()
    # all_edges = BookEdge.query.all()
    # [db.session.delete(item) for item in all_books]
    # [db.session.delete(item) for item in all_users]
    # [db.session.delete(item) for item in all_edges]

    try:
        db.session.commit()
    except Exception as e:
        print("ERROR:", e)
        return

    # 添加书籍信息
    print("add books...")
    with open(BOOK_INFO_PATH) as f:
        _ = f.readline()
        books = f.readlines()
    for book in tqdm(books):
        info = book.strip().split(",")
        id = info[0]
        name = info[1]
        author = info[2]
        res = Book.query.filter_by(
                    book_name   = name,
                    author      = author,
                ).first()
        if res == None:
            db.session.add(Book(
                    id          = int(id),
                    book_name   = name,
                    author      = author,
                ))

    try:
        db.session.commit()
    except Exception as e:
        print("ERROR:", e)
        return

    # 书籍评分信息
    print("add ratings...")
    with open(RATING_PATH) as f:
        _ = f.readline()
        ratings = f.readlines()

    for item in tqdm(ratings):
        info = item.strip().split(",")
        # _id         =  int(info[0])
        _user_id    =  int(info[1])
        _book_id    =  int(info[2])
        _rating     =  int(info[3])
        user_uuid = generate_user(_user_id)
        add_rating(user_uuid, int(_book_id), _rating)
        add_book_edge(user_uuid, int(_book_id), _rating)


    # # write data in MYSQL
    # print("write BOOK_EDGE in MySQL...")
    # all_edges = []
    # for key, value in tqdm(BOOK_EDGE.items()):
    #     book_id_a = key.split("_")[0]
    #     book_id_b = key.split("_")[1]
    #     db.session.add(BookEdge(
    #             book_id_a       = int(book_id_a),
    #             book_id_b       = int(book_id_b),
    #             weight          = value["weight"],
    #             edge_cnt        = value["edge_cnt"],
    #             average_weight  = value["average_weight"],
    #         ))

    # print("write USER_BOOK in MySQL...")
    # all_ratings = []
    # for uuid, value in tqdm(USER_BOOK.items()):
    #     all_ratings.append(BookRating(
    #             uuid    = uuid,
    #             book_id = value["book_id"],
    #             rating  = value["rating"],
    #         ))
    # db.session.add_all(all_ratings)

    # print("write EDGE_NAME in MySQL")
    # db.session.add_all(EDGE_NAME)

    print("commit...")
    try:
        db.session.commit()
    except Exception as e:
        print("ERROR:", e)
        return False
    print("pre_add DONE.")