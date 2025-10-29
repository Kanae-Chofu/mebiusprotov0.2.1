import streamlit as st
import sqlite3
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
import os

# 🧭 ユーザー管理モジュールの読み込み
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
from modules import board, karitunagari, chat
from modules import chatkai

from modules.utils import now_str

# =====================================================
# 🔰 初期設定
# =====================================================

# DB初期化
if "db_initialized" not in st.session_state:
    init_user_db()
    st.session_state.db_initialized = True

# 🌙 ダークモードCSS
st.markdown("""
<style>
body, .stApp { background-color: #000000; color: #FFFFFF; }
div[data-testid="stHeader"] { background-color: #000000; }
div[data-testid="stToolbar"] { display: none; }
input, textarea { background-color: #1F2F54 !important; color:#FFFFFF !important; }
button { background-color: #426AB3 !important; color:#FFFFFF !important; border: none !important; }
</style>
""", unsafe_allow_html=True)

# タイトル
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

# =====================================================
# 🪞 表示名・仮ID編集
# =====================================================
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

# =====================================================
# ☁️ Googleアカウントバックアップ機能
# =====================================================
st.markdown("---")
st.subheader("☁️ Googleアカウントでバックアップ / 復元")

# クライアントシークレットファイルの設定
CLIENT_SECRETS_FILE = "client_secret.json"  # Google CloudからDLしたJSON
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

def google_auth():
    """OAuth認証フローを開始"""
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri="http://localhost:8501"
    )
    auth_url, _ = flow.authorization_url(prompt="consent")
    st.markdown(f"[Googleで認証する]({auth_url})")

if not os.path.exists(CLIENT_SECRETS_FILE):
    st.warning("⚠️ Google連携を使うには client_secret.json が必要です")
else:
    if st.button("🔐 Google連携でバックアップする"):
        display = get_display_name(user)
        kari = get_kari_id(user)
        backup_data = {
            "display_name": display,
            "kari_id": kari,
            "username": user,
            "timestamp": now_str()
        }
        with open(f"{user}_backup.json", "w", encoding="utf-8") as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        st.success("✅ バックアップデータを生成しました（Driveアップロード準備OK）")

    if st.button("🔁 Google連携で復元する"):
        try:
            with open(f"{user}_backup.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            update_display_name(user, data["display_name"])
            update_kari_id(user, data["kari_id"])
            st.success(f"✅ 表示名と仮IDを復元しました（{data['timestamp']}のバックアップ）")
            st.rerun()
        except FileNotFoundError:
            st.error("バックアップファイルが見つかりません")

# =====================================================
# 🚪 空間選択
# =====================================================
st.markdown("---")
st.subheader("🧭 空間を選んでください")
space = st.radio("空間", ["掲示板", "仮つながりスペース", "1対1チャット", "プロフィール", "自分のプロフィールを書く"], horizontal=True)

# =====================================================
# 🧩 各モードの描画
# =====================================================
if space == "掲示板":
    board.render()

elif space == "仮つながりスペース":
    karitunagari.render()

elif space == "1対1チャット":
    chatkai.render()

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

elif space == "自分のプロフィールを書く":
    st.subheader("📝 自分で書くプロフィール")

    def init_profile_db():
        conn = sqlite3.connect("db/mebius.db")
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
        conn = sqlite3.connect("db/mebius.db")
        try:
            c = conn.cursor()
            c.execute("REPLACE INTO user_profiles (username, profile_text, updated_at) VALUES (?, ?, ?)",
                      (username, text, now_str()))
            conn.commit()
        finally:
            conn.close()

    def load_profile(username):
        conn = sqlite3.connect("db/mebius.db")
        try:
            c = conn.cursor()
            c.execute("SELECT profile_text, updated_at FROM user_profiles WHERE username=?", (username,))
            result = c.fetchone()
            return result if result else ("", "")
        finally:
            conn.close()

    init_profile_db()
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
