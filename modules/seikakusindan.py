import streamlit as st

st.set_page_config(page_title="mebius性格診断", layout="centered")

st.title("🧠 mebius簡易性格診断（Big Five）")
st.write("以下の20問に答えて、あなたの関係性スタイルを可視化しましょう。")

# 質問データ
questions = {
    "外向性": [
        ("友達を作るのは簡単だ", False),
        ("初対面の人とすぐに打ち解けられる", False),
        ("人と一緒にいると元気が出る", False),
        ("一人で過ごす時間が好きだ", True),
    ],
    "協調性": [
        ("他人を信頼するほうだ", False),
        ("人の気持ちに敏感に反応する", False),
        ("自分のために他人を利用するほうだ", True),
        ("争いごとは避けたいと思う", False),
    ],
    "誠実性": [
        ("仕事は完璧にこなすほうだ", False),
        ("計画的に物事を進める", False),
        ("約束を守ることを重視している", False),
        ("物事を後回しにしがちだ", True),
    ],
    "神経症傾向": [
        ("心配性だ", False),
        ("些細なことで不安になる", False),
        ("気分が落ち込みやすい", False),
        ("ストレスに強いほうだ", True),
    ],
    "開放性": [
        ("想像力が豊かだ", False),
        ("芸術は重要だと思う", False),
        ("新しいアイデアに興味を持つ", False),
        ("慣れたやり方を好む", True),
    ]
}

# 回答保存用
responses = {}

# 質問表示
for trait, items in questions.items():
    st.subheader(f"🔹 {trait}")
    for i, (q, is_reverse) in enumerate(items):
        key = f"{trait}_{i}"
        responses[key] = st.slider(q, 1, 5, 3, key=key)

# 結果計算
if st.button("診断結果を見る"):
    st.markdown("---")
    st.subheader("🧾 あなたの診断結果")

    for trait, items in questions.items():
        total = 0
        for i, (_, is_reverse) in enumerate(items):
            key = f"{trait}_{i}"
            score = responses[key]
            if is_reverse:
                score = 6 - score  # 逆スコア反転
            total += score
        avg = round(total / len(items), 2)
        st.write(f"・{trait}：{avg} / 5")

    st.markdown("---")
    st.info("この結果は、プロフィールの水玉模様生成や関係性カラー設計に活用できます。")