import streamlit as st
import sqlite3
from modules.user import get_current_user
from modules.utils import now_str

DB_PATH = "db/mebius.db"

# DB初期化
def init_profile_db():
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS user_profiles (
            username TEXT PRIMARY KEY,
            profile_text TEXT,
            updated_at TEXT
        )''')
        conn.commit()
    finally:
        conn.close()

# 保存
def save_profile(username, text):
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        c.execute("REPLACE INTO user_profiles (username, profile_text, updated_at) VALUES (?, ?, ?)",
                  (username, text, now_str()))
        conn.commit()
    finally:
        conn.close()

# 取得
def load_profile(username):
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        c.execute("SELECT profile_text, updated_at FROM user_profiles WHERE username=?", (username,))
        result = c.fetchone()
        return result if result else ("", "")
    finally:
        conn.close()

# UI表示
def render():
    init_profile_db()
    user = get_current_user()
    if not user:
        st.warning("ログインしてください")
        return

    st.title("📝 自分で書くプロフィール")
    current_text, updated = load_profile(user)
    st.caption(f"最終更新：{updated}" if updated else "まだプロフィールは未記入です")

    new_text = st.text_area("あなた自身の語りをここに書いてください", value=current_text, height=300)
    if st.button("保存する"):
        save_profile(user, new_text)
        st.success("プロフィールを保存しました")
        st.rerun()

    st.markdown("---")
    st.subheader("📖 あなたのプロフィール")
    st.write(new_text if new_text else "（まだ書かれていません）")