import streamlit as st
from PIL import Image

# --- サイドバー：プロフィール設定 ---
st.sidebar.title("プロフィール設定")

profile_image = st.sidebar.file_uploader("プロフィール画像をアップロード", type=["png", "jpg", "jpeg"])
user_name = st.sidebar.text_input("ユーザー名", "山田太郎")
handle_name = st.sidebar.text_input("ハンドル名", "@yamada")
bio = st.sidebar.text_area("自己紹介", "こんにちは！Streamlitでプロフィール画面を作っています。")
followers = st.sidebar.number_input("フォロワー数", min_value=0, value=123)
following = st.sidebar.number_input("フォロー数", min_value=0, value=45)

# --- メイン画面：プロフィール表示 ---
st.title("プロフィール画面")

# プロフィール画像
if profile_image:
    img = Image.open(profile_image)
    st.image(img, width=150)
else:
    st.text("プロフィール画像なし")

# 名前とハンドル
st.subheader(user_name)
st.text(handle_name)

# 自己紹介
st.write(bio)

# フォロー/フォロワー数
col1, col2 = st.columns(2)
col1.metric("フォロー", following)
col2.metric("フォロワー", followers)

st.write("---")

# --- 投稿エリア ---
st.subheader("投稿する")
if "posts" not in st.session_state:
    st.session_state.posts = []

new_post = st.text_area("新しい投稿を入力", "")
if st.button("投稿"):
    if new_post.strip() != "":
        st.session_state.posts.insert(0, new_post)  # 新しい投稿を先頭に追加
        st.success("投稿しました！")
    else:
        st.warning("投稿内容が空です。")

# --- 投稿表示 ---
st.subheader("最近の投稿")
if st.session_state.posts:
    for post in st.session_state.posts:
        st.write(f"💬 {post}")
else:
    st.write("まだ投稿はありません。")
