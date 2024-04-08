from flask import Flask
from flask_redis import FlaskRedis
import config as cfg
import logging

from db.model import db
from db.script import pre_add, add_books
from widget.datetime import now_time


# logging init
def cn_time(sec, what):
    return now_time().timetuple()
logging.Formatter.converter = cn_time
logging.basicConfig(
    format      = '%(asctime)s [%(levelname)s] %(message)s',
    datefmt     = '%Y-%m-%d %H:%M:%S',
    filename    = cfg.LOG_FILE_PATH,
    encoding    = 'utf-8',
    level       = logging.INFO,
)

# redis
rds = FlaskRedis()


def create_app():
    app = Flask(__name__)

    # Database
    app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://{cfg.username}:{cfg.password}@{cfg.domain}/{cfg.database_name}"
    db.init_app(app)
    with app.app_context():
        db.create_all()

    # TODO: 预添加数据, 只在迁移时使用一次,
    # 其他时候注释掉, 否则会导致非预添加数据丢失
    # with app.app_context():
        # pre_add()
        # add_books()

    # redis
    app.config['REDIS_URL'] = cfg.redis_url
    rds.init_app(app)

    from views import views_bp
    app.register_blueprint(views_bp)

    with app.app_context():
        print(app.url_map)

    return app


if __name__ == "__main__":
    app = create_app()

    app.run(host="0.0.0.0", port=5000)
