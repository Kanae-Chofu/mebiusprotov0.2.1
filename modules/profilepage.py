import streamlit as st
import sqlite3
from datetime import datetime

DB_PATH = "db/mebius.db"

# ----------------------
# DB操作（プロフィール）
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
                  (username, text, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
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
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        c.execute("SELECT username FROM user_profiles ORDER BY username")
        return [row[0] for row in c.fetchall()]
    finally:
        conn.close()


# ----------------------
# 仮ユーザー認証（サンプル用）
# ----------------------
def get_current_user():
    # 本来はセッションやログイン情報を参照する
    return st.session_state.get("username", "demo_user")


# ----------------------
# 自己プロフィール編集タブ
# ----------------------
def render_self_profile_editor():
    user = get_current_user()
    st.header("📝 自分のプロフィールを書く")

    current_text, updated = load_profile(user)
    if updated:
        st.caption(f"最終更新：{updated}")
    else:
        st.caption("まだプロフィールは未記入です")

    new_text = st.text_area("あなた自身の語りをここに書いてください（Markdown対応）", value=current_text, height=200)

    # Markdownプレビュー
    st.subheader("プレビュー")
    st.markdown(new_text if new_text else "_ここにプレビューが表示されます_")

    if st.button("💾 保存する", key="save_self_profile"):
        save_profile(user, new_text)
        st.success("プロフィールを保存しました！")
        st.experimental_rerun()


# ----------------------
# プロフィール閲覧タブ
# ----------------------
def render_profile_view():
    st.header("🧬 プロフィール閲覧")

    all_users = list_users()
    if not all_users:
        st.info("登録されているユーザーはまだいません。")
        return

    selected_user = st.selectbox("表示したいユーザーを選択", all_users)
    profile_text, updated = load_profile(selected_user)

    st.markdown(f"### 👤 {selected_user} さんのプロフィール")
    if updated:
        st.caption(f"最終更新：{updated}")
    if profile_text:
        st.markdown(profile_text)
    else:
        st.info("プロフィールがまだ登録されていません。")


# ----------------------
# メイン
# ----------------------
def render():
    st.title("🌸 プロフィール管理アプリ")
    init_profile_db()

    # ユーザー名入力欄（簡易ログイン）
    if "username" not in st.session_state:
        st.session_state.username = st.text_input("ユーザー名を入力してください", "demo_user")

    # タブ切り替え
    tab1, tab2 = st.tabs(["✍️ 自分のプロフィールを書く", "🔍 プロフィールを見る"])

    with tab1:
        render_self_profile_editor()

    with tab2:
        render_profile_view()


if __name__ == "__main__":
    render()
