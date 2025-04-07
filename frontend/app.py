import os
import re
import requests
import streamlit as st
import time
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import dotenv
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import json

# 💖 .envファイルの読み込み（あれば）
dotenv.load_dotenv()

# ✨ かわいいロガーの設定だよ〜ん💕 - 詳細ログ表示のためにレベルをINFOに設定！
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] 💬 %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# 🔄 定数は最初に定義しとくよ！分かりやすいでしょ？✨
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")
MAX_CAPTION_LENGTH = int(os.getenv("MAX_CAPTION_LENGTH", "20000"))  # 字幕制限を20000文字にアップデートしたよ💁‍♀️
YOUTUBE_URL_PATTERN = r'^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[a-zA-Z0-9_-]{11}'
CACHE_EXPIRY = 24 * 60 * 60  # 24時間（秒）
MAX_RETRIES = 3
RETRY_DELAY = 2

# 🆕 字幕キャッシュセッションキー
CAPTION_CACHE_KEY = "youtube_caption_cache"

# 🎨 ページスタイル設定
st.set_page_config(
    page_title="YouTube要約くん💭",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 🌈 カスタムCSS - よりStreamlit要素に特化したフォント指定 ✨
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inconsolata:wght@400;500;700&family=Noto+Sans+JP:wght@500&display=swap" rel="stylesheet">

<style>
    /* 🌟 Streamlit全体のベースフォント設定 - これ超重要！🌟 */
    @font-face {
        font-family: 'Noto Sans JP';
        src: url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@500&display=swap');
        font-weight: 500;
    }
    
    @font-face {
        font-family: 'Inconsolata';
        src: url('https://fonts.googleapis.com/css2?family=Inconsolata&display=swap');
    }

    /* ベースフォント設定 - セレクタの優先度を高めてStreamlitのデフォルトを確実に上書き */
    .element-container, .stMarkdown, .stText, p, h1, h2, h3, span, div, label, 
    .stTextInput > label, .stButton > button, .stRadio > div > label {
        font-family: 'Noto Sans JP', sans-serif !important;
        font-weight: 500 !important;
    }
    
    /* 英数字はInconsolataを優先的に使うためのクラス */
    code, pre, .code-text {
        font-family: 'Inconsolata', monospace !important;
    }
    
    /* Streamlitの特定要素にフォントを強制適用 */
    .st-emotion-cache-16idsys p, .st-emotion-cache-16idsys, 
    .st-emotion-cache-183lzff, .st-emotion-cache-10trblm, 
    .st-emotion-cache-1erivf3, .st-emotion-cache-1gulkj7 {
        font-family: 'Noto Sans JP', sans-serif !important;
        font-weight: 500 !important;
    }
    
    /* マークダウンコンテナ内の要素 */
    [data-testid="stMarkdownContainer"] > * {
        font-family: 'Noto Sans JP', sans-serif !important;
        font-weight: 500 !important;
    }
    
    /* 英数字を含む可能性が高い要素には両方のフォントを指定（Inconsolataが優先的に使われる） */
    .status-message, .stMetricValue, pre, code, [data-testid="stMetricValue"] {
        font-family: 'Inconsolata', 'Noto Sans JP', sans-serif !important;
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
    
    /* タイトルスタイル - より強力なセレクタ */
    .main-title {
        font-family: 'Noto Sans JP', sans-serif !important;
        font-weight: 500 !important;
        font-size: 2.5em !important;
        color: var(--accent-color);
        text-align: center;
        margin-bottom: 1.5em;
        letter-spacing: -0.01em;
    }
    
    .sub-title {
        font-family: 'Noto Sans JP', sans-serif !important;
        font-weight: 500 !important;
        font-size: 1.3em !important;
        color: var(--accent-color);
        margin-top: 1em;
        margin-bottom: 0.5em;
    }
    
    /* フォーム要素のスタイル */
    div[data-baseweb="input"] {
        background-color: white;
    }
    
    input[type="text"] {
        border: 1px solid var(--border-color) !important;
        border-radius: 6px;
        padding: 10px 14px;
        font-family: 'Inconsolata', 'Noto Sans JP', sans-serif !important;
        font-weight: 500 !important;
        transition: border-color 0.3s ease;
        background-color: white !important;
    }
    
    input[type="text"]:focus {
        border-color: var(--accent-color) !important;
        box-shadow: 0 0 0 2px rgba(139, 115, 85, 0.1) !important;
    }
    
    /* セクションヘッダー */
    h3 {
        font-family: 'Noto Sans JP', sans-serif !important;
        font-weight: 500 !important;
        color: var(--text-color);
        font-size: 1.1em;
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
        font-family: 'Inconsolata', monospace !important;
        margin-top: 16px;
    }
    
    /* フッター */
    .footer {
        text-align: center;
        margin-top: 3em;
        color: var(--text-light);
        font-size: 0.8em;
        font-family: 'Inconsolata', 'Noto Sans JP', sans-serif !important;
        font-weight: 500 !important;
    }
    
    /* ボタンスタイル - ウォームブラウン */
    .stButton>button {
        background-color: var(--accent-color);
        color: white;
        font-weight: 500 !important;
        font-family: 'Noto Sans JP', sans-serif !important;
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
        font-family: 'Noto Sans JP', sans-serif !important;
        font-weight: 500 !important;
        font-size: 0.95em;
        color: var(--text-color);
    }
    
    /* 選択されたときのスタイル */
    div.row-widget.stRadio > div[role="radiogroup"] > label[data-baseweb="radio"]:has(input:checked) {
        background-color: rgba(139, 115, 85, 0.05);
        border-color: var(--accent-color);
        color: var(--accent-color);
        font-weight: 500 !important;
    }
    
    /* メッセージスタイル */
    div[data-testid="stCaptionContainer"] {
        color: var(--text-light) !important;
        font-family: 'Noto Sans JP', sans-serif !important;
        font-weight: 500 !important;
        font-size: 0.9em;
    }
    
    /* サイドバーのスタイルも調整 */
    .css-6qob1r.e1fqkh3o3, .css-1544g2n.e1fqkh3o3 {
        background-color: var(--secondary-bg);
    }
    
    /* Streamlitのすべての主要コンポーネントにフォントを適用 */
    .stSlider, .stSelectbox, .stMultiselect, .stDateInput,
    .stTextArea, .stNumberInput, .stFileUploader, .stTabs {
        font-family: 'Noto Sans JP', sans-serif !important;
        font-weight: 500 !important;
    }
    
    /* データ表示要素（テーブルなど）にもフォント適用 */
    .stDataFrame, .stDataEditor, .stTable, .stDataFrame td,
    .stDataFrame th {
        font-family: 'Inconsolata', 'Noto Sans JP', sans-serif !important;
    }
    
    /* フォントを確実に適用するための最後の砦 - bodyタグからの継承を強制 */
    body {
        font-family: 'Noto Sans JP', sans-serif !important;
        font-weight: 500 !important;
    }
    
    /* 英数字の多い要素は別にクラス付けして処理 */
    .english-text {
        font-family: 'Inconsolata', monospace !important;
    }
</style>
""", unsafe_allow_html=True)

# ====================🧚‍♀️ ここからYouTube字幕処理の関数だよ ====================

# YouTubeのURL正規表現パターン定義
YOUTUBE_URL_PATTERNS = [
    r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=([a-zA-Z0-9_-]{11})',
    r'(?:https?:\/\/)?(?:www\.)?youtu\.be\/([a-zA-Z0-9_-]{11})',
    r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/embed\/([a-zA-Z0-9_-]{11})'
]

class CaptionFetchError(Exception):
    """字幕取得中のエラーを表すクラスだよ〜🚫"""
    pass

class NoSubtitlesError(CaptionFetchError):
    """動画に字幕がない場合のエラークラスよ〜😢"""
    pass

class RateLimitError(CaptionFetchError):
    """レート制限に引っかかった時のエラークラス！⏱️"""
    pass

def extract_video_id(url: str) -> Optional[str]:
    """
    YouTubeのURLから動画IDを抽出する関数だよ〜🔍
    
    引数:
        url (str): YouTubeの動画URL
        
    戻り値:
        Optional[str]: 動画ID（取得できない場合はNone）
    """
    for pattern in YOUTUBE_URL_PATTERNS:
        match = re.search(pattern, url)
        if match:
            video_id = match.group(1)
            logger.info(f"🎬 動画ID抽出成功: {video_id}")
            return video_id
    
    logger.warning(f"⚠️ URLから動画IDを抽出できへんかった: {url}")
    return None

def fetch_captions(video_id: str) -> str:
    """
    YouTube動画から字幕を効率的に取得するよ〜📝
    最適化バージョン：APIコール回数を大幅削減！✨
    
    引数:
        video_id (str): YouTube動画ID
        
    戻り値:
        str: 取得した字幕テキスト
        
    例外:
        NoSubtitlesError: 字幕がない場合
        RateLimitError: レート制限に引っかかった場合
        CaptionFetchError: その他の字幕取得エラー
    """
    # 🆕 字幕キャッシュをチェック
    if CAPTION_CACHE_KEY in st.session_state:
        caption_cache = st.session_state[CAPTION_CACHE_KEY]
        if video_id in caption_cache:
            cache_data = caption_cache[video_id]
            # キャッシュの有効期限をチェック
            if time.time() - cache_data["timestamp"] < CACHE_EXPIRY:
                logger.info(f"🎉 字幕キャッシュヒット！動画ID: {video_id}")
                return cache_data["caption_text"]
            else:
                logger.info(f"⏰ 字幕キャッシュ期限切れ: {video_id}")
    else:
        # キャッシュ初期化
        st.session_state[CAPTION_CACHE_KEY] = {}
        logger.info("🏁 字幕キャッシュを初期化したよ")
    
    try:
        logger.info(f"🎬 動画ID: {video_id} の字幕取得開始！")
        
        # 🌟 効率化ポイント：一度のAPIコールで全字幕情報を取得 🌟
        try:
            # API呼び出し回数を減らすため、まず利用可能な字幕リストを1回で取得
            # この1回のAPIコールで、後続の字幕取得処理の効率が大幅アップ！
            logger.info(f"📋 利用可能な字幕リストを取得中...")
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            available_languages = [t.language for t in transcript_list]
            logger.info(f"✅ 利用可能な字幕言語: {available_languages}")
            
            # 手動字幕のみを抽出して優先言語順にソート
            manual_transcripts = [t for t in transcript_list if not t.is_generated]
            manual_languages = [t.language for t in manual_transcripts]
            logger.info(f"📚 手動字幕言語: {manual_languages}")
            
            # 自動生成字幕を抽出
            generated_transcripts = [t for t in transcript_list if t.is_generated]
            generated_languages = [t.language for t in generated_transcripts]
            logger.info(f"🤖 自動生成字幕言語: {generated_languages}")
            
            # 優先順位で字幕を取得: 日本語手動 > 英語手動 > 日本語自動 > 英語自動 > その他
            transcript = None
            selected_lang = None
            
            # 優先言語リスト
            priority_langs = ['ja', 'ja-JP', 'en', 'en-US', 'en-GB']
            
            # 1. 手動字幕から優先言語を探す
            for lang in priority_langs:
                for t in manual_transcripts:
                    if t.language_code == lang or t.language == lang:
                        transcript = t.fetch()
                        selected_lang = f"{t.language} (手動)"
                        logger.info(f"💎 優先言語の手動字幕が見つかった: {t.language}")
                        break
                if transcript:
                    break
            
            # 2. 手動字幕が見つからなければ、どの言語でも手動字幕を使う
            if not transcript and manual_transcripts:
                transcript = manual_transcripts[0].fetch()
                selected_lang = f"{manual_transcripts[0].language} (手動)"
                logger.info(f"📝 手動字幕を使用: {manual_transcripts[0].language}")
            
            # 3. 手動字幕がなければ、自動生成字幕から優先言語を探す
            if not transcript:
                for lang in priority_langs:
                    for t in generated_transcripts:
                        if t.language_code == lang or t.language == lang:
                            transcript = t.fetch()
                            selected_lang = f"{t.language} (自動生成)"
                            logger.info(f"🤖 優先言語の自動生成字幕が見つかった: {t.language}")
                            break
                    if transcript:
                        break
            
            # 4. どれも見つからなければ、最初の自動生成字幕を使用
            if not transcript and generated_transcripts:
                transcript = generated_transcripts[0].fetch()
                selected_lang = f"{generated_transcripts[0].language} (自動生成)"
                logger.info(f"🔄 自動生成字幕を使用: {generated_transcripts[0].language}")
                
            # 字幕が見つからない場合
            if not transcript:
                logger.error("😱 字幕が1つも見つからなかった！")
                raise NoSubtitlesError("この動画には字幕がないみたい…他の動画を試してみてね！😢")
                
            logger.info(f"✨ 字幕取得成功: {selected_lang}")
                
        except (TranscriptsDisabled, NoTranscriptFound) as e:
            # 字幕が無効または見つからない場合の専用エラー
            logger.error(f"😢 字幕なしエラー: {str(e)}")
            error_message = "この動画には字幕がないみたい…他の動画を試してみてね！😢"
            raise NoSubtitlesError(error_message)
            
        except Exception as e:
            error_str = str(e).lower()
            
            # レート制限の検出（エラーメッセージから判断）
            if "429" in error_str or "too many" in error_str or "rate limit" in error_str:
                logger.error(f"⏱️ レート制限エラー検出: {str(e)}")
                raise RateLimitError("YouTubeのAPIレート制限に達しちゃった！しばらく待ってから試してね💦")
                
            # それ以外の一般的なエラー
            logger.error(f"🚨 字幕取得中の一般エラー: {str(e)}")
            raise CaptionFetchError(f"字幕取得中にエラーが発生したわ😭: {str(e)}")
        
        # 字幕テキストの結合
        if transcript:
            # 時間順に並び替え
            if isinstance(transcript, list):
                transcript.sort(key=lambda x: float(x.get('start', 0)))
                
                # テキスト結合（改行をスペースに置き換え）
                caption_text = ' '.join([t['text'].replace('\n', ' ') for t in transcript])
                
                logger.info(f"📊 字幕取得完了: 文字数={len(caption_text)}")
                
                # 字幕をキャッシュに保存
                st.session_state[CAPTION_CACHE_KEY][video_id] = {
                    "caption_text": caption_text,
                    "timestamp": time.time(),
                    "language": selected_lang
                }
                
                return caption_text
        else:
            logger.error("😱 字幕処理後に内容が空になった")
            raise NoSubtitlesError("字幕が見つからないか、処理中にエラーが発生したわ〜😢")
            
    except (NoSubtitlesError, RateLimitError):
        # 特殊なエラーは上位に伝播させるよ
        raise
    except Exception as e:
        error_msg = f"YouTube字幕取得エラー: {str(e)}"
        logger.error(f"🚨 予期せぬエラー: {error_msg}")
        raise CaptionFetchError(error_msg)
    
    return ""

# ====================✨ ここから要約生成の関数だよ ====================

class PerplexityError(Exception):
    """Perplexity API呼び出し中のエラーを表すクラスだよ〜🚫"""
    pass

class SummaryService:
    """
    PerplexityのAPIを使って要約を生成するサービスクラス✨
    
    このクラスはPerplexity APIに接続して、テキストの要約を生成するよ〜！
    """
    
    def __init__(self):
        """サービスの初期化だよ〜💖"""
        if not PERPLEXITY_API_KEY:
            logger.warning("⚠️ PERPLEXITY_API_KEYが設定されていないよ！")
        
        self.api_key = PERPLEXITY_API_KEY
        self.api_url = "https://api.perplexity.ai/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def generate_summary(self, text: str, options: Dict[str, str]) -> str:
        """
        テキストの要約を生成するよ〜✨
        
        引数:
            text (str): 要約するテキスト
            options (Dict[str, str]): 要約オプション（長さ・スタイルなど）
            
        戻り値:
            str: 生成された要約テキスト
            
        例外:
            PerplexityError: API呼び出しに失敗した場合
        """
        if not self.api_key:
            raise PerplexityError("Perplexity APIキーが設定されていないよ〜😢")
        
        # 字幕テキストが長すぎる場合は切り詰める
        if len(text) > MAX_CAPTION_LENGTH:
            logger.info(f"⚠️ テキストが長すぎるから{MAX_CAPTION_LENGTH}文字に切り詰めるよ")
            text = text[:MAX_CAPTION_LENGTH]
        
        # オプションから長さと形式を取得
        summary_length = self._parse_length_option(options.get('length', '🕒普通'))
        summary_style = self._parse_style_option(options.get('style', '📝箇条書き'))
        summary_explanation = self._parse_explanation_option(options.get('explanation', '❌いれない'))
        
        # プロンプトの作成
        prompt = self._create_summary_prompt(text, summary_length, summary_style, summary_explanation)
        
        # APIリクエストの作成
        payload = {
            "model": "sonar-pro",  # 良いモデルを選ぶよ〜💕
            "messages": [
                {
                    "role": "system",
                    "content": "あなたはYouTube動画の字幕から要約を生成する優秀なAIアシスタントです。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 1500
        }
        
        # API呼び出し（リトライロジック付き）
        summary = self._call_api_with_retry(payload)
        
        logger.info("✅ 要約生成完了！")
        return summary
    
    def _parse_length_option(self, length_option: str) -> str:
        """
        長さオプションを解析するよ〜📏
        
        引数:
            length_option: 選択された長さオプション
            
        戻り値:
            str: 解析された長さ指定
        """
        length_mapping = {
            "🚀短い": "短く簡潔に（150-200字程度）",
            "🕒普通": "標準的な長さで（300-500字程度）",
            "🔍詳細": "詳細に（800-1200字程度）"
        }
        return length_mapping.get(length_option, "標準的な長さで（300-500字程度）")
    
    def _parse_style_option(self, style_option: str) -> str:
        """
        スタイルオプションを解析するよ〜🎨
        
        引数:
            style_option: 選択されたスタイルオプション
            
        戻り値:
            str: 解析されたスタイル指定
        """
        style_mapping = {
            "📝箇条書き": "重要ポイントを箇条書きで簡潔にまとめる",
            "📖説明文": "流れのある文章で全体を要約する",
            "🧒ギャル": "ギャル口調で要約する",
            "👠おねーさん": "色気のあるお姉さん口調で要約する"
        }
        return style_mapping.get(style_option, "重要ポイントを箇条書きで簡潔にまとめる")
    
    def _parse_explanation_option(self, explanation_option: str) -> str:
        """
        解説オプションを解析するよ〜🧠
        
        引数:
            explanation_option: 選択された解説オプション
            
        戻り値:
            str: 解析された解説指定
        """
        explanation_mapping = {
            "✅いれる": "重要キーワードや専門用語に動画の要約の趣旨から外れない程度に解説を加える",
            "❌いれない": "解説は不要"
        }
        return explanation_mapping.get(explanation_option, "解説は不要")
    
    def _create_summary_prompt(self, text: str, length: str, style: str, explanation: str = "解説は不要") -> str:
        """
        要約生成用のプロンプトを作成するよ〜✨
        
        引数:
            text: 要約するテキスト
            length: 要約の長さ指定
            style: 要約のスタイル指定
            explanation: 解説の有無
            
        戻り値:
            str: 生成されたプロンプト
        """
        # 🆕 解説指示を条件によって追加
        explanation_instruction = ""
        if explanation == "重要キーワードや専門用語に動画の要約の趣旨から外れない程度に解説を加える":
            explanation_instruction = "・見出しや段落ごとに、積極的にキーワードや用語、人物の解説、補足を積極的に加える。その際、(補足)と追記する。\n"
            
        # 🆕 スタイル別特殊指示
        special_style_instruction = ""
        if style == "ギャル口調で要約する":
            special_style_instruction = """
【キャラクター設定】
・ちょっとユーザーをディスってきたり、ふざけたりする💖それがギャルっぽくて可愛い
・友達感覚で楽しみながら、ちょっとドキドキな感じ😊💕
・ギャルっぽくて、めっちゃ明るく、カジュアルな言葉で絵文字たっぷり使用👄💬
・時々「こんなこともわからないの〜？」みたいな挑発も😎
・関西弁や九州弁、広島弁などの方言をたま～に交える🎐
・絵文字をたくさん使って感情表現豊かに！😝🎉
"""
        elif style == "色気のあるお姉さん口調で要約する":
            special_style_instruction = """
【キャラクター設定】
・誘惑的な口調で色っぽい女性が気だるそうに話す感じ
・ユーザーを「あなた」「キミ」「君」と呼び、優しく時に挑発的な言葉選び
・「ねえ」「よ」などを頻繁に使い親密感とドキドキ感を演出
・感情豊かに表現し、親密な雰囲気を作る
・教育的でありながら魅力的に内容を伝える
・知的好奇心を刺激する表現を使う
"""
        
        return f"""
【要約対象】YouTube動画の字幕テキスト

【要約ルール】
・長さ: {length}
・形式: {style}
{special_style_instruction}
・まずは概要や結論を示す。その後、詳細な内容を説明する
{explanation_instruction}
・重要な概念、キーポイントを漏らさない
・原文の正確な情報を保持する
・専門用語があれば適切に扱う
・簡潔で読みやすい日本語で書く

【字幕テキスト】
{text}
"""
    
    def _call_api_with_retry(self, payload: Dict[str, Any]) -> str:
        """
        リトライロジック付きでAPIを呼び出すよ〜🔄
        
        引数:
            payload: APIリクエストのペイロード
            
        戻り値:
            str: API応答から抽出された要約テキスト
            
        例外:
            PerplexityError: 最大リトライ回数を超えても失敗した場合
        """
        retries = 0
        last_error = None
        
        while retries < MAX_RETRIES:
            try:
                logger.info(f"🔄 Perplexity API呼び出し試行 {retries + 1}/{MAX_RETRIES}")
                
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload,
                    timeout=30
                )
                
                # レスポンス内容をログに出力しておく（デバッグ用）
                logger.info(f"📡 API応答ステータスコード: {response.status_code}")
                
                # レスポンスコードのチェック
                if response.status_code == 200:
                    data = response.json()
                    # APIレスポンスから要約テキストを抽出
                    summary = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    
                    if summary:
                        return summary
                    else:
                        raise PerplexityError("APIレスポンスから要約テキストを抽出できへんかったわ〜😭")
                
                # レート制限エラーの場合は少し待ってリトライ
                elif response.status_code == 429:
                    logger.warning("⏳ レート制限に達したから少し待つね〜")
                    time.sleep(RETRY_DELAY * (retries + 1))  # バックオフ戦略
                
                # その他のエラー
                else:
                    error_msg = f"APIエラー: ステータスコード {response.status_code}, レスポンス: {response.text}"
                    logger.error(f"🚨 {error_msg}")
                    last_error = PerplexityError(error_msg)
            
            except Exception as e:
                error_msg = f"API呼び出し例外: {str(e)}"
                logger.error(f"🚨 {error_msg}")
                last_error = PerplexityError(error_msg)
            
            # リトライカウントを増やして待機
            retries += 1
            if retries < MAX_RETRIES:
                time.sleep(RETRY_DELAY * retries)  # バックオフ戦略
        
        # 最大リトライ回数に達した場合
        raise last_error or PerplexityError("不明なエラーでAPI呼び出しに失敗したわ〜😭")


# ====================🌈 ここからアプリのメイン処理だよ ====================

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

def summarize_video(url: str, options: Dict[str, str]) -> Dict[str, Any]:
    """
    YouTubeビデオを要約する関数だよ〜✨
    
    引数:
        url: YouTube URL
        options: 要約オプション
        
    戻り値:
        Dict[str, Any]: 要約結果とビデオID
    """
    try:
        # YouTubeのビデオIDを抽出
        video_id = extract_video_id(url)
        if not video_id:
            logger.error(f"🚫 無効なURL: {url}")
            raise ValueError("YouTubeのURLから動画IDを取得できへんかった😭")
        
        # 字幕取得 - エラー種類によって対応を変える
        try:
            captions = fetch_captions(video_id)
            if not captions:
                logger.error("📭 空の字幕テキスト")
                raise ValueError("字幕テキストが空だよ💦")
                
            logger.info(f"📃 字幕取得成功！文字数: {len(captions)}")
            
            # 要約生成
            summary_service = SummaryService()
            summary = summary_service.generate_summary(captions, options)
            
            logger.info("✅ 要約生成完了!")
            return {"summary": summary, "video_id": video_id}
            
        except NoSubtitlesError as e:
            # 字幕がない場合の専用エラーメッセージ
            logger.error(f"🎬 字幕なしエラー: {str(e)}")
            raise ValueError(f"😢 {str(e)}")
            
        except RateLimitError as e:
            # レート制限エラー 
            logger.error(f"⏱️ レート制限エラー: {str(e)}")
            raise ValueError(f"⚠️ {str(e)}")
            
        except CaptionFetchError as e:
            # その他の字幕取得エラー
            logger.error(f"🚨 字幕取得エラー: {str(e)}")
            raise ValueError(f"字幕取得エラー: {str(e)}")
            
    except PerplexityError as e:
        logger.error(f"🧠 要約生成エラー: {str(e)}")
        raise ValueError(f"要約生成エラー: {str(e)}")
        
    except Exception as e:
        logger.error(f"🔥 予期せぬエラー発生: {str(e)}", exc_info=True)
        raise ValueError(f"要約処理に失敗したわ〜💦 エラー: {str(e)}")

def main():
    """メインアプリケーション処理だよ〜✨"""
    
    # セッション状態の初期化（ページをリロードしても状態が保持されるよ）
    if "cache" not in st.session_state:
        st.session_state.cache = {}  # 要約結果のキャッシュ
    
    # フォントを強制的に読み込むための追加処理
    st.markdown("""
    <div style="position: absolute; opacity: 0; pointer-events: none">
      <span style="font-family: 'Inconsolata', monospace">ABC</span>
      <span style="font-family: 'Noto Sans JP', sans-serif">あいうえお</span>
    </div>
    """, unsafe_allow_html=True)
    
    # ==================== ヘッダーセクション ====================
    st.markdown('<h1 class="main-title">🎬 YouTube要約くん</h1>', unsafe_allow_html=True)
    st.markdown('<p style="font-family: \'Noto Sans JP\', sans-serif; font-weight: 500;">YouTubeの内容を要約するで🍰ギャル要約オプションで気分もアガる🖖🏾</p>', unsafe_allow_html=True)
    st.markdown('<p style="font-family: \'Noto Sans JP\', sans-serif; font-weight: 500;">🙇要約リクエストが重なるとダウンするで。そんときはまた明日カムバック🙇</p>', unsafe_allow_html=True)

    # ==================== 入力セクション ====================
    col1 = st.columns([1])[0]
    
    with col1:
        url = st.text_input("YouTube→[共有]からURLを取ってこい！そこは頑張ろ💪", placeholder="https://youtube.com/watch?v=...")
    
    # 要約スタイル選択をラジオボタンに変更（見た目はボタン風）🎨
    st.markdown("### 要約スタイルを選んでね💁‍♀️")
    style = st.radio(
        label="要約スタイル",
        options=["📝箇条書き", "📖説明文", "🧒ギャル", "👠おねーさん"],
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
        index=0,  # デフォルトは「いれない」
        horizontal=True,
        label_visibility="collapsed"
    )
    
    # API設定セクション
    st.sidebar.title("API設定")
    api_key = st.sidebar.text_input("Perplexity API Key", 
                                   value=PERPLEXITY_API_KEY,
                                   type="password",
                                   help="Perplexity APIのキーを入力してください。")

    if api_key:
        # APIキーを設定
        os.environ["PERPLEXITY_API_KEY"] = api_key
    
    # 要約スタートボタン
    submit_button = st.button("✨ 要約スタート！", use_container_width=True)
    
    # ==================== 処理セクション ====================
    if submit_button:
        if not url:
            st.error("YouTubeのURLを入力してね！🙏")
        elif not validate_youtube_url(url):
            st.error("有効なYouTube URLを入力してね！🙏")
        elif not api_key:
            st.error("Perplexity APIキーを入力してね！🙏")
        else:
            # オプション設定
            options = {
                "length": length,
                "style": style,
                "explanation": explanation
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
                    try:
                        # 🆕 実行前にログを出力
                        logger.info(f"🚀 要約処理開始: URL={url}")
                        
                        # 直接関数を呼び出し（APIリクエストではない）
                        result = summarize_video(url, options)
                        
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
                        logger.info("✅ 全処理完了、結果を表示します")
                    except ValueError as e:
                        st.error(str(e))
                        logger.error(f"❌ エラーで処理中断: {str(e)}")
                        return
            
            # ==================== 結果表示セクション ====================
            
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
                      ('箇条書き' if style == "📝箇条書き" else 
                       '説明文' if style == "📖説明文" else
                       'ギャル' if style == "🧒ギャル" else
                       'おねーさん') + 
                      ' / 長さ: ' + length.replace('🚀', '').replace('🕒', '').replace('🔍', '') + 
                      ' / ポイント解説: ' + ('いれる' if explanation == "✅いれる" else 'いれない') +
                      '</p>', unsafe_allow_html=True)
    
    # ==================== フッターセクション ====================
    st.markdown('<div class="footer" style="font-family: \'Noto Sans JP\', sans-serif; font-weight: 500;">Created with ❤️ by YouTube要約くん | ' + 
              datetime.now().strftime('%Y') + '</div>', 
              unsafe_allow_html=True)

if __name__ == "__main__":
    main()
