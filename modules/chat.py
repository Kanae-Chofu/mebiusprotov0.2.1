import streamlit as st
import sqlite3
import os
import openai
from streamlit_autorefresh import st_autorefresh
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

from dotenv import load_dotenv  # ← これを追加！
load_dotenv()  # ← これが重要！

# --- OpenAI APIキー設定 ---
openai.api_key = os.getenv("OPENAI_API_KEY")
AI_NAME = "AIアシスタント"

# --- スタンプ定義 ---
STAMPS = ["😀", "😂", "❤️", "👍", "😢", "🎉", "🔥", "🤔"]

# --- データベース ---
DB_PATH = "db/mebius.db"

def init_chat_db():
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            receiver TEXT,
            message TEXT,
            timestamp TEXT,
            message_type TEXT DEFAULT 'text'
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS friends (
            user TEXT,
            friend TEXT,
            UNIQUE(user, friend)
        )''')
        conn.commit()
    finally:
        conn.close()

def save_message(sender, receiver, message, message_type="text"):
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        c.execute("INSERT INTO chat_messages (sender, receiver, message, timestamp, message_type) VALUES (?, ?, ?, ?, ?)",
                  (sender, receiver, message, now_str(), message_type))
        conn.commit()
    finally:
        conn.close()

def get_messages(user, partner):
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        c.execute('''SELECT sender, message, message_type FROM chat_messages
                     WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?)
                     ORDER BY timestamp''', (user, partner, partner, user))
        return c.fetchall()
    finally:
        conn.close()

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

# --- スタンプ関連 ---
def get_stamp_images():
    """stampsフォルダ内のスタンプ画像一覧を取得"""
    stamp_dir = "stamps"
    if not os.path.exists(stamp_dir):
        os.makedirs(stamp_dir)
    files = [f for f in os.listdir(stamp_dir) if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif"))]
    return [os.path.join(stamp_dir, f) for f in files]

# ファイル先頭付近で（既に openai.api_key を使っているなら不要）
from openai import OpenAI
# 環境変数 OPENAI_API_KEY がセットされている想定
client = OpenAI()  # 必要なら OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_ai_response(user):
    messages = get_messages(user, AI_NAME)
    last_msg = messages[-1][1] if messages else "こんにちは！"
    prompt = f"あなたは親切なチャットAIです。ユーザーの発言に対して自然に返答してください。\n\nユーザー: {last_msg}\nAI:"

    try:
        resp = client.chat.completions.create(
            model="gpt-5-nano",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.7
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"AI応答でエラーが発生しました: {e}"


# --- メインUI ---
def render():
    init_chat_db()
    init_feedback_db()

    user = get_current_user()
    if not user:
        st.warning("ログインしてください（共通ID）")
        return

    st.subheader("💬 1対1チャット空間")
    st.write(f"あなたの表示名： `{get_display_name(user)}`")

    st_autorefresh(interval=3000, limit=100, key="chat_refresh")

    # --- 友達追加 ---
    st.markdown("---")
    st.subheader("👥 友達を追加する")
    new_friend = st.text_input("追加したいユーザー名", key="add_friend_input", max_chars=64)
    if st.button("追加"):
        if new_friend and new_friend != user:
            add_friend(user, new_friend)
            st.success(f"{new_friend} を追加しました")
            st.rerun()
        else:
            st.error("自分自身は追加できません")

    # --- チャット相手 ---
    friends = get_friends(user) + [AI_NAME]
    partner = st.selectbox("チャット相手を選択", friends)
    if not partner:
        return

    st.session_state.partner = partner
    st.write(f"チャット相手： `{get_display_name(partner) if partner != AI_NAME else AI_NAME}`")

    # --- メッセージ履歴 ---
    st.markdown("---")
    st.subheader("📨 メッセージ履歴（自動更新）")

    messages = get_messages(user, partner)
    st.markdown("<div style='height:400px; overflow-y:auto; border:1px solid #ccc; padding:10px; background-color:#f9f9f9;'>", unsafe_allow_html=True)
    for sender, msg, msg_type in messages:
        align = "right" if sender == user else "left"
        bg = "#1F2F54" if align == "right" else "#426AB3"

        if msg_type == "stamp" and os.path.exists(msg):
            st.markdown(
                f"<div style='text-align:{align}; margin:10px 0;'>"
                f"<img src='{msg}' style='width:100px; border-radius:10px;'>"
                f"</div>", unsafe_allow_html=True
            )
        elif len(msg.strip()) <= 2 and all('\U0001F300' <= c <= '\U0001FAFF' or c in '❤️🔥🎉' for c in msg):
            st.markdown(
                f"<div style='text-align:{align}; margin:5px 0;'>"
                f"<span style='font-size:40px;'>{msg}</span></div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"<div style='text-align:{align}; margin:5px 0;'>"
                f"<span style='background-color:{bg}; color:#FFFFFF; padding:8px 12px; border-radius:10px; display:inline-block; max-width:80%;'>"
                f"{msg}</span></div>",
                unsafe_allow_html=True
            )
    st.markdown("</div>", unsafe_allow_html=True)

    # --- メッセージ入力 ---
    st.markdown("---")
    st.markdown("### 💌 メッセージ入力")

    # 絵文字スタンプ
    st.markdown("#### 🙂 テキストスタンプを送る")
    cols = st.columns(len(STAMPS))
    for i, stamp in enumerate(STAMPS):
        if cols[i].button(stamp, key=f"stamp_{stamp}"):
            save_message(user, partner, stamp)
            if partner == AI_NAME:
                ai_reply = generate_ai_response(user)
                save_message(AI_NAME, user, ai_reply)
            st.rerun()

    # 画像スタンプ
    st.markdown("#### 🖼 画像スタンプを送る")
    stamp_images = get_stamp_images()
    if stamp_images:
        cols = st.columns(5)
        for i, img_path in enumerate(stamp_images):
            with cols[i % 5]:
                st.image(img_path, width=60)
                if st.button("送信", key=f"send_{i}"):
                    save_message(user, partner, img_path, message_type="stamp")
                    if partner == AI_NAME:
                        ai_reply = generate_ai_response(user)
                        save_message(AI_NAME, user, ai_reply)
                    st.rerun()
    else:
        st.info("スタンプ画像がまだありません。`/stamps/` フォルダに画像を追加してください。")

    # --- スタンプアップロード機能 ---
    st.markdown("#### 📤 新しいスタンプを追加")
    uploaded = st.file_uploader("画像ファイルをアップロード (.png, .jpg, .gif)", type=["png", "jpg", "jpeg", "gif"])
    if uploaded:
        save_path = os.path.join("stamps", uploaded.name)
        with open(save_path, "wb") as f:
            f.write(uploaded.getbuffer())
        st.success(f"スタンプ {uploaded.name} を追加しました！")
        st.rerun()

    # --- 通常メッセージ ---
    new_msg = st.chat_input("ここにメッセージを入力してください")
    if new_msg:
        char_count = len(new_msg)
        st.caption(f"現在の文字数：{char_count} / 10000")
        if char_count > 10000:
            st.warning("⚠️ メッセージは10,000字以内で入力してください")
        else:
            save_message(user, partner, new_msg)
            if partner == AI_NAME:
                ai_reply = generate_ai_response(user)
                save_message(AI_NAME, user, ai_reply)
            st.rerun()

    # --- AIフィードバック ---
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

    # --- 手動フィードバック ---
    st.markdown("---")
    st.markdown("### 📝 あなたのフィードバック")
    feedback_text = st.text_input("フィードバックを入力", key="feedback_input", max_chars=150)
    if st.button("送信"):
        if feedback_text:
            save_feedback(user, partner, feedback_text)
            st.success("フィードバックを保存しました")
            st.rerun()
        else:
            st.warning("フィードバックを入力してください")

    # --- 過去のフィードバック ---
    st.markdown("---")
    st.markdown("### 🕊 過去のフィードバックを振り返る")
    feedback_list = get_feedback(user, partner)
    if feedback_list:
        options = [f"{ts}｜{fb}" for fb, ts in feedback_list]
        selected = st.selectbox("表示したいフィードバックを選んでください", options)
        st.write(f"選択されたフィードバック：{selected}")
    else:
        st.write("まだフィードバックはありません。")


# --- Streamlit実行 ---
if __name__ == "__main__":
    render()
