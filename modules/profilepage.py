import streamlit as st
import sqlite3
from modules.user import get_current_user
from modules.utils import now_str, to_jst

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
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        c.execute("SELECT username FROM user_profiles ORDER BY username")
        return [row[0] for row in c.fetchall()]
    finally:
        conn.close()

# ----------------------
# DB操作（ユーザー情報）
# ----------------------
def get_user_profile(username):
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        c.execute("SELECT display_name, kari_id, registered_at FROM users WHERE username=?", (username,))
        result = c.fetchone()
        if result:
            display_name, kari_id, registered_at = result
            return {
                "username": username,
                "display_name": display_name or username,
                "kari_id": kari_id or username,
                "registered_at": to_jst(registered_at)
            }
    finally:
        conn.close()
    return None

def get_personality(username):
    # 仮データ
    return {
        "外向性": 3.8,
        "協調性": 4.2,
        "誠実性": 3.5,
        "神経症傾向": 2.1,
        "開放性": 4.7
    }

# ----------------------
# 自己プロフィールUI（単独）
# ----------------------
def render_self_profile_editor():
    user = get_current_user()
    if not user:
        st.warning("ログインしてください")
        return

    st.header("🔹 自己プロフィール記述")
    current_text, updated = load_profile(user)
    st.caption(f"最終更新：{updated}" if updated else "まだプロフィールは未記入です")
    new_text = st.text_area("あなた自身の語りをここに書いてください", value=current_text, height=200)
    if st.button("保存する", key="save_self_profile"):
        save_profile(user, new_text)
        st.success("プロフィールを保存しました")
        st.experimental_rerun()

# ----------------------
# プロフィール画面（表示のみ）
# ----------------------
def render_profile(target_user):
    profile_info = get_user_profile(target_user)
    if not profile_info:
        st.error("ユーザー情報が見つかりません")
        return

    st.title("🧬 プロフィール画面")
    st.markdown(f"**表示名：** `{profile_info['display_name']}`")
    st.markdown(f"**仮ID：** `{profile_info['kari_id']}`")
    st.markdown(f"**登録日：** `{profile_info['registered_at']}`")

    # 自己プロフィール表示（編集不可）
    st.markdown("---")
    st.subheader("📖 自己プロフィール")
    profile_text, updated = load_profile(target_user)
    if profile_text:
        st.caption(f"{target_user} さんの最終更新：{updated}")
        st.write(profile_text)
    else:
        st.info("プロフィールはまだ登録されていません")

    # 性格診断
    st.markdown("---")
    st.subheader("🧠 性格診断（Big Five）")
    personality = get_personality(target_user)
    for trait, score in personality.items():
        st.write(f"・{trait}：{score} / 5")

    # 関係性アクション
    if target_user != get_current_user():
        st.markdown("---")
        st.subheader("🤝 関係性アクション")
        if st.button(f"{target_user} さんと友達になる", key=f"friend_{target_user}"):
            st.success("友達申請を送信しました（仮）")

# ----------------------
# メイン
# ----------------------
def render():
    init_profile_db()
    st.title("プロフィール管理アプリ")

    # --- 自己プロフィール記述ブロック ---
    render_self_profile_editor()
    st.markdown("---")

    # --- プロフィール閲覧ブロック ---
    all_users = list_users()
    current_user = get_current_user()
    if current_user and current_user not in all_users:
        all_users.append(current_user)  # 自分も追加

    if all_users:
        selected_user = st.selectbox("表示したいユーザーを選択", all_users)
        render_profile(selected_user)
    else:
        st.info("登録されているユーザーはまだいません")

if __name__ == "__main__":
    render()
