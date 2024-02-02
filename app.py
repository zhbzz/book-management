from flask import Flask
from flask_redis import FlaskRedis
from db.model import db
import config as cfg

# redis
rds = FlaskRedis()

def create_app():
    app = Flask(__name__)

    # Database
    app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://{cfg.username}:{cfg.password}@{cfg.domain}/{cfg.database_name}"
    db.init_app(app)
    with app.app_context():
        db.create_all()

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

    app.run(host="0.0.0.0", port=5000, debug=True)
