import re
from datetime import datetime, timedelta

def now_str():
    # JSTで現在時刻を文字列で返す
    jst = datetime.utcnow() + timedelta(hours=9)
    return jst.strftime("%Y-%m-%d %H:%M:%S")

def to_jst(utc_str):
    # UTC文字列 → JST文字列に変換
    utc = datetime.strptime(utc_str, "%Y-%m-%d %H:%M:%S")
    jst = utc + timedelta(hours=9)
    return jst.strftime("%Y-%m-%d %H:%M:%S")

def sanitize_message(text: str, max_len: int) -> str:
    text = text.replace("\r", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_len]