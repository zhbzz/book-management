import datetime

# UTC+8
TIME_ZONE = datetime.timezone(datetime.timedelta(hours=8))
FORMAT = "%Y-%m-%d %H:%M:%S"

def now_time() -> datetime.datetime:
    """
    获取当前时间的datetime类型
    """
    return datetime.datetime.now(TIME_ZONE).replace(tzinfo=TIME_ZONE)
    # return datetime.datetime.now(tzinfo = TIME_ZONE)

def now_time_str(format=FORMAT) -> str:
    """
    获取当前时间的字符串
    """
    return datetime.datetime.now(TIME_ZONE).strftime(format)

def get_time_str(time : datetime, format=FORMAT) -> str:
    """
    获取datetime类型的字符串
    """
    return time.strftime(format)

def parse_time_str(time_str : str, format=FORMAT) -> datetime.datetime:
    """
    将字符串解析为datetime类型
    """
    return datetime.datetime.strptime(time_str, format).replace(tzinfo=TIME_ZONE)

def time_interval(**kwargs) -> datetime.timedelta:
    """
    返回时间间隔, 参数有
    - days: float = ...,
    - seconds: float = ...,
    - microseconds: float = ...,
    - milliseconds: float = ...,
    - minutes: float = ...,
    - hours: float = ...,
    - weeks: float = ...
    """
    return datetime.timedelta(**kwargs)
