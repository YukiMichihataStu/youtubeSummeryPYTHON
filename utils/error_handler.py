import streamlit as st
import logging

# ガールズトークなログ設定😘
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("YouTubeサマリーちゃん🎀")

# APIエラータイプを識別する関数
def identify_youtube_error(error_message):
    """
    エラーの種類を特定するやつ〜♪
    引数: error_message - エラーメッセージの文字列
    戻り値: エラータイプの文字列
    """
    error_message = error_message.lower()
    
    # レート制限系のキーワード
    rate_limit_keywords = ["quota", "rate", "limit", "exceeded", "too many", "429"]
    
    # 字幕なし系のキーワード
    no_subtitle_keywords = ["subtitle", "caption", "transcript", "not available", "not found"]
    
    # ネットワーク系のキーワード
    network_keywords = ["network", "connection", "timeout", "connect", "unreachable"]
    
    # エラー種別を判定
    for keyword in rate_limit_keywords:
        if keyword in error_message:
            logger.warning(f"レート制限エラー検出: {error_message}")
            return "rate_limit"
            
    for keyword in no_subtitle_keywords:
        if keyword in error_message:
            logger.warning(f"字幕なしエラー検出: {error_message}")
            return "no_subtitle"
            
    for keyword in network_keywords:
        if keyword in error_message:
            logger.warning(f"ネットワークエラー検出: {error_message}")
            return "network"
    
    # どれにも当てはまらない場合
    logger.error(f"不明なエラー: {error_message}")
    return "unknown"

# エラーメッセージを表示する関数
def display_error_message(error_type, error_detail=None):
    """
    エラータイプに応じたメッセージを表示するやつ〜✨
    引数: 
      error_type - エラーの種類
      error_detail - オリジナルのエラー詳細（オプション）
    """
    if error_type == "rate_limit":
        st.error("""
        ## 🚫 API制限に引っかかったみたい〜！😭

        **YouTube API のレート制限に達しちゃったわ！** これよくあるやつ〜！

        ### 💡 対処法：
        - しばらく待って（30分〜1時間くらい）からもう一回試してみて！⏰
        - 同じURLで連続して試さないでね！🙅‍♀️
        - 今日はもう無理かも...明日また来てね〜💕
        
        技術的に言うと：YouTube Data API の1日の割り当て量を使い切っちゃったのよ〜！
        """)
        
    elif error_type == "no_subtitle":
        st.error("""
        ## 📝 字幕がないみたい...😢

        この動画には字幕データがないから要約できないの...ごめんね！

        ### 💡 試してみて：
        - 字幕がある別の動画を試してみてね！
        - 英語の動画だと字幕がある確率高いよ〜！🇺🇸
        """)
        
    elif error_type == "network":
        st.error("""
        ## 📶 ネットワークエラー発生！😵

        YouTubeサーバーに接続できへんかったみたい...

        ### 💪 試してみて：
        - ちょっと待ってからリロードしてみて！🔄
        - インターネット接続を確認してみて〜📱
        """)
        
    else:
        st.error(f"""
        ## 😱 なんかエラー出ちゃった！

        予期せぬエラーが発生したっぽい...ごめんね〜！💦

        ### 🔍 原因かも？：
        - URLが間違ってるかも？🔗
        - 非公開動画かも？🔒
        - 別の動画で試してみて！🎬

        エラー詳細：{error_detail if error_detail else "不明"}
        """)
