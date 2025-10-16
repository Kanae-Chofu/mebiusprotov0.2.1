import streamlit as st
import sqlite3
from modules.user import get_current_user
from modules.utils import now_str

DB_PATH = "db/mebius.db"

# ----------------------
# DB操作
# ----------------------
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

def save_profile(username, text):
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        c.execute("REPLACE INTO user_profiles (username, profile_text, updated_at) VALUES (?, ?, ?)",
                  (username, text, now_str()))
        conn.commit()
    finally:
        conn.close()

def load_profile(username):
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        c.execute("SELECT profile_text, updated_at FROM user_profiles WHERE username=?", (username,))
        result = c.fetchone()
        return result if result else ("", "")
    finally:
        conn.close()

def list_users():
    """登録されているユーザー名一覧を取得"""
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        c.execute("SELECT username FROM user_profiles ORDER BY username")
        return [row[0] for row in c.fetchall()]
    finally:
        conn.close()

# ----------------------
# UI表示
# ----------------------
def render():
    init_profile_db()
    user = get_current_user()
    if not user:
        st.warning("ログインしてください")
        return

    st.title("📝 プロフィール管理")

    # --- 自分のプロフィール編集 ---
    st.header("🔹 自分のプロフィール")
    current_text, updated = load_profile(user)
    st.caption(f"最終更新：{updated}" if updated else "まだプロフィールは未記入です")

    new_text = st.text_area("あなた自身の語りをここに書いてください", value=current_text, height=300)
    if st.button("保存する"):
        save_profile(user, new_text)
        st.success("プロフィールを保存しました")
        st.experimental_rerun()

    st.markdown("---")

    # --- 他人のプロフィール閲覧 ---
    st.header("🔹 他のユーザーのプロフィールを見る")

    all_users = list_users()
    # 自分を除外して選択肢にする
    other_users = [u for u in all_users if u != user]

    if other_users:
        selected_user = st.selectbox("ユーザーを選択", other_users)
        profile_text, updated = load_profile(selected_user)
        if profile_text:
            st.caption(f"{selected_user} さんの最終更新：{updated}")
            st.write(profile_text)
        else:
            st.info(f"{selected_user} さんのプロフィールはまだ登録されていません")
    else:
        st.info("他のユーザーのプロフィールはまだ登録されていません")
