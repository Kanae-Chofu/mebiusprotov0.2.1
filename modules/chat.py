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

# --- OpenAI APIキー設定 ---
openai.api_key = os.getenv("OPENAI_API_KEY")
AI_NAME = "AIアシスタント"

# -----------------------
# AI応答
# -----------------------
def generate_ai_response(user, partner):
    """GPTを使って最新ユーザーメッセージに応答"""
    # ユーザーの直近メッセージを取得
    messages = get_messages(user, AI_NAME)
    last_msg = messages[-1][1] if messages else "こんにちは！"

    prompt = f"あなたは親切なチャットAIです。ユーザーの発言に対して自然に返答してください。\n\nユーザー: {last_msg}\nAI:"
    
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.7
        )
        reply = resp.choices[0].message.content.strip()
        return reply
    except Exception as e:
        return f"AI応答でエラーが発生しました: {e}"

# -----------------------
# メッセージ保存
# -----------------------
def save_message(sender, receiver, message):
    conn = sqlite3.connect("db/mebius.db")
    try:
        c = conn.cursor()
        c.execute("INSERT INTO chat_messages (sender, receiver, message, timestamp) VALUES (?, ?, ?, ?)",
                  (sender, receiver, message, now_str()))
        conn.commit()
    finally:
        conn.close()

def get_messages(user, partner):
    conn = sqlite3.connect("db/mebius.db")
    try:
        c = conn.cursor()
        c.execute('''SELECT sender, message FROM chat_messages
                     WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?)
                     ORDER BY timestamp''', (user, partner, partner, user))
        return c.fetchall()
    finally:
        conn.close()

# -----------------------
# Streamlit UI
# -----------------------
def render_chat():
    user = get_current_user()
    if not user:
        st.warning("ログインしてください（共通ID）")
        return

    st.subheader(f"💬 1対1チャット空間（あなた: {get_display_name(user)}）")

    # 自動更新
    st_autorefresh(interval=3000, limit=100, key="chat_refresh")

    # チャット相手選択
    partner = st.selectbox("チャット相手を選択", [AI_NAME])  # AI専用版
    st.write(f"チャット相手： `{partner}`")

    # メッセージ履歴表示
    st.markdown("---")
    st.subheader("📨 メッセージ履歴（自動更新）")
    messages = get_messages(user, partner)
    st.markdown("<div style='height:400px; overflow-y:auto; border:1px solid #ccc; padding:10px; background-color:#f9f9f9;'>", unsafe_allow_html=True)
    for sender, msg in messages:
        align = "right" if sender == user else "left"
        bg = "#1F2F54" if align == "right" else "#426AB3"
        st.markdown(
            f"<div style='text-align:{align}; margin:5px 0;'>"
            f"<span style='background-color:{bg}; color:#FFFFFF; padding:8px 12px; border-radius:10px; display:inline-block; max-width:80%;'>"
            f"{msg}"
            f"</span></div>", unsafe_allow_html=True
        )
    st.markdown("</div>", unsafe_allow_html=True)

    # メッセージ入力
    st.markdown("---")
    new_msg = st.chat_input("ここにメッセージを入力")
    if new_msg:
        save_message(user, partner, new_msg)
        # AI応答生成
        ai_reply = generate_ai_response(user, partner)
        save_message(AI_NAME, user, ai_reply)
        st.rerun()

    # AIフィードバック表示
    st.markdown("---")
    st.subheader("🤖 AIフィードバック")
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
