import jwt
import datetime
import secrets

from app import rds
from config import AUTH_SECRET_KEY
from db.model import db
from db.model import User
from db.model import UserSecretKey

REDIS_KEY_PREFIX = "user_key_" # REDIS_KEY_PREFIX + ${username}

def check_token(token, secrekey=AUTH_SECRET_KEY):
    """
        传递 request 的 headers 中的 Authorization 字段

        成功返回payload: {'uuid': xxxxx}, 失败返回None
    """
    if token == None:
        return None
    token = token.split(" ")
    if token[0] != "bearer" and token[0] != "Bearer":
        return None
    if len(token) == 1:
        return None
    token = token[1]

    # 先取出payload
    try:
        jwt_options = {'verify_signature': False, 'verify_exp': True}
        payload = jwt.decode(token, algorithms=["HS256"], options=jwt_options)
        uuid = payload["uuid"]
    except Exception:
        return None

    user_key = _get_user_secret_key(uuid)
    if user_key == None:
        return None
    secrekey += user_key

    # 生成key后验证, secret_key = 服务器key + 用户key
    try:
        decoded_payload = jwt.decode(token, secrekey, algorithms=["HS256"])
    except Exception:
        return None

    return decoded_payload


def generate_token(uuid, secrekey=AUTH_SECRET_KEY):
    """
    生成token, 不包含 "Bearer " 部分
    """
    res = User.query.filter_by(uuid=uuid).first()
    if res == None:
        return None

    payload = {
        "uuid"      : res.uuid,
        "username"  : res.username,
        "exp"       : datetime.datetime.utcnow() + datetime.timedelta(hours=3) # 过期时间
    }

    user_key = _get_user_secret_key(uuid)
    return jwt.encode(payload, secrekey + user_key, algorithm="HS256")


def _get_user_secret_key(uuid) -> str:
    """
    从redis中获取用户key, 如果用户key不存在, 去数据库中找

    返回用户的key, 如果返回None则为数据库错误

    需要在app.app_context()中调用
    """
    user_key = rds.get(REDIS_KEY_PREFIX + str(uuid))
    if user_key != None:
        user_key = user_key.decode("utf8")
        return user_key

    res = UserSecretKey.query.filter_by(username=uuid).first()
    if res == None:
        user_key = _generate_new_secret_key(uuid)
        if user_key == None:
            return None
    else:
        user_key = res.secret_key
    rds.setex(REDIS_KEY_PREFIX + str(uuid), 1 * 60 * 60, user_key)

    return user_key


def _generate_new_secret_key(uuid) -> str:
    """
    为用户生成新的key, 并更新数据库, 清空redis

    返回生成的新key, 如果返回None则为数据库错误

    需要在app.app_context()中调用
    """
    # 生成128位16进制数, 参数为64字节
    user_key = secrets.token_hex(64)
    res = UserSecretKey.query.filter_by(secret_key=user_key).first()
    while res != None:
        user_key = secrets.token_hex(64)
        res = UserSecretKey.query.filter_by(secret_key=user_key).first()

    new_data = UserSecretKey(
            uuid        = uuid,
            secret_key  = user_key,
        )
    db.session.add(new_data)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return None

    rds.delete(REDIS_KEY_PREFIX + uuid)

    return user_key
