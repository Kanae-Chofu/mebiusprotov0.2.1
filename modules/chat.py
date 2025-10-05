import streamlit as st
import sqlite3
import time
from modules.user import get_current_user, get_display_name
from modules.utils import now_str
from modules.feedback import (
    init_feedback_db,
    save_feedback,
    get_feedback,
    auto_feedback,
    question_feedback,
    silence_feedback,
    emotion_feedback,
    response_feedback,
    length_feedback,
    diversity_feedback,
    disclosure_feedback,
    continuity_feedback,
    continuity_duration_feedback
)

DB_PATH = "db/mebius.db"
MAX_NAME_LEN = 64
MAX_FEEDBACK_LEN = 150

# DB初期化
def init_chat_db():
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            receiver TEXT,
            message TEXT,
            timestamp TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS friends (
            user TEXT,
            friend TEXT,
            UNIQUE(user, friend)
        )''')
        conn.commit()
    finally:
        conn.close()

# メッセージ保存・取得
def save_message(sender, receiver, message):
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        c.execute("INSERT INTO chat_messages (sender, receiver, message, timestamp) VALUES (?, ?, ?, ?)",
                  (sender, receiver, message, now_str()))
        conn.commit()
    finally:
        conn.close()

def get_messages(user, partner):
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        c.execute('''SELECT sender, message FROM chat_messages
                     WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?)
                     ORDER BY timestamp''', (user, partner, partner, user))
        return c.fetchall()
    finally:
        conn.close()

# 友達管理
def get_friends(user):
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        c.execute("SELECT friend FROM friends WHERE user=?", (user,))
        return [row[0] for row in c.fetchall()]
    finally:
        conn.close()

def add_friend(user, friend):
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO friends (user, friend) VALUES (?, ?)", (user, friend))
        conn.commit()
    finally:
        conn.close()

# UI表示
def render():
    init_chat_db()
    init_feedback_db()

    user = get_current_user()
    if not user:
        st.warning("ログインしてください（共通ID）")
        return

    st.subheader("💬 1対1チャット空間")
    st.write(f"あなたの表示名： `{get_display_name(user)}`")

    # 友達追加
    st.markdown("---")
    st.subheader("👥 友達を追加する")
    new_friend = st.text_input("追加したいユーザー名", key="add_friend_input", max_chars=MAX_NAME_LEN)
    if st.button("追加"):
        if new_friend and new_friend != user:
            add_friend(user, new_friend)
            st.success(f"{new_friend} を追加しました")
            st.rerun()
        else:
            st.error("自分自身は追加できません")

    # チャット相手選択
    friends = get_friends(user)
    if not friends:
        st.info("まだ友達がいません。追加してください。")
        return

    partner = st.selectbox("チャット相手を選択", friends)
    if partner:
        st.session_state.partner = partner
        st.write(f"チャット相手： `{get_display_name(partner)}`")

        # メッセージ表示（毎秒更新）
        st.markdown("---")
        st.subheader("📨 メッセージ履歴（自動更新）")
        message_container = st.empty()
        for _ in range(1):  # 初回のみ描画（無限ループは避ける）
            with message_container:
                messages = get_messages(user, partner)
                for sender, msg in messages:
                    align = "right" if sender == user else "left"
                    bg = "#1F2F54" if align == "right" else "#426AB3"
                    st.markdown(
                        f"""<div style='text-align:{align}; margin:5px 0;'>
                        <span style='background-color:{bg}; color:#FFFFFF; padding:8px 12px; border-radius:10px; display:inline-block; max-width:80%;'>
                        {msg}
                        </span></div>""", unsafe_allow_html=True
                    )
            time.sleep(1)
            st.rerun()

        # メッセージ入力
        new_msg = st.chat_input("メッセージを入力")
        if new_msg:
            save_message(user, partner, new_msg)
            st.rerun()

        # AIフィードバック（設計順に並べる）
        st.markdown("---")
        st.markdown("### 🤖 AIフィードバック")
        st.write("・会話の長さ：" + length_feedback(user, partner))
        st.write("・会話の連続性：" + continuity_feedback(user, partner))
        st.write("・沈黙の余白：" + silence_feedback(user, partner))
        st.write("・応答率：" + response_feedback(user, partner))
        st.write("・発言割合：" + auto_feedback(user, partner))
        st.write("・問いの頻度：" + question_feedback(user, partner))
        st.write("・感情語の使用：" + emotion_feedback(user, partner))
        st.write("・自己開示度：" + disclosure_feedback(user, partner))
        st.write("・話題の広がり：" + diversity_feedback(user, partner))
        st.write("・関係性の継続性：" + continuity_duration_feedback(user, partner))

        # 手動フィードバック入力
        st.markdown("---")
        st.markdown("### 📝 あなたのフィードバック")
        st.write("この会話を振り返って、どんなことを感じましたか？問いでも、感想でも、ひとことでもOKです。")
        feedback_text = st.text_input("フィードバックを入力", key="feedback_input", max_chars=MAX_FEEDBACK_LEN)
        if st.button("送信"):
            if feedback_text:
                save_feedback(user, partner, feedback_text)
                st.success("フィードバックを保存しました")
                st.rerun()
            else:
                st.warning("フィードバックを入力してください")

        # 過去のフィードバック履歴
        st.markdown("---")
        st.markdown("### 🕊 過去のフィードバックを振り返る")
        feedback_list = get_feedback(user, partner)
        if feedback_list:
            options = [f"{ts}｜{fb}" for fb, ts in feedback_list]
            selected = st.selectbox("表示したいフィードバックを選んでください", options)
            st.write(f"選択されたフィードバック：{selected}")
        else:
            st.write("まだフィードバックはありません。")