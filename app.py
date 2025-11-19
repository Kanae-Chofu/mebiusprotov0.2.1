import streamlit as st
import sqlite3
from modules.user import (
    login_user as login_user_func,
    register_user,
    get_current_user,
    init_user_db,
    update_display_name,
    update_kari_id,
    get_display_name,
    get_kari_id
)
from modules import board, karitunagari, chatkai, chatkai2
from modules.utils import now_str

# =====================================================
# 🔰 初期設定
# =====================================================
if "db_initialized" not in st.session_state:
    init_user_db()
    st.session_state.db_initialized = True

# ダークモードCSS
st.markdown("""
<style>
body, .stApp { background-color: #000000; color: #FFFFFF; }
div[data-testid="stHeader"] { background-color: #000000; }
div[data-testid="stToolbar"] { display: none; }
input, textarea { background-color: #1F2F54 !important; color:#FFFFFF !important; }
button { background-color: #426AB3 !important; color:#FFFFFF !important; border: none !important; }
</style>
""", unsafe_allow_html=True)

st.title("めびうす redesign")
st.caption("問いと沈黙から始まる、関係性の設計空間")

# =====================================================
# 🔐 ログイン処理
# =====================================================
user = get_current_user()

if user is None:
    st.subheader("🔐 ログイン")
    input_username = st.text_input("ユーザー名", key="login_username")
    input_password = st.text_input("パスワード", type="password", key="login_password")
    if st.button("ログイン", key="login_btn"):
        if login_user_func(input_username, input_password):
            st.success(f"ようこそ、{input_username} さん")
            st.rerun()
        else:
            st.error("ログイン失敗：ユーザー名またはパスワードが間違っています")

    st.subheader("🆕 新規登録")
    new_user = st.text_input("ユーザー名（新規）", key="register_username")
    new_pass = st.text_input("パスワード（新規）", type="password", key="register_password")
    if st.button("登録", key="register_btn"):
        result = register_user(new_user, new_pass)
        if result == "OK":
            st.success("登録完了！ログイン画面に戻ってください")
        else:
            st.error(f"登録失敗：{result}")
    st.stop()

# =====================================================
# 🪞 表示名・仮ID編集
# =====================================================
st.markdown("---")
show_editor = st.checkbox("🪞 表示名・仮IDを編集する", value=False, key="edit_checkbox")

if show_editor:
    st.subheader("🪞 あなたの関係性の見え方を編集")
    current_display = get_display_name(user)
    new_display = st.text_input("表示名（例：佳苗）", value=current_display, key="edit_display")
    if st.button("表示名を更新", key="update_display_btn"):
        update_display_name(user, new_display)
        st.success("表示名を更新しました")
        st.rerun()

    current_kari = get_kari_id(user)
    new_kari = st.text_input("仮ID（例：kari_1234）", value=current_kari, key="edit_kari")
    if st.button("仮IDを更新", key="update_kari_btn"):
        update_kari_id(user, new_kari)
        st.success("仮IDを更新しました")
        st.rerun()

# =====================================================
# 🚪 空間選択
# =====================================================
st.markdown("---")
st.subheader("🧭 空間を選んでください")
space = st.radio(
    "空間",
    ["掲示板", "仮つながりスペース", "1対1チャット", "プロフィール"],
    horizontal=True,
    key="space_radio"  # ←ユニークキーを追加
)

# =====================================================
# 🧩 各モードの描画
# =====================================================
if space == "掲示板":
    board.render()

elif space == "仮つながりスペース":
    karitunagari.render()

elif space == "1対1チャット":
    chatkai2.render()

elif space == "プロフィール":
    st.subheader("🧬 プロフィール画面")

    # ユーザープロフィール取得
    def get_user_profile(username):
        conn = sqlite3.connect("db/mebius.db")
        try:
            c = conn.cursor()
            c.execute(
                "SELECT display_name, kari_id, registered_at FROM users WHERE username=?",
                (username,)
            )
            result = c.fetchone()
            if result:
                return {
                    "display_name": result[0],
                    "kari_id": result[1],
                    "registered_at": result[2]
                }
            return None
        finally:
            conn.close()

    profile = get_user_profile(user)
    if profile:
        st.write(f"**表示名:** {profile['display_name']}")
        st.write(f"**仮ID:** {profile['kari_id']}")
        st.write(f"**登録日時:** {profile['registered_at']}")
    else:
        st.warning("プロフィール情報が見つかりません")
