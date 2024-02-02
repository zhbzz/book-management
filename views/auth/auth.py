from flask import Blueprint
from flask import request
import uuid
import logging
import re # 正则

from db.model import db
from db.model import User
from widget.datetime import now_time
from widget.jwt.token import check_token
from widget.jwt.token import generate_token
from widget.jwt.token import _generate_new_secret_key
from widget.response_type import ErrorResponse
from widget.response_type import SuccessResponse
from widget.response_type import NotLoginResponse
from widget.response_type import FormatErrorResponse
from widget.response_type import DatabaseErrorResponse


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")



def check_uuid(user_uuid) -> bool:
    """
    返回uuid是否存在
    """
    res = User.query.filter_by(uuid=user_uuid).first()

    if res == None:
        return False
    return True


# 获取用户信息
@auth_bp.get('/info/')
def get_userinfo():
    res = check_token(request.headers.get('Authorization'))
    if res == None:
        return NotLoginResponse().json()

    username = res['username']

    result = User.query.filter_by(username=username).first()

    if result == None:
        return ErrorResponse(message="用户不存在").json()

    ret_data = {
        "uuid"                  : result.uuid,
        "username"              : result.username,
        "email"                 : result.email,
        "registration_time"     : result.registration_time,
    }

    return SuccessResponse(info=ret_data).json()


# 登陆
@auth_bp.post('/login/')
def login():
    token = request.headers.get('Authorization')
    if token != None:
        res = check_token(token)
        if res != None:
            return SuccessResponse().json()

    try:
        data = request.get_json()
    except Exception as e:
        return FormatErrorResponse().json()

    if "username" not in data or data["username"] == None:
        return FormatErrorResponse().json()
    if "password" not in data or data["password"] == None:
        return FormatErrorResponse().json()

    username = data["username"]
    password = data["password"]

    user = User.query.filter_by(
        username = username,
        password = password,
    ).first()

    if user == None:
        return FormatErrorResponse(message='用户名密码错误').json()

    token = generate_token(user.uuid)

    return SuccessResponse(token=f'Bearer {token}').json()


@auth_bp.post('/register/')
def register():
    try:
        data = request.get_json()
    except Exception as e:
        return FormatErrorResponse().json()

    if "username" not in data or data["username"] == None:
        return FormatErrorResponse().json()
    if "password" not in data or data["password"] == None:
        return FormatErrorResponse().json()

    username = data["username"]
    password = data["password"]

    pattern = re.compile(r'[^a-zA-Z0-9_\u4e00-\u9fa5]')
    match = pattern.search(username)
    if match:
        return FormatErrorResponse(message='用户名包含非法字符').json()

    # 设置uuid
    user_uuid = uuid.uuid4()
    while check_uuid(user_uuid):
        user_uuid = uuid.uuid4()

    # 注册时刻
    current_time = now_time()

    new_user = User(
        uuid                = user_uuid,
        username            = username,
        password            = password,
        nickname            = username,
        registration_time   = current_time,
    )
    db.session.add(new_user)

    try:
        db.session.commit()
    except Exception as e:
        logging.error(str(e))
        db.session.rollback()
        return DatabaseErrorResponse().json()

    token = generate_token(user_uuid)

    return SuccessResponse(token=f'Bearer {token}')


@auth_bp.post("/change_password/")
def change_password():
    try:
        data = request.get_json()
    except Exception:
        return FormatErrorResponse().json()


    if "username" not in data or data["username"] == None:
        return FormatErrorResponse().json()
    if "old_password" not in data or data["old_password"] == None:
        return FormatErrorResponse().json()
    if "new_password" not in data or data["new_password"] == None:
        return FormatErrorResponse().json()

    username        = data['username']
    old_password    = data["old_password"]
    new_password    = data["new_password"]

    user = User.query.filter_by(username=username, password=old_password).first()
    if user == None:
        return ErrorResponse(message="用户名密码错误").json()

    user.password = new_password

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return DatabaseErrorResponse().json()

    if _generate_new_secret_key(user.username) == None:
        return DatabaseErrorResponse().json()

    return SuccessResponse().json()
