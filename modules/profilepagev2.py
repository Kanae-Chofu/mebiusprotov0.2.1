import streamlit as st
from PIL import Image
from modules.user import get_current_user  # ← ここでログイン中のユーザー名を取得

def render():
    st.title("プロフィール画面")

    current_user = get_current_user()
    if not current_user:
        st.warning("ログインしてください")
        return

    # --- 初期ユーザー情報 ---
    if "users" not in st.session_state:
        st.session_state.users = {}

    # --- ユーザーが未登録なら初期化 ---
    if current_user not in st.session_state.users:
        st.session_state.users[current_user] = {
            "handle": current_user,  # ← ハンドルネームはユーザー名と一致
            "bio": "",
            "image": None,
            "posts": []
        }

    profile = st.session_state.users[current_user]

    # --- プロフィール設定 ---
    st.markdown("### プロフィール設定")
    uploaded_image = st.file_uploader("プロフィール画像をアップロード", type=["png", "jpg", "jpeg"])
    if uploaded_image:
        profile["image"] = Image.open(uploaded_image)

    # ハンドルネームは固定（表示のみ）
    profile["handle"] = current_user
    st.text(f"ハンドルネーム： {profile['handle']}")

    profile["bio"] = st.text_area("自己紹介", profile.get("bio", ""))

    # --- プロフィール表示 ---
    st.markdown("### プロフィール")
    if profile.get("image"):
        st.image(profile["image"], width=150)
    else:
        st.text("プロフィール画像なし")

    st.subheader(current_user)
    st.text(f"ハンドルネーム： {profile.get('handle', '')}")
    st.write(profile.get("bio", ""))

    st.write("---")

    # --- 投稿 ---
    st.markdown("### 投稿する")
    new_post = st.text_area("新しい投稿を入力", "")
    if st.button("投稿"):
        if new_post.strip():
            profile["posts"].insert(0, new_post)
            st.success("投稿しました！")
        else:
            st.warning("投稿内容が空です。")

    # --- 投稿表示 ---
    st.markdown("### 最近の投稿")
    if profile.get("posts"):
        for post in profile["posts"]:
            st.write(f"💬 {post}")
    else:
        st.write("まだ投稿はありません。")