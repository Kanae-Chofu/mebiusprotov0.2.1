import streamlit as st
import sqlite3
from modules.user import get_current_user
from modules.utils import now_str, to_jst

DB_PATH = "db/mebius.db"

# ----------------------
# DB接続キャッシュ
# ----------------------
@st.cache_resource
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

# ----------------------
# DB操作（プロフィール）
# ----------------------
def init_profile_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS user_profiles (
        username TEXT PRIMARY KEY,
        profile_text TEXT,
        updated_at TEXT
    )''')
    conn.commit()

def save_profile(username, text):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "REPLACE INTO user_profiles (username, profile_text, updated_at) VALUES (?, ?, ?)",
        (username, text, now_str())
    )
    conn.commit()

def load_profile(username):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT profile_text, updated_at FROM user_profiles WHERE username=?", (username,))
    result = c.fetchone()
    return result if result else ("", "")

def list_users():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT username FROM user_profiles ORDER BY username")
    return [row[0] for row in c.fetchall()]

# ----------------------
# DB操作（ユーザー情報）
# ----------------------
def get_user_profile(username):
    conn = get_conn()
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
# 自己プロフィール編集（Markdown対応）
# ----------------------
def render_self_profile_editor(user):
    st.header("🔹 自己プロフィール記述")
    current_text, updated = load_profile(user)
    
    st.caption(f"最終更新：{updated}" if updated else "まだプロフィールは未記入です")
    
    # Markdown対応テキストエリア
    new_text = st.text_area(
        "あなた自身の語りをここに書いてください（Markdown可）",
        value=current_text,
        height=200
    )
    
    # Markdownプレビュー
    st.subheader("プレビュー")
    st.markdown(new_text if new_text else "_プロフィールがここに表示されます_")
    
    if st.button("保存する", key="save_self_profile"):
        save_profile(user, new_text)
        st.success("プロフィールを保存しました")
        st.experimental_rerun()

# ----------------------
# プロフィール表示
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

    # 自己プロフィール
    st.markdown("---")
    st.subheader("📖 自己プロフィール")
    profile_text, updated = load_profile(target_user)
    if profile_text:
        st.caption(f"{target_user} さんの最終更新：{updated}")
        st.markdown(profile_text)  # Markdown表示
    else:
        st.info("プロフィールはまだ登録されていません")

    # 性格診断（グラフ表示）
    st.markdown("---")
    st.subheader("🧠 性格診断（Big Five）")
    personality = get_personality(target_user)
    st.bar_chart({k: [v] for k, v in personality.items()})

    # 関係性アクション
    current_user = get_current_user()
    if target_user != current_user:
        st.markdown("---")
        st.subheader("🤝 関係性アクション")
        key = f"friend_{target_user}"
        if key not in st.session_state:
            st.session_state[key] = False
        if st.button(f"{target_user} さんと友達になる", key=key):
            st.session_state[key] = True
            st.success("友達申請を送信しました（仮）")
        elif st.session_state[key]:
            st.info("友達申請済み（仮）")

# ----------------------
# メイン
# ----------------------
def render():
    init_profile_db()
    st.title("プロフィール管理アプリ")

    user = get_current_user()
    if not user:
        st.warning("ログインしてください")
        return

    # 自己プロフィール編集
    render_self_profile_editor(user)
    st.markdown("---")

    # プロフィール閲覧
    all_users = list_users()
    if user not in all_users:
        all_users.append(user)
    selected_user = st.selectbox("表示したいユーザーを選択", all_users)
    render_profile(selected_user)

if __name__ == "__main__":
    render()
