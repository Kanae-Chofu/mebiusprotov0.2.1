import streamlit as st
import sqlite3
from modules.user import get_display_name, get_kari_id, get_current_user
from modules.utils import to_jst

DB_PATH = "db/mebius.db"

# ユーザー情報取得
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

# 性格診断結果取得（仮）
def get_personality(username):
    # 仮データ：将来的にはDBから取得
    return {
        "外向性": 3.8,
        "協調性": 4.2,
        "誠実性": 3.5,
        "神経症傾向": 2.1,
        "開放性": 4.7
    }

# UI表示
def render_profile(target_user):
    profile = get_user_profile(target_user)
    if not profile:
        st.error("ユーザー情報が見つかりません")
        return

    st.title("🧬 プロフィール画面")
    st.markdown(f"**表示名：** `{profile['display_name']}`")
    st.markdown(f"**仮ID：** `{profile['kari_id']}`")
    st.markdown(f"**登録日：** `{profile['registered_at']}`")

    st.markdown("---")
    st.subheader("🧠 性格診断（Big Five）")
    personality = get_personality(target_user)
    for trait, score in personality.items():
        st.write(f"・{trait}：{score} / 5")

    st.markdown("---")
    st.subheader("🤝 関係性アクション")
    current_user = get_current_user()
    if current_user and current_user != target_user:
        if st.button("このユーザーと友達になる"):
            st.success("友達申請を送信しました（仮）")
    else:
        st.info("これはあなた自身のプロフィールです")

# メイン
if __name__ == "__main__":
    # 仮：表示対象ユーザー名（将来的にはURLパラメータやセッションで切り替え）
    target_user = st.text_input("表示したいユーザー名を入力", key="target_user_input")
    if target_user:
        render_profile(target_user)