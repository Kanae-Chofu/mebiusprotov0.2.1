# chatkai2.py

import streamlit as st
import sqlite3
import os
import bcrypt
from datetime import datetime
from dotenv import load_dotenv
from streamlit_autorefresh import st_autorefresh

load_dotenv()

DB_PATH = "db/mebius.db"
STAMPS = ["😀","😂","❤️","👍","😢","🎉","🔥","🤔",
          "🥰","😎","🙌","💀","🌟","🍕","☕","🛹",
          "🐶","🐱","🐭","🐹","🐰","🦊","🐻","🐼",
          "🦁","🐮","🐷","🐸","🐵","🦄"]

# --- 共通ユーティリティ ---
def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# --- DB初期化 ---
def init_db():
    os.makedirs("db", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        display_name TEXT,
        kari_id TEXT,
        registered_at TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS friends (
        user TEXT,
        friend TEXT,
        UNIQUE(user, friend)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        receiver TEXT,
        message TEXT,
        timestamp TEXT,
        message_type TEXT DEFAULT 'text',
        is_read INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS message_reactions (
        message_id INTEGER,
        user TEXT,
        reaction TEXT,
        PRIMARY KEY (message_id, user)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS feedback (
        sender TEXT,
        receiver TEXT,
        feedback TEXT,
        timestamp TEXT
    )''')
    conn.commit()
    conn.close()

# --- ユーザー管理 ---
def register_user(username, password, display_name="", kari_id=""):
    username = username.strip()
    password = password.strip()
    if not username or not password:
        return "ユーザー名とパスワードを入力してください"
    hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        c.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)",
                  (username, hashed_pw, display_name, kari_id, now_str()))
        conn.commit()
        return "OK"
    except sqlite3.IntegrityError:
        return "このユーザー名は既に使われています"
    finally:
        conn.close()

def login_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username=?", (username,))
    result = c.fetchone()
    conn.close()
    if result and bcrypt.checkpw(password.encode("utf-8"), result[0]):
        st.session_state.username = username
        return True
    return False

def get_current_user():
    return st.session_state.get("username", None)

def get_display_name(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT display_name FROM users WHERE username=?", (username,))
    result = c.fetchone()
    conn.close()
    return result[0] if result and result[0] else username

def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT username FROM users ORDER BY username")
    users = [row[0] for row in c.fetchall()]
    conn.close()
    return users

# --- チャット機能 ---
def save_message(sender, receiver, message, message_type="text"):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO chat_messages (sender, receiver, message, timestamp, message_type) VALUES (?, ?, ?, ?, ?)",
              (sender, receiver, message, now_str(), message_type))
    conn.commit()
    conn.close()

def get_messages(user, partner):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT id, sender, message, message_type FROM chat_messages
                 WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?)
                 ORDER BY timestamp''', (user, partner, partner, user))
    rows = c.fetchall()
    c.execute("UPDATE chat_messages SET is_read=1 WHERE receiver=? AND sender=? AND is_read=0", (user, partner))
    conn.commit()
    conn.close()
    return rows

def get_unread_count(user, partner):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM chat_messages WHERE receiver=? AND sender=? AND is_read=0", (user, partner))
    count = c.fetchone()[0]
    conn.close()
    return count

def get_friends(user):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT friend FROM friends WHERE user=?", (user,))
    res = [r[0] for r in c.fetchall()]
    conn.close()
    return res

def add_friend(user, friend):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO friends (user, friend) VALUES (?, ?)", (user, friend))
    conn.commit()
    conn.close()

def remove_friend(user, friend):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM friends WHERE user=? AND friend=?", (user, friend))
    conn.commit()
    conn.close()

def get_stamp_images():
    stamp_dir = "stamps"
    if not os.path.exists(stamp_dir):
        os.makedirs(stamp_dir)
    return [os.path.join(stamp_dir, f) for f in os.listdir(stamp_dir)
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif"))]

def save_reaction(message_id, user, reaction):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO message_reactions VALUES (?, ?, ?)", (message_id, user, reaction))
    conn.commit()
    conn.close()

def get_reactions(message_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT reaction, COUNT(*) FROM message_reactions WHERE message_id=? GROUP BY reaction", (message_id,))
    results = c.fetchall()
    conn.close()
    return results

# --- フィードバック ---
def save_feedback(sender, receiver, feedback):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO feedback VALUES (?, ?, ?, ?)", (sender, receiver, feedback, now_str()))
    conn.commit()
    conn.close()

def get_feedback(sender, receiver):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT feedback, timestamp FROM feedback WHERE sender=? AND receiver=? ORDER BY timestamp DESC",
              (sender, receiver))
    results = c.fetchall()
    conn.close()
    return results

# --- メインUI ---
def render():
    st.set_page_config(page_title="1対1チャット", layout="wide")
    init_db()

    user = get_current_user()
    if not user:
        st.warning("ログインしてください（共通ID）")
        return

    st.subheader("💬 1対1チャット空間")
    st.write(f"あなたの表示名： `{get_display_name(user)}`")

    # --- 友達管理 ---
    st.markdown("---")
    st.subheader("👥 友達を管理")
    users_list = get_all_users()
    new_friend = st.text_input("追加または削除するユーザー名", key="add_friend_input", max_chars=64)
    col1, col2 = st.columns(2)
    if col1.button("追加"):
        if new_friend == user:
            st.error("自分自身は追加できません")
        elif new_friend not in users_list:
            st.error("存在しないユーザーです")
        else:
            add_friend(user, new_friend)
            st.success(f"{new_friend} を追加しました")

    if col2.button("削除"):
        remove_friend(user, new_friend)
        st.success(f"{new_friend} を削除しました")

    friends = get_friends(user)
    partner = st.selectbox("チャット相手を選択", friends)

    if not partner:
        return

    unread = get_unread_count(user, partner)
    if unread:
        st.info(f"📩 {unread}件の未読メッセージがあります")

    st.markdown("---")
    st.subheader("📨 メッセージ履歴")
    st_autorefresh(interval=3000, key="auto_refresh")
    chat_placeholder = st.empty()

    def render_chat():
        messages = get_messages(user, partner)
        chat_box_html = """
        <div id='chat-box' style='height:400px; overflow-y:auto; border:1px solid #ccc; padding:10px; background-color:#000; color:white;'>
        """

        for msg_id, sender, msg, msg_type in messages:
            align = "right" if sender == user else "left"
            bg = "#1F2F54" if align == "right" else "#333"

            # --- メッセージ表示 ---
            if msg_type == "stamp" and os.path.exists(msg):
                chat_box_html += f"""
                <div style='text-align:{align}; margin:10px 0;'>
                    <img src='{msg}' style='width:100px; border-radius:10px;'>
                </div>
                """
            elif len(msg.strip()) <= 2 and all('\U0001F300' <= c <= '\U0001FAFF' or c in '❤️🔥🎉' for c in msg):
                chat_box_html += f"""
                <div style='text-align:{align}; margin:5px 0; font-size:40px;'>{msg}</div>
                """
            else:
                chat_box_html += f"""
                <div style='text-align:{align}; margin:5px 0;'>
                    <span style='background-color:{bg}; color:white; padding:8px 12px; border-radius:10px; display:inline-block; max-width:80%;'>
                        {msg}
                    </span>
                </div>
                """

            # --- リアクション表示 ---
            reactions = get_reactions(msg_id)
            if reactions:
                reaction_str = " ".join([f"{r}×{n}" for r, n in reactions])
                chat_box_html += f"""
                <div style='text-align:{align}; font-size:14px; color:gray;'>{reaction_str}</div>
                """

            # --- いいねボタン ---
            if st.button("👍", key=f"like_{msg_id}"):
                save_reaction(msg_id, user, "👍")
                st.rerun()

        chat_box_html += """
        </div>
        <script>
            var chatBox = document.getElementById('chat-box');
            if (chatBox) {
                chatBox.scrollTop = chatBox.scrollHeight;
            }
        </script>
        """

        chat_placeholder.markdown(chat_box_html, unsafe_allow_html=True)