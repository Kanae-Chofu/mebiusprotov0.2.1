# chatkai_newapi_refactored.py
import streamlit as st
import sqlite3, os, time
from contextlib import contextmanager
from dotenv import load_dotenv
from streamlit_autorefresh import st_autorefresh
from modules.user import get_current_user, get_display_name, get_all_users
from modules.utils import now_str
from modules.feedback import init_feedback_db, save_feedback, get_feedback
from openai import OpenAI
import emoji

load_dotenv()
AI_NAME = "AIアシスタント"
STAMPS = ["😀", "😂", "❤️", "👍", "😢", "🎉", "🔥", "🤔"]
DB_PATH = "db/mebius.db"

# --- OpenAI 新APIクライアント ---
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- DB 共通処理 ---
@contextmanager
def db_cursor():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn.cursor()
        conn.commit()
    finally:
        conn.close()

def init_chat_db():
    with db_cursor() as c:
        c.execute('''CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT, receiver TEXT, message TEXT,
            timestamp TEXT, message_type TEXT DEFAULT 'text'
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS friends (
            user TEXT, friend TEXT, UNIQUE(user, friend)
        )''')

def save_message(sender, receiver, message, message_type="text"):
    with db_cursor() as c:
        c.execute(
            "INSERT INTO chat_messages (sender, receiver, message, timestamp, message_type) VALUES (?, ?, ?, ?, ?)",
            (sender, receiver, message, now_str(), message_type)
        )

def get_messages(user, partner):
    with db_cursor() as c:
        c.execute('''SELECT sender, message, message_type FROM chat_messages
                     WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?)
                     ORDER BY timestamp''', (user, partner, partner, user))
        return c.fetchall()

def get_friends(user):
    with db_cursor() as c:
        c.execute("SELECT friend FROM friends WHERE user=?", (user,))
        return [row[0] for row in c.fetchall()]

def add_friend(user, friend):
    with db_cursor() as c:
        c.execute("INSERT OR IGNORE INTO friends (user, friend) VALUES (?, ?)", (user, friend))

def remove_friend(user, friend):
    with db_cursor() as c:
        c.execute("DELETE FROM friends WHERE user=? AND friend=?", (user, friend))

# --- スタンプ画像 ---
def get_stamp_images():
    stamp_dir = "stamps"
    if not os.path.exists(stamp_dir):
        os.makedirs(stamp_dir)
    return [os.path.join(stamp_dir, f) for f in os.listdir(stamp_dir) if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif"))]

# --- AI応答 ---
def generate_ai_response(user, retries=2):
    messages = get_messages(user, AI_NAME)
    messages_for_ai = [{"role": "user", "content": msg} for _, msg, _ in messages[-5:]] or [{"role":"user","content":"こんにちは！"}]

    system_msg = {"role":"system","content":"あなたは親切なチャットAIです。過去の会話も踏まえて自然に返答してください。"}
    
    for attempt in range(retries):
        try:
            resp = client.chat.completions.create(
                model="gpt-5-nano",
                messages=[system_msg] + messages_for_ai,
                max_tokens=150,
                temperature=0.7
            )
            content = getattr(resp.choices[0].message, "content", None)
            if content:
                return content.strip()
            return "AI応答でエラー: 応答内容がありません"
        except Exception as e:
            if attempt == retries - 1:
                return f"AI応答でエラーが発生しました: {e}"
            time.sleep(1)  # リトライの間隔

# --- Streamlit UI ---
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

    # --- 友達管理 ---
    st.markdown("---")
    st.subheader("👥 友達を管理")
    users_list = get_all_users()
    new_friend = st.text_input("追加したいユーザー名", key="add_friend_input", max_chars=64)
    col1, col2 = st.columns(2)
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

    # --- チャット相手選択 ---
    friends = get_friends(user) + [AI_NAME]
    partner = st.selectbox("チャット相手を選択", friends)
    if not partner:
        return
    st.session_state.partner = partner
    display_name = AI_NAME if partner == AI_NAME else get_display_name(partner)
    st.write(f"チャット相手： `{display_name}`")

    # --- メッセージ表示 ---
    st.markdown("---")
    st.subheader("📨 メッセージ履歴")
    messages = get_messages(user, partner)
    chat_box = st.container()
    with chat_box:
        for sender, msg, msg_type in messages:
            align = "right" if sender == user else "left"
            bg = "#1F2F54" if align == "right" else "#426AB3"
            if msg_type == "stamp" and os.path.exists(msg):
                st.markdown(f"<div style='text-align:{align}; margin:10px 0;'><img src='{msg}' style='width:100px; border-radius:10px;'></div>", unsafe_allow_html=True)
            elif all(emoji.is_emoji(c) or c in '❤️🔥🎉' for c in msg):
                st.markdown(f"<div style='text-align:{align}; margin:5px 0;'><span style='font-size:40px;'>{msg}</span></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='text-align:{align}; margin:5px 0;'><span style='background-color:{bg}; color:#FFF; padding:8px 12px; border-radius:10px; display:inline-block; max-width:80%;'>{msg}</span></div>", unsafe_allow_html=True)

    # --- スタンプ送信 ---
    st.markdown("---")
    st.markdown("### 💌 メッセージ入力")
    st.markdown("#### 🙂 テキストスタンプ")
    cols = st.columns(len(STAMPS))
    for i, stamp in enumerate(STAMPS):
        if cols[i].button(stamp, key=f"stamp_{stamp}"):
            save_message(user, partner, stamp)
            if partner == AI_NAME:
                ai_reply = generate_ai_response(user)
                save_message(AI_NAME, user, ai_reply)
            st.rerun()

    # --- 画像スタンプ送信 ---
    st.markdown("#### 🖼 画像スタンプ")
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
        st.info("スタンプ画像がまだありません。`/stamps/` フォルダに追加してください。")

    # --- 新スタンプアップロード ---
    st.markdown("#### 📤 新しいスタンプ追加")
    uploaded = st.file_uploader("画像ファイルをアップロード (.png, .jpg, .gif)", type=["png", "jpg", "jpeg", "gif"])
    if uploaded:
        filename = os.path.basename(uploaded.name)
        save_path = os.path.join("stamps", f"{int(time.time())}_{filename}")
        with open(save_path, "wb") as f:
            f.write(uploaded.getbuffer())
        st.success(f"スタンプ {filename} を追加しました！")
        st.rerun()

    # --- テキスト入力 ---
    new_msg = st.chat_input("ここにメッセージを入力してください")
    st.session_state.chat_input_active = bool(new_msg)
    if new_msg:
        if len(new_msg) <= 10000:
            save_message(user, partner, new_msg)
            if partner == AI_NAME:
                ai_reply = generate_ai_response(user)
                save_message(AI_NAME, user, ai_reply)
            st.rerun()
        else:
            st.warning("⚠️ メッセージは10,000字以内で入力してください")

    # --- フィードバック ---
    st.markdown("---")
    st.markdown("### 📝 フィードバック")
    feedback_text = st.text_input("入力", key="feedback_input", max_chars=150)
    if st.button("送信フィードバック"):
        if feedback_text:
            save_feedback(user, partner, feedback_text)
            st.success("保存しました")
            st.rerun()
        else:
            st.warning("入力してください")

    # --- 過去フィードバック ---
    st.markdown("---")
    st.markdown("### 🕊 過去のフィードバック")
    feedback_list = get_feedback(user, partner)
    if feedback_list:
        options = [f"{ts}｜{fb}" for fb, ts in feedback_list]
        selected = st.selectbox("表示", options)
        st.write(f"選択されたフィードバック：{selected}")
    else:
        st.write("まだありません")

# --- Streamlit実行 ---
if __name__ == "__main__":
    render()
