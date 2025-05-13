from datetime import datetime


def get_curr_str_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
