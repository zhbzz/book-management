
from apscheduler.triggers.cron import CronTrigger
from functools import wraps
import config as cfg
# import pytz
import datetime
import os
import logging

from db.model import db
from db.model import User
from db.model import Shop
from db.model import Email
from db.model import OnlineStatus
from db.model import CompleteTask
from db.model import CVOnlineStatus
from db.model import RecurringTasks
from db.model import UserDailyCount
from db.model import PurchaseHistory
from db.model import InteractionTimes
from db.model import TouchInteractionTimes
from widget.datetime.datetime import TIME_ZONE
from widget.datetime.datetime import now_time
from widget.datetime.datetime import now_time_str
from widget.datetime.datetime import parse_time_str
from widget.datetime.datetime import time_interval


daily_trigger = CronTrigger(
    day         = "*",
    hour        = 5,
    minute      = 0,
    second      = 0,
    timezone    = TIME_ZONE,
)

weekly_trigger = CronTrigger(
    week        = "*",
    day_of_week = "mon",
    hour        = 5,
    minute      = 0,
    second      = 0,
    timezone    = TIME_ZONE,
)

monthly_trigger = CronTrigger(
    month       = "*",
    day         = 1,
    hour        = 5,
    minute      = 0,
    second      = 0,
    timezone    = TIME_ZONE,
)

scheduled_tasks = []

def scheduled_task(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        func(*args, **kwargs)

    scheduled_tasks.append(wrapper)

    return wrapper

def add_tasks(scheduler, app):
    for task_func in scheduled_tasks:
        task_func(scheduler, app)


# 更新每日签到
@scheduled_task
def update_daily_checkin(scheduler, app):
    def operate():
        with app.app_context():
            User.query.filter_by(checkin_today=True).update({'checkin_today': False})

            try:
                db.session.commit()

                logging.info("[LOG]: Daily task executed successfully")

            except Exception as e:
                db.session.rollback()
                logging.error(str(e))
                # operate()

    scheduler.add_job(id="update_daily_checkin", func=operate, trigger=daily_trigger)


# 更新每月签到
@scheduled_task
def update_monthly_checkin(scheduler, app):
    def operate():
        with app.app_context():
            db.session.query(User).update({
                User.checkin_last_month: User.checkin_month,
                User.checkin_month: 0
            })
            try:
                db.session.commit()
                logging.info("[LOG]: Monthly task executed successfully")
            except Exception as e:
                db.session.rollback()
                logging.error(str(e))
                # operate()

    scheduler.add_job(id="update_monthly_checkin", func=operate, trigger=monthly_trigger)


# 更新每日任务
@scheduled_task
def update_daily_task(scheduler, app):
    def operate():
        with app.app_context():
            result = db.session.query(RecurringTasks, CompleteTask).filter(
                RecurringTasks.task_type == "daily",
                RecurringTasks.task_id == CompleteTask.task_id,
            ).all()

            for _, complete_task in result:
                db.session.delete(complete_task)

            try:
                db.session.commit()
                logging.info("update_daily_task success")
            except Exception as e:
                logging.error(str(e))
                db.session.rollback()

    scheduler.add_job(id="update_daily_task", func=operate, trigger=daily_trigger)


# 更新每周任务
@scheduled_task
def update_weekly_task(scheduler, app):
    def operate():
        with app.app_context():
            result = db.session.query(RecurringTasks, CompleteTask).filter(
                RecurringTasks.task_type == "weekly",
                RecurringTasks.task_id == CompleteTask.task_id,
            ).all()

            for _, complete_task in result:
                db.session.delete(complete_task)

            try:
                db.session.commit()
                logging.info("update_weekly_task success")
            except Exception as e:
                logging.error(str(e))
                db.session.rollback()

    scheduler.add_job(id="update_weekly_task", func=operate, trigger=weekly_trigger)


# 每天零点更新需要进入账号保护期或删除的账户
@scheduled_task
def update_user_del_state(scheduler, app):
    def operate():
        from db.model import UserMac
        from db.model import UserLevel
        from db.model import UserPopupCount
        from db.model import UserDailyCount
        from db.model import UserHistoryNumber
        with app.app_context():
            # 数据保存期->删除
            result = User.query.filter_by(del_state=2).all()
            for res in result:
                del_date = parse_time_str(res.del_datetime)
                current = now_time()
                if del_date + datetime.timedelta(days=365) <= current:
                    username = res.username
                    user_mac = UserMac.query.filter_by(username=username).first()
                    user_level = UserLevel.query.filter_by(username=username).first()
                    user_popup = UserPopupCount.query.filter_by(username=username).first()
                    user_dailycount = UserDailyCount.query.filter_by(username=username).first()
                    user_historynumber = UserHistoryNumber.query.filter_by(username=username).first()
                    db.session.delete(res)
                    db.session.delete(user_mac)
                    db.session.delete(user_level)
                    db.session.delete(user_popup)
                    db.session.delete(user_dailycount)
                    db.session.delete(user_historynumber)

            # 账号保护期->数据保存期
            result = User.query.filter_by(del_state=1).all()
            for res in result:
                del_date = parse_time_str(res.del_datetime)
                current = now_time()
                if del_date + datetime.timedelta(days=15) <= current:
                    res.del_state = 2
                    res.del_datetime = current
            try:
                db.session.commit()
                logging.info("update_user_del_state success")
            except Exception as e:
                logging.error(str(e))
                db.session.rollback()

    scheduler.add_job(id="update_user_del_state", func=operate, trigger=daily_trigger)

@scheduled_task
def update_user_talk_count(scheduler, app):
    def operate():
        logging.info("update talk limit " + now_time_str())

        with app.app_context():
            users = UserDailyCount.query.all()
            for user in users:
                user.cnt = 0

            try:
                db.session.commit()
            except Exception as e:
                logging.error(str(e))
                db.session.rollback()
                # operate()

    scheduler.add_job(id="update_user_talk_count", func=operate, trigger=daily_trigger)


@scheduled_task
def update_user_online_daily(scheduler, app):
    """
    - 保存redis中的在线时间段, 并保存到文件 `online_status_daily.csv`
    - 更新周和月
    """
    def operate():
        from app import rds

        online_data = {} # 详细在线信息
        online_time = {} # 在线总时间
        day = datetime.datetime.now().day

        with app.app_context():
            # 更新在线情况
            users = OnlineStatus.query.all()
            for user in users:
                key = f"online_{user.username}"
                all_seconds = 0

                # redis中的在线时间段
                while rds.llen(key) > 0:
                    period = rds.lpop(key).decode("utf-8")
                    moment1 = parse_time_str(period.split("~")[0])
                    moment2 = parse_time_str(period.split("~")[1])
                    all_seconds += (moment2 - moment1).seconds
                    if user.username not in online_data:
                        online_data[user.username] = []
                    online_data[user.username].append(period)

                user.online_today += all_seconds
                if user.online_today != 0:
                    user.online_total += user.online_today
                    user.online_yesterday = user.online_today
                    user.online_week += user.online_today
                    user.online_month |= 1 << (day - 1)
                    online_time[user.username] = user.online_today
                    user.online_today = 0

            # cv在线情况
            cv_users = CVOnlineStatus.query.all()
            for user in cv_users:
                user.online_total += user.online_today
                user.online_yesterday = user.online_today
                user.online_week += user.online_today
                user.online_month += user.online_today
                user.online_today = 0

            try:
                db.session.commit()
            except Exception as e:
                logging.error(str(e))
                db.session.rollback()

        # 用户详细在线时间段
        from config import HOME_DIR
        import os

        online_folder = os.path.join(HOME_DIR, "backup/online")
        if not os.path.exists(online_folder):
            os.makedirs(online_folder)

        online_path = os.path.join(
            online_folder,
            f"daily_{now_time_str()}.csv",
        )
        with open(online_path, "w") as f:
            f.truncate()   #清空文件
            # 第一行写入当前时间
            f.write(now_time_str() + "\n")
            # 后续写入用户的详细在线时间
            for username in online_data:
                periods = online_data[username]
                for period in periods:
                    f.write(f"{username},{period}\n")

    trigger = CronTrigger(
        hour        = 23,
        minute      = 59,
        second      = 59,
        timezone    = TIME_ZONE,
    )
    scheduler.add_job(id="update_user_online_daily", func=operate, trigger=trigger)


# 本周在线时间
@scheduled_task
def update_user_online_weekly(scheduler, app):
    """
    - 更新用户本周在线总时长
    """
    def operate():
        logging.info("update user online weekly " + now_time_str())

        # online_time = {}
        with app.app_context():
            # 更新本周在线情况
            users = OnlineStatus.query.all()
            for user in users:
                user.online_last_week = user.online_week
                user.online_week = 0

            # 更新本周cv在线情况
            users = CVOnlineStatus.query.all()
            for user in users:
                user.online_last_week = user.online_week
                user.online_week = 0

            try:
                db.session.commit()
            except Exception as e:
                logging.error(str(e))
                db.session.rollback()

    trigger = CronTrigger(
        day_of_week = "sun",
        hour        = 23,
        minute      = 59,
        second      = 59,
        timezone    = TIME_ZONE,
    )
    scheduler.add_job(id="update_user_online_weekly", func=operate, trigger=trigger)


@scheduled_task
def update_user_online_monthly(scheduler, app):
    """
    - 更新用户本月在线总时长
    """
    def operate():
        logging.info("update user online monthly " + now_time_str())

        with app.app_context():
            users = OnlineStatus.query.all()
            for user in users:
                user.online_last_month = user.online_month
                user.online_month = 0

            users = CVOnlineStatus.query.all()
            for user in users:
                user.online_last_month = user.online_month
                user.online_month = 0

            try:
                db.session.commit()
            except Exception as e:
                logging.error(str(e))
                db.session.rollback()

    trigger = CronTrigger(
        day         = 1,
        hour        = 23,
        minute      = 59,
        second      = 59,
        timezone    = TIME_ZONE,
    )
    scheduler.add_job(id="update_user_online_monthly", func=operate, trigger=trigger)


@scheduled_task
def backup_log_file(scheduler, app):
    def operate():
        from config import HOME_DIR
        from config import LOG_FILE_PATH
        import os

        backup_log_folder = os.path.join(HOME_DIR, "backup/log")
        if not os.path.exists(backup_log_folder):
            os.makedirs(backup_log_folder)

        backup_log_file = os.path.join(backup_log_folder, f"{now_time_str('%Y-%m-%d').replace(' ', '-')}.log")

        with open(LOG_FILE_PATH, "r+") as f:
            log_file = f.readlines()
            f.seek(0)
            f.truncate()

        with open(backup_log_file, "w") as f:
            f.writelines(log_file)

    trigger = CronTrigger(
        hour        = 0,
        minute      = 0,
        second      = 0,
        timezone    = TIME_ZONE,
    )
    scheduler.add_job(id="backup_log_file", func=operate, trigger=trigger)


@scheduled_task
def update_mail_remainder(scheduler, app):
    def operate():
        with app.app_context():
            results = Email.query.all()
            for res in results:
                if res.remainder > 0:
                    res.remainder -= 1

            try:
                db.session.commit()
                logging.info("update_user_del_state success")
            except Exception as e:
                logging.error(str(e))
                db.session.rollback()

    trigger = CronTrigger(
        minute      = 0,
        second      = 0,
        timezone    = TIME_ZONE,
    )
    scheduler.add_job(id="update_mail_remainder", func=operate, trigger=trigger)


@scheduled_task
def update_shop_daily(scheduler, app):
    def operate():
        with app.app_context():
            items = Shop.query.filter_by(refresh_period=1).all()
            for item in items:
                # 删除所有用户购买该物品的记录
                history = PurchaseHistory.query.filter_by(goods_id=item.goods_id).all()
                for histry in history:
                    histry.cnt = 0

            try:
                db.session.commit()
                logging.info("update_shop_daily success")
            except Exception as e:
                logging.error(str(e))
                db.session.rollback()

    scheduler.add_job(id="update_shop_daily", func=operate, trigger=daily_trigger)


@scheduled_task
def update_shop_weekly(scheduler, app):
    def operate():
        with app.app_context():
            items = Shop.query.filter_by(refresh_period=2).all()
            for item in items:
                # 删除所有用户购买该物品的记录
                history = PurchaseHistory.query.filter_by(goods_id=item.goods_id).all()
                for histry in history:
                    histry.cnt = 0

            try:
                db.session.commit()
                logging.info("update_shop_weekly success")
            except Exception as e:
                logging.error(str(e))
                db.session.rollback()

    scheduler.add_job(id="update_shop_weekly", func=operate, trigger=weekly_trigger)


@scheduled_task
def update_shop_monthly(scheduler, app):
    def operate():
        with app.app_context():
            items = Shop.query.filter_by(refresh_period=3).all()
            for item in items:
                # 删除所有用户购买该物品的记录
                history = PurchaseHistory.query.filter_by(goods_id=item.goods_id).all()
                for histry in history:
                    histry.cnt = 0

            try:
                db.session.commit()
                logging.info("update_shop_monthly success")
            except Exception as e:
                logging.error(str(e))
                db.session.rollback()

    scheduler.add_job(id="update_shop_monthly", func=operate, trigger=monthly_trigger)


@scheduled_task
def update_interaction_times(scheduler, app):
    def operate():
        with app.app_context():
            interaciton_times = InteractionTimes.query.all()
            for item in interaciton_times:
                item.count = 0

            interaciton_times = TouchInteractionTimes.query.all()
            for item in interaciton_times:
                item.count = 0

            try:
                db.session.commit()
                logging.info("update_shop_monthly success")
            except Exception as e:
                logging.error(str(e))
                db.session.rollback()

    scheduler.add_job(id="update_interaction_times", func=operate, trigger=daily_trigger)


@scheduled_task
def remove_backup_file(scheduler, app):
    def operate():

        def checkNremove(path, filename_prefix):
            files = os.listdir(path)
            for filename in files:
                if filename_prefix not in filename:
                    return
                date_str = filename.split(".")[0][len(filename_prefix):]
                date = parse_time_str(date_str, "%Y-%m-%d")
                if date < now_time() - time_interval(days=14):
                    os.remove(os.path.join(path, filename))


        db_backup_path = os.path.join(cfg.HOME_DIR, "backup")
        db_prefix = "db_backup_"
        checkNremove(db_backup_path, db_prefix)

        log_backup_path = os.path.join(cfg.HOME_DIR, "backup/log")
        log_prefix = ""
        checkNremove(log_backup_path, log_prefix)

    scheduler.add_job(id="remove_backup_file", func=operate, trigger=daily_trigger)
