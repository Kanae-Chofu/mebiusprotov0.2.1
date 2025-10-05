import sqlite3
import re
from datetime import datetime
from modules.utils import now_str

# MeCabによる日本語形態素解析
import MeCab
import unidic_lite

DB_PATH = "db/mebius.db"

# 定数（設計意図の明示）
EMOTION_WORDS = ["嬉しい", "楽しい", "悲しい", "不安", "安心", "つらい", "好き", "嫌い"]
DISCLOSURE_KEYWORDS = ["私", "自分", "最近", "悩み", "好き", "嫌い", "思う", "考える"]

# ✅ 共通DB接続関数
def get_connection():
    return sqlite3.connect(DB_PATH)

# ✅ 会話取得＋長さチェック（min_len件以上）
def get_valid_chat(sender, receiver, min_len=1):
    rows = get_chat(sender, receiver)
    return rows if len(rows) >= min_len else None

# 🧱 初期化
def init_feedback_db():
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS chat_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            receiver TEXT,
            feedback TEXT,
            timestamp TEXT
        )''')
        conn.commit()
    finally:
        conn.close()

# 💾 手動フィードバック保存
def save_feedback(sender, receiver, feedback_text):
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("INSERT INTO chat_feedback (sender, receiver, feedback, timestamp) VALUES (?, ?, ?, ?)",
                  (sender, receiver, feedback_text, now_str()))
        conn.commit()
    finally:
        conn.close()

# 📥 手動フィードバック取得
def get_feedback(sender, receiver):
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute('''SELECT feedback, timestamp FROM chat_feedback
                     WHERE sender=? AND receiver=?
                     ORDER BY timestamp DESC''', (sender, receiver))
        return c.fetchall()
    finally:
        conn.close()

# 💬 会話取得（共通）
def get_chat(sender, receiver):
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute('''SELECT sender, message, timestamp FROM chat_messages
                     WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?)
                     ORDER BY timestamp''', (sender, receiver, receiver, sender))
        return c.fetchall()
    finally:
        conn.close()

# 🤖 会話の連続性フィードバック
def continuity_feedback(sender, receiver):
    rows = get_valid_chat(sender, receiver, min_len=4)
    if not rows:
        return "会話の流れを分析するには少し短すぎます"

    timestamps = [datetime.strptime(r[2], "%Y-%m-%d %H:%M:%S") for r in rows]
    gaps = [(timestamps[i] - timestamps[i-1]).total_seconds() for i in range(1, len(timestamps))]
    turns = [r[0] for r in rows]
    switch_count = sum(1 for i in range(1, len(turns)) if turns[i] != turns[i-1])
    switch_ratio = switch_count / (len(turns) - 1)
    avg_gap = sum(gaps) / len(gaps)

    if avg_gap < 90 and switch_ratio > 0.6:
        return f"自然な流れで会話が続いていました（平均間隔 {int(avg_gap)}秒・交互率 {int(switch_ratio*100)}%）"
    elif avg_gap < 180:
        return f"適度なテンポで会話が展開されていました（平均間隔 {int(avg_gap)}秒）"
    else:
        return f"間が空きがちで、会話の流れはやや途切れがちでした（平均間隔 {int(avg_gap)}秒）"

# 🤖 発言割合
def auto_feedback(sender, receiver):
    rows = get_valid_chat(sender, receiver)
    if not rows:
        return "会話がまだありません"
    total = len(rows)
    sender_count = sum(1 for r in rows if r[0] == sender)
    ratio = sender_count / total
    if ratio > 0.7:
        return f"あなたの発言が多めでした（{int(ratio*100)}%）"
    elif ratio < 0.3:
        return f"相手の話をよく聞いていました（{int(ratio*100)}%）"
    else:
        return f"バランスの取れた会話でした（{int(ratio*100)}%）"

# 🤖 問いの頻度
def question_feedback(sender, receiver):
    rows = get_valid_chat(sender, receiver)
    if not rows:
        return "会話がまだありません"
    total = len(rows)
    question_count = sum(1 for s, m, _ in rows if s == sender and "?" in m)
    if question_count == 0:
        return "問いかけはありませんでした。沈黙や受け止める時間が多かったかも"
    elif question_count / total > 0.5:
        return f"問いかけが多く、関係性を探る姿勢が見られました（{question_count}件）"
    else:
        return f"問いが適度に含まれていて、会話に流れがありました（{question_count}件）"

# 🤖 沈黙の余白
def silence_feedback(sender, receiver):
    rows = get_valid_chat(sender, receiver, min_len=2)
    if not rows:
        return "沈黙の分析には会話が少なすぎます"
    timestamps = [datetime.strptime(r[2], "%Y-%m-%d %H:%M:%S") for r in rows]
    gaps = [(timestamps[i] - timestamps[i-1]).total_seconds() for i in range(1, len(timestamps))]
    avg_gap = sum(gaps) / len(gaps)
    if avg_gap > 300:
        return f"沈黙の余白が長く、安心感を生む会話だったかもしれません（平均 {int(avg_gap)}秒）"
    elif avg_gap > 60:
        return f"適度な間があり、問いや受け止めが活きていたようです（平均 {int(avg_gap)}秒）"
    else:
        return f"テンポよく会話が進みました（平均 {int(avg_gap)}秒）"

# 🤖 感情語の使用率
def emotion_feedback(sender, receiver):
    rows = get_valid_chat(sender, receiver)
    if not rows:
        return "会話がまだありません"
    count = sum(1 for s, m, _ in rows if s == sender and any(word in m for word in EMOTION_WORDS))
    if count == 0:
        return "感情表現は控えめでした。沈黙や問いが中心だったかも"
    elif count > 5:
        return f"感情を共有することで、関係性が深まっていたようです（{count}件）"
    else:
        return f"感情語が適度に使われていました（{count}件）"

# 🤖 応答率
def response_feedback(sender, receiver):
    rows = get_valid_chat(sender, receiver, min_len=2)
    if not rows:
        return "応答の分析には会話が少なすぎます"
    response_count = 0
    for i in range(1, len(rows)):
        prev_sender = rows[i-1][0]
        curr_sender = rows[i][0]
        if prev_sender != sender and curr_sender == sender:
            response_count += 1
    ratio = response_count / len(rows)
    if ratio > 0.4:
        return f"相手の言葉をよく受け止めていました（応答率 {int(ratio*100)}%）"
    else:
        return f"問いや沈黙が中心の会話だったかもしれません（応答率 {int(ratio*100)}%）"

# 🤖 会話の長さ
def length_feedback(sender, receiver):
    rows = get_valid_chat(sender, receiver)
    if not rows:
        return "会話がまだありません"
    start = datetime.strptime(rows[0][2], "%Y-%m-%d %H:%M:%S")
    end = datetime.strptime(rows[-1][2], "%Y-%m-%d %H:%M:%S")
    duration = (end - start).total_seconds() / 60
    if len(rows) > 20 and duration > 30:
        return f"継続的なやりとりがあり、関係性が育っているようです（{len(rows)}件・{int(duration)}分）"
    else:
        return f"短めの会話でした（{len(rows)}件・{int(duration)}分）"

# 🤖 日本語テキストの形態素解析とトークン化
def tokenize_japanese(text):
    tagger = MeCab.Tagger(f"-d {unidic_lite.DICDIR} -Owakati")
    return tagger.parse(text).strip().split()

# 🤖 話題の広がり（語彙の多様性）
def diversity_feedback(sender, receiver):
    rows = get_valid_chat(sender, receiver)
    if not rows:
        return "会話がまだありません"
    sender_msgs = [m for s, m, _ in rows if s == sender]
    all_words = []
    for msg in sender_msgs:
        words = tokenize_japanese(msg)
        all_words.extend(words)
    unique_words = set(all_words)
    count = len(unique_words)
    if count > 50:
        return f"語彙が豊かで、多様な話題が展開されていました（{count}種類）"
    elif count > 20:
        return f"適度な語彙の広がりがあり、問いが自然に展開されていました（{count}種類）"
    else:
        return f"語彙は少なめでした（{count}種類）"

# 🤖 自己開示度
def disclosure_feedback(sender, receiver):
    rows = get_valid_chat(sender, receiver)
    if not rows:
        return "会話がまだありません"
    count = sum(1 for s, m, _ in rows if s == sender and any(k in m for k in DISCLOSURE_KEYWORDS))
    if count > 10:
        return f"自己開示が多く、関係性が深まっていたようです（{count}件）"
    elif count > 3:
        return f"自分のことを適度に語ることで、安心感が育まれていたようです（{count}件）"
    else:
        return f"自己開示は控えめでした。問いや沈黙が中心だったかもしれません（{count}件）"

# 🤝 関係性の継続性フィードバック
def continuity_duration_feedback(sender, receiver):
    rows = get_valid_chat(sender, receiver)
    if not rows:
        return "会話がまだ始まっていません"
    start = datetime.strptime(rows[0][2], "%Y-%m-%d %H:%M:%S")
    end = datetime.strptime(rows[-1][2], "%Y-%m-%d %H:%M:%S")
    duration_days = (end - start).days
    if duration_days >= 30:
        return f"この関係は {duration_days} 日間続いており、継続的な対話が育っています"
    elif duration_days >= 7:
        return f"この関係は {duration_days} 日間続いており、安定したやりとりが見られます"
    elif duration_days >= 2:
        return f"この関係は {duration_days} 日間続いており、対話の芽が育ち始めています"
    else:
        return f"会話は始まったばかりで、これから関係性が育っていくかもしれません（{duration_days}日）"