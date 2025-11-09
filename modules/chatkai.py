# chatkai_newapi_autorefresh_v2.py
import streamlit as st
import sqlite3
import os
from modules.user import get_current_user, get_display_name, get_all_users
from modules.utils import now_str
from modules.feedback import init_feedback_db, save_feedback, get_feedback
from dotenv import load_dotenv
from openai import OpenAI
from streamlit_autorefresh import st_autorefresh

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
AI_NAME = "AIアシスタント"

STAMPS = [
    "😀","😂","❤️","👍","😢","🎉","🔥","🤔",
    "🥰","😎","🙌","💀","🌟","🍕","☕","🛹",
    "🐶","🐱","🐭","🐹","🐰","🦊","🐻","🐼",
    "🦁","🐮","🐷","🐸","🐵","🦄"
]

DB_PATH = "db/mebius.db"

# ----------------- DB -----------------
def init_chat_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        receiver TEXT,
        message TEXT,
        timestamp TEXT,
        message_type TEXT DEFAULT 'text'
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS friends (
        user TEXT,
        friend TEXT,
        UNIQUE(user, friend)
    )''')
    conn.commit()
    conn.close()

def save_message(sender, receiver, message, message_type="text"):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO chat_messages (sender, receiver, message, timestamp, message_type) VALUES (?, ?, ?, ?, ?)",
        (sender, receiver, message, now_str(), message_type)
    )
    conn.commit()
    conn.close()

def get_messages(user, partner):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT sender, message, message_type FROM chat_messages
                 WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?)
                 ORDER BY timestamp''', (user, partner, partner, user))
    rows = c.fetchall()
    conn.close()
    return rows

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

# ----------------- AI応答 -----------------
def generate_ai_response(user):
    messages = get_messages(user, AI_NAME)
    messages_for_ai = [{"role": "user", "content": msg} for _, msg, _ in messages[-5:]] or [{"role": "user", "content": "こんにちは！"}]
    try:
        resp = client.chat.completions.create(
            model="gpt-5-nano",
            messages=[{"role": "system", "content": "あなたは親切な日本語のチャットAIです。"}] + messages_for_ai,
            max_completion_tokens=150
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"AI応答でエラーが発生しました: {e}"

# ----------------- チャット描画 -----------------
def render_chat(user, partner):
    messages = get_messages(user, partner)
    for sender, msg, msg_type in messages:
        is_user = sender == user
        if msg_type == "stamp" and os.path.exists(msg):
            st.chat_message("user" if is_user else "assistant").image(msg, width=100)
        elif all('\U0001F300' <= c <= '\U0001FAFF' or c in '❤️🔥🎉' for c in msg) and len(msg.strip()) <= 2:
            st.chat_message("user" if is_user else "assistant", avatar=None).markdown(f"<span style='font-size:40px;'>{msg}</span>", unsafe_allow_html=True)
        else:
            st.chat_message("user" if is_user else "assistant").text(msg)

# ----------------- メイン -----------------
def render():
    st.set_page_config(page_title="ChatKAI", layout="wide")
    init_chat_db()
    init_feedback_db()

    user = get_current_user()
    if not user:
        st.warning("ログインしてください（共通ID）")
        return

    st.markdown("<style>div[data-testid='stAppViewContainer']{background-color:#000;}</style>", unsafe_allow_html=True)
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

    friends = get_friends(user) + [AI_NAME]
    partner = st.selectbox("チャット相手を選択", friends)
    if not partner:
        return

    st.markdown("---")
    st.subheader("📨 メッセージ履歴")

    # --- 自動更新 ---
    st_autorefresh(interval=3000, key="auto_refresh")
    render_chat(user, partner)

    # --- スタンプ ---
    st.markdown("#### 🙂 テキストスタンプ")
    for row in range(0, len(STAMPS), 8):
        cols = st.columns(8)
        for i, stamp in enumerate(STAMPS[row:row+8]):
            if cols[i].button(stamp, key=f"stamp_{stamp}_{row}"):
                save_message(user, partner, stamp)
                if partner == AI_NAME:
                    ai_reply = generate_ai_response(user)
                    save_message(AI_NAME, user, ai_reply)
                render_chat(user, partner)

    # --- 画像スタンプ ---
    st.markdown("#### 🖼 画像スタンプ")
    stamp_images = get_stamp_images()
    if stamp_images:
        cols = st.columns(5)
        for i, img_path in enumerate(stamp_images):
            with cols[i % 5]:
                st.image(img_path, width=60)
                if st.button("送信", key=f"send_img_{i}"):
                    save_message(user, partner, img_path, message_type="stamp")
                    if partner == AI_NAME:
                        ai_reply = generate_ai_response(user)
                        save_message(AI_NAME, user, ai_reply)
                    render_chat(user, partner)
    else:
        st.info("スタンプ画像を /stamps/ フォルダに追加してください。")

    # --- テキスト入力 ---
    new_msg = st.chat_input("ここにメッセージを入力してください")
    if new_msg:
        save_message(user, partner, new_msg)
        if partner == AI_NAME:
            ai_reply = generate_ai_response(user)
            save_message(AI_NAME, user, ai_reply)
        render_chat(user, partner)

    # --- フィードバック ---
    st.markdown("---")
    st.subheader("📝 フィードバック")
    feedback_text = st.text_input("フィードバックを入力", key="feedback_input", max_chars=150)
    if st.button("送信"):
        if feedback_text:
            save_feedback(user, partner, feedback_text)
            st.success("フィードバックを保存しました")
        else:
            st.warning("フィードバックを入力してください")
    feedback_list = get_feedback(user, partner)
    if feedback_list:
        options = [f"{ts}｜{fb}" for fb, ts in feedback_list]
        selected = st.selectbox("表示したいフィードバックを選択してください", options)
        st.write(f"選択されたフィードバック：{selected}")
    else:
        st.write("まだフィードバックはありません。")

if __name__ == "__main__":
    render()
