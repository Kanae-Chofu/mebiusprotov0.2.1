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
# UI表示
# ----------------------
def render():
    init_profile_db()
    user = get_current_user()
    if not user:
        st.warning("ログインしてください")
        return

    st.title("📝 プロフィール管理・ユーザー情報")

    # --- 自分のプロフィール編集 ---
    st.header("🔹 自分のプロフィール")
    current_text, updated = load_profile(user)
    st.caption(f"最終更新：{updated}" if updated else "まだプロフィールは未記入です")
    new_text = st.text_area("あなた自身の語りをここに書いてください", value=current_text, height=200)
    if st.button("保存する"):
        save_profile(user, new_text)
        st.success("プロフィールを保存しました")
        st.experimental_rerun()

    st.markdown("---")

    # --- 他人のプロフィール閲覧 ---
    st.header("🔹 他のユーザーのプロフィールを見る")
    all_users = list_users()
    other_users = [u for u in all_users if u != user]

    if other_users:
        selected_user = st.selectbox("ユーザーを選択", other_users)

        # 自己プロフィール
        profile_text, updated = load_profile(selected_user)
        st.subheader("📖 自己プロフィール")
        if profile_text:
            st.caption(f"{selected_user} さんの最終更新：{updated}")
            st.write(profile_text)
        else:
            st.info("まだプロフィールは登録されていません")

        # ユーザー情報
        profile_info = get_user_profile(selected_user)
        if profile_info:
            st.markdown("---")
            st.subheader("🧬 ユーザー情報")
            st.markdown(f"**表示名：** `{profile_info['display_name']}`")
            st.markdown(f"**仮ID：** `{profile_info['kari_id']}`")
            st.markdown(f"**登録日：** `{profile_info['registered_at']}`")

        # 性格診断
        st.markdown("---")
        st.subheader("🧠 性格診断（Big Five）")
        personality = get_personality(selected_user)
        for trait, score in personality.items():
            st.write(f"・{trait}：{score} / 5")

        # 関係性アクション
        st.markdown("---")
        st.subheader("🤝 関係性アクション")
        if st.button(f"{selected_user} さんと友達になる"):
            st.success("友達申請を送信しました（仮）")

    else:
        st.info("他のユーザーのプロフィールはまだ登録されていません")

# ----------------------
# メイン
# ----------------------
if __name__ == "__main__":
    render()
