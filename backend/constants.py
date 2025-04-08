# 📝 オプション定数まとめ～パリピ編 🌈

# 🎀 要約スタイル定数 - 内部処理用の値
SUMMARY_STYLE_BULLET = "bullet"     # 箇条書き
SUMMARY_STYLE_PARAGRAPH = "paragraph"  # 説明文
SUMMARY_STYLE_GAL = "gal"           # ギャル口調
SUMMARY_STYLE_ONEESAN = "oneesan"   # おねーさん口調

# 🎀 要約スタイル選択肢 - 表示と内部値のペア
SUMMARY_STYLES = [
    {"value": SUMMARY_STYLE_BULLET, "label": "📝箇条書き"},
    {"value": SUMMARY_STYLE_PARAGRAPH, "label": "📖説明文"},
    {"value": SUMMARY_STYLE_GAL, "label": "🧒ギャル"},
    {"value": SUMMARY_STYLE_ONEESAN, "label": "👠おねーさん"},
]

# 📏 要約長さ定数 - 内部処理用の値
SUMMARY_LENGTH_SHORT = "short"    # 短い
SUMMARY_LENGTH_MEDIUM = "medium"  # 普通
SUMMARY_LENGTH_LONG = "long"      # 詳細

# 📏 要約長さ選択肢 - 表示と内部値のペア
SUMMARY_LENGTHS = [
    {"value": SUMMARY_LENGTH_SHORT, "label": "🚀短い"},
    {"value": SUMMARY_LENGTH_MEDIUM, "label": "🕒普通"},
    {"value": SUMMARY_LENGTH_LONG, "label": "🔍詳細"},
]

# 💡 解説オプション定数 - 内部処理用の値
SUMMARY_EXPLANATION_YES = "include"  # 解説あり
SUMMARY_EXPLANATION_NO = "exclude"   # 解説なし

# 💡 解説オプション選択肢 - 表示と内部値のペア
SUMMARY_EXPLANATIONS = [
    {"value": SUMMARY_EXPLANATION_YES, "label": "✅いれる"},
    {"value": SUMMARY_EXPLANATION_NO, "label": "❌いれない"},
]

# 💭 プロンプトマッピング - 内部値から実際のプロンプト指示へのマッピング
SUMMARY_LENGTH_PROMPTS = {
    SUMMARY_LENGTH_SHORT: "短く簡潔に（500字程度）",
    SUMMARY_LENGTH_MEDIUM: "標準的な長さで（800字程度）",
    SUMMARY_LENGTH_LONG: "詳細に（1200字程度）",
}

SUMMARY_STYLE_PROMPTS = {
    SUMMARY_STYLE_BULLET: "重要ポイントを箇条書きで簡潔にまとめる",
    SUMMARY_STYLE_PARAGRAPH: "流れのある文章で全体を要約する",
    SUMMARY_STYLE_GAL: "ギャル口調で要約する",
    SUMMARY_STYLE_ONEESAN: "色気のあるお姉さん口調で要約する",
}

SUMMARY_EXPLANATION_PROMPTS = {
    SUMMARY_EXPLANATION_YES: "・重要キーワードや専門用語、人物などに、動画の要約の趣旨から外れない程度に解説を加える。その解説は、動画の要約内容から引用したり取得するのではなく、一般的な知見の立場から補足する。解説は要約の最後にまとめていれるのではなく、見出しや段落ごとに挿入する。補足を行うときは、(補足)や[補足]などの記号をつけて、要約内容と区別する。\n\n",
    SUMMARY_EXPLANATION_NO: "",
}

# 🔄 逆引き辞書 - ラベルから値を取得するための辞書（ユーティリティ）
LABEL_TO_STYLE = {option["label"]: option["value"] for option in SUMMARY_STYLES}
LABEL_TO_LENGTH = {option["label"]: option["value"] for option in SUMMARY_LENGTHS}
LABEL_TO_EXPLANATION = {option["label"]: option["value"] for option in SUMMARY_EXPLANATIONS}
