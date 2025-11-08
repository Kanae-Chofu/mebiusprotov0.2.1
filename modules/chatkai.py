# chatkai_newapi.py (絵文字自動対応＋リアクション・お気に入り版)
import streamlit as st
import sqlite3
import os
from streamlit_autorefresh import st_autorefresh
from modules.user import get_current_user, get_display_name, get_all_users
from modules.utils import now_str
from modules.feedback import init_feedback_db, save_feedback, get_feedback
from dotenv import load_dotenv
import emoji

load_dotenv()

# --- OpenAI 新APIクライアント ---
from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
AI_NAME = "AIアシスタント"

# --- 絵文字スタンプ（最大30個） ---
STAMPS = [e for e in emoji.EMOJI_DATA.keys() if e in "😀😂❤️👍😢🎉🔥🤔🥰😎🙌💀🌟🍕☕🛹🐶🐱🐭🐹🐰🦊🐻🐼🦁🐮🐷🐸"][:30]

# --- DB ---
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
        c.execute('''CREATE TABLE IF NOT EXISTS reactions (
            message_id INTEGER,
            reaction TEXT,
            PRIMARY KEY (message_id, reaction)
        )''')
        conn.commit()
    finally:
        conn.close()

def save_message(sender, receiver, message, message_type="text"):
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        c.execute(
            "INSERT INTO chat_messages (sender, receiver, message, timestamp, message_type) VALUES (?, ?, ?, ?, ?)",
            (sender, receiver, message, now_str(), message_type)
        )
        msg_id = c.lastrowid
        conn.commit()
        return msg_id
    finally:
        conn.close()

def add_reaction(message_id, reaction):
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO reactions (message_id, reaction) VALUES (?, ?)", (message_id, reaction))
        conn.commit()
    finally:
        conn.close()

def get_reactions(message_id):
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        c.execute("SELECT reaction FROM reactions WHERE message_id=?", (message_id,))
        return [r[0] for r in c.fetchall()]
    finally:
        conn.close()

def get_messages(user, partner):
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        c.execute('''SELECT id, sender, message, message_type FROM chat_messages
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

def remove_friend(user, friend):
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        c.execute("DELETE FROM friends WHERE user=? AND friend=?", (user, friend))
        conn.commit()
    finally:
        conn.close()

# --- スタンプ画像 ---
def get_stamp_images():
    stamp_dir = "stamps"
    if not os.path.exists(stamp_dir):
        os.makedirs(stamp_dir)
    return [os.path.join(stamp_dir, f) for f in os.listdir(stamp_dir) if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif"))]

# --- AI応答生成 ---
def generate_ai_response(user):
    messages = get_messages(user, AI_NAME)
    messages_for_ai = [{"role": "user", "content": msg} for _, _, msg, _ in messages[-5:]] or [{"role":"user","content":"こんにちは！"}]

    try:
        resp = client.chat.completions.create(
            model="gpt-5-nano",
            messages=[{"role":"system","content":"あなたは親切なチャットAIです。過去の会話も踏まえて自然に返答してください。"}] + messages_for_ai,
            max_tokens=150,
            temperature=0.7
        )
        content = getattr(resp.choices[0].message, "content", None)
        if content is None:
            return "AI応答でエラーが発生しました（message.contentが取得できません）"
        return content.strip()
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

    if 'chat_input_active' not in st.session_state:
        st.session_state.chat_input_active = False

    if not st.session_state.chat_input_active:
        st_autorefresh(interval=3000, limit=100, key="chat_refresh")

    # --- 友達追加 ---
    st.markdown("---")
    st.subheader("👥 友達を管理")
    users_list = get_all_users()
    new_friend = st.text_input("追加したいユーザー名", key="add_friend_input", max_chars=64)
    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("追加"):
            if new_friend == user:
                st.error("自分自身は追加できません")
            elif new_friend not in users_list:
                st.error("存在しないユーザーです")
            else:
                add_friend(user, new_friend)
                st.success(f"{new_friend} を追加しました")
                st.rerun()
    with col2:
        if st.button("削除"):
            remove_friend(user, new_friend)
            st.success(f"{new_friend} を削除しました")
            st.rerun()

    # --- チャット相手 ---
    friends = get_friends(user) + [AI_NAME]
    partner = st.selectbox("チャット相手を選択", friends)
    if not partner:
        return
    st.session_state.partner = partner
    display_name = AI_NAME if partner == AI_NAME else get_display_name(partner)
    st.write(f"チャット相手： `{display_name}`")

    # --- メッセージ履歴 ---
    st.markdown("---")
    st.subheader("📨 メッセージ履歴（自動更新）")
    messages = get_messages(user, partner)
    st.markdown("<div id='chat-box' style='height:400px; overflow-y:auto; border:1px solid #ccc; padding:10px; background-color:#f9f9f9;'>", unsafe_allow_html=True)
    for msg_id, sender, msg, msg_type in messages:
        align = "right" if sender == user else "left"
        bg = "#1F2F54" if align == "right" else "#426AB3"
        if msg_type == "stamp" and os.path.exists(msg):
            st.markdown(f"<div style='text-align:{align}; margin:10px 0;'><img src='{msg}' style='width:100px; border-radius:10px;'></div>", unsafe_allow_html=True)
        elif len(msg.strip()) <= 2 and all('\U0001F300' <= c <= '\U0001FAFF' or c in '❤️🔥🎉' for c in msg):
            st.markdown(f"<div style='text-align:{align}; margin:5px 0;'><span style='font-size:40px;'>{msg}</span></div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='text-align:{align}; margin:5px 0;'><span style='background-color:{bg}; color:#FFFFFF; padding:8px 12px; border-radius:10px; display:inline-block; max-width:80%;'>{msg}</span></div>", unsafe_allow_html=True)

        # --- リアクション表示 ---
        current_reacts = get_reactions(msg_id)
        if current_reacts:
            st.markdown(f"<div style='text-align:{align}; font-size:14px; color:#444;'>リアクション: {' '.join(current_reacts)}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<script>var chatBox = document.getElementById('chat-box'); chatBox.scrollTop = chatBox.scrollHeight;</script>", unsafe_allow_html=True)

    # --- メッセージ入力 ---
    st.markdown("---")
    st.markdown("### 💌 メッセージ入力")
    st.markdown("#### 🙂 テキストスタンプを送る（お気に入り＆リアクション対応）")

    if "favorites" not in st.session_state:
        st.session_state.favorites = []
    REACTIONS = ["👍","❤️","😂","😮","😢","🔥","🎉","🤔"]

    cols = st.columns(len(STAMPS))
    for i, stamp in enumerate(STAMPS):
        with cols[i]:
            col1, col2 = st.columns([2,1])
            with col1:
                if st.button(stamp, key=f"stamp_{stamp}"):
                    msg_id = save_message(user, partner, stamp)
                    if partner == AI_NAME:
                        ai_reply = generate_ai_response(user)
                        save_message(AI_NAME, user, ai_reply)
                    st.rerun()
            with col2:
                if st.button("★", key=f"fav_btn_{i}"):
                    if stamp not in st.session_state.favorites:
                        st.session_state.favorites.append(stamp)
                        st.success(f"{stamp} をお気に入りに追加")

        # --- リアクションボタン ---
        for r in REACTIONS:
            if st.button(r, key=f"react_{i}_{r}"):
                last_msg_id = get_messages(user, partner)[-1][0]  # 最新メッセージID
                add_reaction(last_msg_id, r)
                st.rerun()

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

    st.markdown("#### 📤 新しいスタンプを追加")
    uploaded = st.file_uploader("画像ファイルをアップロード (.png, .jpg, .gif)", type=["png", "jpg", "jpeg", "gif"])
    if uploaded:
        save_path = os.path.join("stamps", uploaded.name)
        with open(save_path, "wb") as f:
            f.write(uploaded.getbuffer())
        st.success(f"スタンプ {uploaded.name} を追加しました！")
        st.rerun()

    new_msg = st.chat_input("ここにメッセージを入力してください")
    st.session_state.chat_input_active = bool(new_msg)
    if new_msg:
        char_count = len(new_msg)
        st.caption(f"現在の文字数：{char_count} / 10000")
        if char_count <= 10000:
            save_message(user, partner, new_msg)
            if partner == AI_NAME:
                ai_reply = generate_ai_response(user)
                save_message(AI_NAME, user, ai_reply)
            st.rerun()
        else:
            st.warning("⚠️ メッセージは10,000字以内で入力してください")

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
