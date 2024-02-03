import toml
import os
config = toml.load('config.toml')

DEBUG               = config["APP"]["DEBUG"]
HOME_DIR            = config["APP"]["HOME_DIR"]
AUTH_SECRET_KEY     = config["APP"]["AUTH_SECRET_KEY"]
LOG_FILE_PATH       = os.path.join(HOME_DIR, "project.log")

# database
username        = config["DATABASE"]["USERNAME"]
password        = config["DATABASE"]["PASSWORD"]
domain          = config["DATABASE"]["DOMAIN"]
database_name   = config["DATABASE"]["DATABASE_NAME"]
redis_url       = config["DATABASE"]["REDIS_URL"]
