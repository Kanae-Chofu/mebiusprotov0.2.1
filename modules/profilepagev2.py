import streamlit as st
from PIL import Image
from modules.user import get_current_user  # ← 1:1チャットと同じユーザー取得関数を使う

def render():
    st.title("プロフィール画面")

    current_user = get_current_user()
    if not current_user:
        st.warning("ログインしてください")
        return

    # --- 初期ユーザー情報 ---
    if "users" not in st.session_state:
        st.session_state.users = {
            "admin": {
                "handle": "admin",
                "bio": "こんにちは！Streamlitでプロフィール画面を作っています。",
                "image": None,
                "posts": []
            },
            "kanae": {
                "handle": "kanae",
                "bio": "物語構造と三国志に夢中な大学生です。",
                "image": None,
                "posts": ["三国志の語り直し、今夜も進行中。"]
            },
            "すする": {
                "handle": "すする",
                "bio": "ラーメンが好き。中学三年生。",
                "image": None,
                "posts": ["あなたの好きなラーメンは？"]
            }
        }

    # --- 初期フォロー関係 ---
    if "follow_relations" not in st.session_state:
        st.session_state.follow_relations = {
            "kanae": ["admin"],
            "admin": [],
            "すする": ["kanae"]
        }

    def get_following(user):
        return st.session_state.follow_relations.get(user, [])

    def get_followers(user):
        return [u for u, follows in st.session_state.follow_relations.items() if user in follows]

    # --- 表示するユーザー選択（メイン画面に移動） ---
    selected_user = st.selectbox("表示するユーザー", list(st.session_state.users.keys()))
    profile = st.session_state.users[selected_user]
    is_own_profile = (selected_user == current_user)

    # --- プロフィール設定（自分のみ） ---
    if is_own_profile:
        st.markdown("### プロフィール設定")
        uploaded_image = st.file_uploader("プロフィール画像をアップロード", type=["png", "jpg", "jpeg"])
        if uploaded_image:
            profile["image"] = Image.open(uploaded_image)

        # ハンドルネームをチャットのユーザー名に固定（@なし）
        profile["handle"] = current_user
        st.text(f"ハンドルネーム： {profile['handle']}")  # 表示のみ

        profile["bio"] = st.text_area("自己紹介", profile.get("bio", ""))

    # --- プロフィール表示 ---
    st.markdown("### プロフィール")
    if profile.get("image"):
        st.image(profile["image"], width=150)
    else:
        st.text("プロフィール画像なし")

    st.subheader(selected_user)
    st.text(f"ハンドルネーム： {profile.get('handle', '')}")
    st.write(profile.get("bio", ""))

    col1, col2 = st.columns(2)
    col1.metric("フォロー", len(get_following(selected_user)))
    col2.metric("フォロワー", len(get_followers(selected_user)))

    # --- フォローボタン（他人のプロフィールのみ） ---
    if not is_own_profile:
        following = get_following(current_user)
        if selected_user in following:
            if st.button("フォロー解除"):
                following.remove(selected_user)
                st.success(f"{selected_user} のフォローを解除しました")
        else:
            if st.button("フォローする"):
                following.append(selected_user)
                st.success(f"{selected_user} をフォローしました")

    st.write("---")

    # --- 投稿（自分のみ） ---
    if is_own_profile:
        st.markdown("### 投稿する")
        new_post = st.text_area("新しい投稿を入力", "")
        if st.button("投稿"):
            if new_post.strip():
                profile["posts"].insert(0, new_post)
                st.success("投稿しました！")
            else:
                st.warning("投稿内容が空です。")

    # --- 投稿表示（誰でも閲覧可能） ---
    st.markdown("### 最近の投稿")
    if profile.get("posts"):
        for post in profile["posts"]:
            st.write(f"💬 {post}")
    else:
        st.write("まだ投稿はありません。")