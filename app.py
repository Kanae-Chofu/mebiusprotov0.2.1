import streamlit as st
import sqlite3

# 🧭 ユーザー管理モジュールの読み込みと初期化
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

# 初回のみDB初期化（セッションステートで制御）
if "db_initialized" not in st.session_state:
    init_user_db()
    st.session_state.db_initialized = True

# 🧩 空間モジュールの読み込み
from modules import board, karitunagari, chat

# 🌙 ダークモードCSS（共通）
st.markdown("""
<style>
body, .stApp { background-color: #000000; color: #FFFFFF; }
div[data-testid="stHeader"] { background-color: #000000; }
div[data-testid="stToolbar"] { display: none; }
input, textarea { background-color: #1F2F54 !important; color:#FFFFFF !important; }
button { background-color: #426AB3 !important; color:#FFFFFF !important; border: none !important; }
</style>
""", unsafe_allow_html=True)

# 🧭 タイトルとログインチェック
st.title("めびうす redesign")
st.caption("問いと沈黙から始まる、関係性の設計空間")

user = get_current_user()

# 🔐 ログイン画面（未ログイン時のみ表示）
if user is None:
    st.subheader("🔐 ログイン")
    input_username = st.text_input("ユーザー名", key="login_username")
    input_password = st.text_input("パスワード", type="password", key="login_password")
    if st.button("ログイン"):
        if login_user_func(input_username, input_password):
            st.success(f"ようこそ、{input_username} さん")
            st.rerun()
        else:
            st.error("ログイン失敗：ユーザー名またはパスワードが間違っています")

    st.subheader("🆕 新規登録")
    new_user = st.text_input("ユーザー名（新規）", key="register_username")
    new_pass = st.text_input("パスワード（新規）", type="password", key="register_password")
    if st.button("登録"):
        result = register_user(new_user, new_pass)
        if result == "OK":
            st.success("登録完了！ログイン画面に戻ってください")
        else:
            st.error(f"登録失敗：{result}")
    st.stop()

# 🪞 表示名・仮ID編集（ログイン後・表示切り替え可能）
st.markdown("---")
show_editor = st.checkbox("🪞 表示名・仮IDを編集する", value=False)

if show_editor:
    st.subheader("🪞 あなたの関係性の見え方を編集")

    current_display = get_display_name(user)
    new_display = st.text_input("表示名（例：佳苗）", value=current_display, key="edit_display")
    if st.button("表示名を更新"):
        update_display_name(user, new_display)
        st.success("表示名を更新しました")
        st.rerun()

    current_kari = get_kari_id(user)
    new_kari = st.text_input("仮ID（例：kari_1234）", value=current_kari, key="edit_kari")
    if st.button("仮IDを更新"):
        update_kari_id(user, new_kari)
        st.success("仮IDを更新しました")
        st.rerun()

# 🚪 空間選択とルーティング
st.markdown("---")
st.subheader("🧭 空間を選んでください")
space = st.radio("空間", ["掲示板", "仮つながりスペース", "1対1チャット", "プロフィール"], horizontal=True)

if space == "掲示板":
    board.render()
elif space == "仮つながりスペース":
    karitunagari.render()
elif space == "1対1チャット":
    chat.render()
elif space == "プロフィール":
    st.subheader("🧬 プロフィール画面")

    def get_user_profile(username):
        conn = sqlite3.connect("db/mebius.db")
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
                    "registered_at": registered_at
                }
        finally:
            conn.close()
        return None

    def get_personality(username):
        # 仮データ：将来的にはDBから取得
        return {
            "外向性": 3.8,
            "協調性": 4.2,
            "誠実性": 3.5,
            "神経症傾向": 2.1,
            "開放性": 4.7
        }

    target_user = st.text_input("表示したいユーザー名を入力", key="target_user_input")
    if target_user:
        profile = get_user_profile(target_user)
        if profile:
            st.markdown(f"**表示名：** `{profile['display_name']}`")
            st.markdown(f"**仮ID：** `{profile['kari_id']}`")
            st.markdown(f"**登録日：** `{profile['registered_at']}`")

            st.markdown("---")
            st.subheader("🧠 性格診断（Big Five）")
            personality = get_personality(target_user)
            for trait, score in personality.items():
                st.write(f"・{trait}：{score} / 5")

            st.markdown("---")
            if user != target_user:
                if st.button("このユーザーと友達になる"):
                    st.success("友達申請を送信しました（仮）")
            else:
                st.info("これはあなた自身のプロフィールです")
        else:
            st.error("ユーザー情報が見つかりません")