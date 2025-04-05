import os
import re
import requests
import streamlit as st
import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime

# ✨ かわいいロガーの設定だよ〜ん💕
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] 💬 %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# 🔄 定数は最初に定義しとくよ！分かりやすいでしょ？✨
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
YOUTUBE_URL_PATTERN = r'^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[a-zA-Z0-9_-]{11}'
CACHE_EXPIRY = 24 * 60 * 60  # 24時間（秒）

# 🎨 ページスタイル設定
st.set_page_config(
    page_title="YouTube要約くん💭",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 🌈 カスタムCSS - ベージュ系のやさしいデザイン✨
st.markdown("""
<style>
    /* ✨ フォント設定 ✨ */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&family=Inconsolata:wght@400;500;700&display=swap');
    
    /* ベースとなる全体設定 */
    html, body, [class*="css"] {
        font-family: 'Noto Sans JP', sans-serif;
        color: #3C3C3C;
    }
    
    code, pre {
        font-family: 'Inconsolata', monospace;
    }
    
    /* ✨ 新しい色彩設定 ✨ */
    :root {
        --base-bg: rgb(250, 249, 245);       /* ベース背景色 - 指定された色 */
        --secondary-bg: rgb(240, 238, 230);  /* セカンダリ背景色 - 指定された少し濃い色 */
        --accent-color: #8B7355;             /* アクセントカラー - 温かみのあるブラウン */
        --accent-light: #A89078;             /* 薄いアクセントカラー */
        --accent-dark: #6B5744;              /* 濃いアクセントカラー */
        --text-color: #3C3C3C;               /* テキストカラー - ダークグレイ */
        --text-light: #6A6A6A;               /* 薄いテキストカラー */
        --border-color: #E0DED5;             /* ボーダーカラー - ベージュに合わせた色 */
    }
    
    /* ベース背景色 */
    .stApp {
        background-color: var(--base-bg);
    }
    
    /* メインコンテナ背景 */
    .main .block-container {
        padding: 2rem;
        max-width: 1100px;
        margin: 0 auto;
    }
    
    /* タイトルスタイル */
    .main-title {
        font-family: 'Noto Sans JP', sans-serif;
        font-size: 2.5em !important;
        font-weight: 700;
        color: var(--accent-color);
        text-align: center;
        margin-bottom: 1.5em;
        letter-spacing: -0.01em;
    }
    
    .sub-title {
        font-family: 'Noto Sans JP', sans-serif;
        font-size: 1.3em !important;
        color: var(--accent-color);
        margin-top: 1em;
        margin-bottom: 0.5em;
        font-weight: 600;
    }
    
    /* フォーム要素のスタイル */
    div[data-baseweb="input"] {
        background-color: white;
    }
    
    input[type="text"] {
        border: 1px solid var(--border-color) !important;
        border-radius: 6px;
        padding: 10px 14px;
        font-family: 'Inconsolata', 'Noto Sans JP', sans-serif;
        transition: border-color 0.3s ease;
        background-color: white !important;
    }
    
    input[type="text"]:focus {
        border-color: var(--accent-color) !important;
        box-shadow: 0 0 0 2px rgba(139, 115, 85, 0.1) !important;
    }
    
    /* セクションヘッダー */
    h3 {
        font-family: 'Noto Sans JP', sans-serif;
        color: var(--text-color);
        font-size: 1.1em;
        font-weight: 600;
        margin-top: 1.5em;
        margin-bottom: 0.8em;
    }
    
    /* 結果表示エリア */
    .success-box {
        background-color: white;
        border-radius: 8px;
        padding: 24px;
        margin-top: 24px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        border: 1px solid var(--border-color);
    }
    
    /* ステータスメッセージ */
    .status-message {
        font-size: 0.9em;
        color: var(--text-light);
        font-style: normal;
        font-family: 'Inconsolata', monospace;
        margin-top: 16px;
    }
    
    /* フッター */
    .footer {
        text-align: center;
        margin-top: 3em;
        color: var(--text-light);
        font-size: 0.8em;
        font-family: 'Inconsolata', 'Noto Sans JP', sans-serif;
    }
    
    /* ボタンスタイル - ウォームブラウン */
    .stButton>button {
        background-color: var(--accent-color);
        color: white;
        font-weight: 500;
        font-family: 'Noto Sans JP', sans-serif;
        border: none;
        border-radius: 6px;
        padding: 0.6em 1em;
        font-size: 1.05em;
        transition: all 0.15s ease;
        box-shadow: none;
    }
    
    .stButton>button:hover {
        background-color: var(--accent-dark);
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        transform: translateY(-1px);
    }
    
    /* カスタムラジオボタン - ウォームデザイン */
    div.row-widget.stRadio > div[role="radiogroup"] > label > div:first-child {
        display: none;
    }
    
    div.row-widget.stRadio > div[role="radiogroup"] {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        justify-content: flex-start;
    }
    
    div.row-widget.stRadio > div[role="radiogroup"] > label {
        cursor: pointer;
        background-color: white;
        border: 1px solid var(--border-color);
        border-radius: 6px;
        padding: 8px 16px;
        transition: all 0.15s ease;
        margin: 0 !important;
        font-family: 'Noto Sans JP', sans-serif;
        font-weight: 400;
        font-size: 0.95em;
        color: var(--text-color);
    }
    
    /* 選択されたときのスタイル */
    div.row-widget.stRadio > div[role="radiogroup"] > label[data-baseweb="radio"]:has(input:checked) {
        background-color: rgba(139, 115, 85, 0.05);
        border-color: var(--accent-color);
        color: var(--accent-color);
        font-weight: 500;
    }
    
    /* ホバー時のスタイル */
    div.row-widget.stRadio > div[role="radiogroup"] > label:hover {
        border-color: var(--accent-light);
        background-color: rgba(139, 115, 85, 0.02);
    }
    
    /* メッセージスタイル */
    div[data-testid="stCaptionContainer"] {
        color: var(--text-light) !important;
        font-family: 'Noto Sans JP', sans-serif;
        font-size: 0.9em;
    }
    
    /* 通知のスタイル */
    .stAlert {
        background-color: white;
        border: 1px solid var(--border-color);
        border-radius: 6px;
    }
    
    .stAlert [data-testid="stMarkdownContainer"] p {
        font-family: 'Noto Sans JP', sans-serif;
    }
    
    /* スピナーのスタイル */
    div[data-testid="stSpinner"] > div {
        border-top-color: var(--accent-color) !important;
    }
    
    /* スピナーテキスト */
    div[data-testid="stSpinner"] + div [data-testid="stMarkdownContainer"] p {
        color: var(--text-light);
        font-family: 'Noto Sans JP', sans-serif;
        font-size: 0.95em;
    }
    
    /* サイドバーのスタイルも調整 */
    .css-6qob1r.e1fqkh3o3 {
        background-color: var(--secondary-bg);
    }
</style>
""", unsafe_allow_html=True)

class APIClient:
    """バックエンドAPIクライアントクラスだよ〜🔌"""
    
    @staticmethod
    def summarize(url: str, options: Dict[str, str]) -> Dict[str, Any]:
        """
        YouTubeビデオの要約をリクエストするよ〜📝
        
        引数:
            url: YouTube URL
            options: 要約オプション
        
        戻り値:
            Dict[str, Any]: 要約結果（エラーの場合はエラーメッセージ）
        """
        try:
            logger.info(f"🔄 要約リクエスト送信: {url}")
            
            response = requests.post(
                f"{API_BASE_URL}/summarize",
                json={"url": url, "options": options},
                timeout=60  # タイムアウト設定
            )
            
            if response.status_code == 200:
                logger.info("✅ 要約取得成功！")
                return response.json()
            else:
                error_msg = f"APIエラー: {response.status_code}"
                try:
                    error_detail = response.json().get("detail", "不明なエラー")
                    error_msg += f" - {error_detail}"
                except:
                    pass
                logger.error(f"🚨 {error_msg}")
                return {"error": error_msg}
                
        except Exception as e:
            error_msg = f"APIリクエスト例外: {str(e)}"
            logger.error(f"🚨 {error_msg}")
            return {"error": error_msg}

def validate_youtube_url(url: str) -> bool:
    """
    YouTubeのURLを検証するよ〜🔍
    
    引数:
        url: 検証するURL
        
    戻り値:
        bool: 有効なYouTube URLならTrue
    """
    return bool(re.match(YOUTUBE_URL_PATTERN, url))

def get_youtube_embed_url(url: str) -> Optional[str]:
    """
    YouTube埋め込み用URLを生成するよ〜🎬
    
    引数:
        url: YouTubeの動画URL
        
    戻り値:
        Optional[str]: 埋め込み用URL（取得できない場合はNone）
    """
    match = re.search(r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})', url)
    if match:
        video_id = match.group(1)
        return f"https://www.youtube.com/embed/{video_id}"
    return None

def get_cache_key(url: str, options: Dict[str, str]) -> str:
    """
    キャッシュキーを生成するよ〜🗝️
    
    引数:
        url: YouTube URL
        options: 要約オプション
        
    戻り値:
        str: キャッシュキー
    """
    options_str = "_".join([f"{k}:{v}" for k, v in sorted(options.items())])
    return f"{url}_{options_str}"

def main():
    """メインアプリケーション処理だよ〜✨"""
    
    # セッション状態の初期化（ページをリロードしても状態が保持されるよ）
    if "cache" not in st.session_state:
        st.session_state.cache = {}  # 要約結果のキャッシュ
    
    # ==================== ヘッダーセクション ====================
    st.markdown('<h1 class="main-title">🎬 YouTube要約くん</h1>', unsafe_allow_html=True)
    st.markdown("YouTubeビデオの内容をスマートに要約。URL入力だけでカンタンに使えます。")
    
    # ==================== 入力セクション ====================
    col1 = st.columns([1])[0]
    
    with col1:
        url = st.text_input("YouTube URLをペーストしてね！", placeholder="https://youtube.com/watch?v=...")
    
    # 要約スタイル選択をラジオボタンに変更（見た目はボタン風）🎨
    st.markdown("### 要約スタイルを選んでね💁‍♀️")
    style = st.radio(
        label="要約スタイル",
        options=["📝箇条書き", "📖説明文"],
        index=0,
        horizontal=True,
        label_visibility="collapsed"
    )
    
    # 要約の長さ選択をラジオボタンに変更（見た目はボタン風）📏
    st.markdown("### 要約の長さはどうする？🤔")
    length = st.radio(
        label="要約の長さ",
        options=["🚀短い", "🕒普通", "🔍詳細"],
        index=1,
        horizontal=True,
        label_visibility="collapsed"
    )
    
    # 🆕 ポイント解説オプション追加 🧠
    st.markdown("### ポイント解説いれる？🧐")
    explanation = st.radio(
        label="ポイント解説",
        options=["✅いれる", "❌いれない"],
        index=1,  # デフォルトは「いれない」
        horizontal=True,
        label_visibility="collapsed"
    )
    
    # 要約スタートボタン
    submit_button = st.button("✨ 要約スタート！", use_container_width=True)
    
    # ==================== 処理セクション ====================
    if submit_button:
        if not url:
            st.error("YouTubeのURLを入力してね！🙏")
        elif not validate_youtube_url(url):
            st.error("有効なYouTube URLを入力してね！🙏")
        else:
            # オプション設定
            options = {
                "length": length,
                "style": style,
                "explanation": explanation  # 🆕 解説オプション追加
            }
            
            # キャッシュキー生成
            cache_key = get_cache_key(url, options)
            
            # キャッシュチェック
            cached_result = st.session_state.cache.get(cache_key)
            if cached_result and (time.time() - cached_result["timestamp"]) < CACHE_EXPIRY:
                st.success("キャッシュからの高速表示だよ〜⚡")
                summary = cached_result["summary"]
                video_id = cached_result.get("video_id")
            else:
                # ローディング表示
                with st.spinner("動画を分析中...ちょっと待っててね〜🐢"):
                    # API呼び出し
                    result = APIClient.summarize(url, options)
                    
                    if "error" in result:
                        st.error(f"エラーが発生したよ😢: {result['error']}")
                        return
                    
                    # 結果の取得
                    summary = result.get("summary", "要約生成に失敗しちゃった...")
                    video_id = result.get("video_id")
                    
                    # キャッシュに保存
                    st.session_state.cache[cache_key] = {
                        "summary": summary,
                        "video_id": video_id,
                        "timestamp": time.time()
                    }
                
                st.success("要約完了！✨")
            
            # ==================== 結果表示セクション ====================
            st.markdown('<div class="success-box">', unsafe_allow_html=True)
            
            # 動画埋め込み表示（利用可能な場合）
            embed_url = get_youtube_embed_url(url)
            if embed_url:
                st.markdown('<h2 class="sub-title">📺 参照動画</h2>', unsafe_allow_html=True)
                st.components.v1.iframe(embed_url, height=315)
            
            # 要約結果表示
            st.markdown('<h2 class="sub-title">📝 要約結果</h2>', unsafe_allow_html=True)
            st.markdown(summary)
            
            # メタデータ表示
            st.markdown('<p class="status-message">要約スタイル: ' + 
                      ('箇条書き' if style == "📝箇条書き" else '説明文') + 
                      ' / 長さ: ' + length.replace('🚀', '').replace('🕒', '').replace('🔍', '') + 
                      ' / ポイント解説: ' + ('いれる' if explanation == "✅いれる" else 'いれない') +
                      '</p>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    # ==================== フッターセクション ====================
    st.markdown('<div class="footer">Created with ❤️ by YouTube要約くん | ' + 
              datetime.now().strftime('%Y') + '</div>', 
              unsafe_allow_html=True)

if __name__ == "__main__":
    main()
