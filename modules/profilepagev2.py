import streamlit as st
from PIL import Image

def render(current_user):
    st.title("プロフィール画面")

    # --- 初期ユーザー情報 ---
    if "users" not in st.session_state:
        st.session_state.users = {
            "admin": {
                "handle": "@admin",
                "bio": "こんにちは！Streamlitでプロフィール画面を作っています。",
                "followers": 123,
                "following": 45,
                "image": None,
                "posts": []
            },
            "kanae": {
                "handle": "@kanae",
                "bio": "物語構造と三国志に夢中な大学生です。",
                "followers": 321,
                "following": 88,
                "image": None,
                "posts": ["三国志の語り直し、今夜も進行中。"]
            },
            "すする": {
                "handle": "@susuru",
                "bio": "ラーメンが好き。中学三年生。",
                "followers": 321,
                "following": 88,
                "image": None,
                "posts": ["あなたの好きなラーメンは？"]
            }
        }

    # --- 表示するユーザー選択 ---
    selected_user = st.sidebar.selectbox("表示するユーザー", list(st.session_state.users.keys()))
    profile = st.session_state.users[selected_user]
    is_own_profile = (selected_user == current_user)

    # --- 編集UI（自分のみ） ---
    if is_own_profile:
        st.sidebar.title("プロフィール設定")
        uploaded_image = st.sidebar.file_uploader("プロフィール画像をアップロード", type=["png", "jpg", "jpeg"])
        if uploaded_image:
            profile["image"] = Image.open(uploaded_image)

        profile["handle"] = st.sidebar.text_input("ハンドル名", profile.get("handle", ""))
        profile["bio"] = st.sidebar.text_area("自己紹介", profile.get("bio", ""))
        profile["followers"] = st.sidebar.number_input("フォロワー数", min_value=0, value=profile.get("followers", 0))
        profile["following"] = st.sidebar.number_input("フォロー数", min_value=0, value=profile.get("following", 0))

    # --- 表示 ---
    if profile.get("image"):
        st.image(profile["image"], width=150)
    else:
        st.text("プロフィール画像なし")

    st.subheader(selected_user)
    st.text(profile.get("handle", ""))
    st.write(profile.get("bio", ""))

    col1, col2 = st.columns(2)
    col1.metric("フォロー", profile.get("following", 0))
    col2.metric("フォロワー", profile.get("followers", 0))

    st.write("---")

    # --- 投稿（自分のみ） ---
    if is_own_profile:
        st.subheader("投稿する")
        new_post = st.text_area("新しい投稿を入力", "")
        if st.button("投稿"):
            if new_post.strip():
                profile["posts"].insert(0, new_post)
                st.success("投稿しました！")
            else:
                st.warning("投稿内容が空です。")

    # --- 投稿表示（誰でも閲覧可能） ---
    st.subheader("最近の投稿")
    if profile.get("posts"):
        for post in profile["posts"]:
            st.write(f"💬 {post}")
    else:
        st.write("まだ投稿はありません。")