import os
import logging
import requests
import time
from typing import Dict, Any, Optional

# ✨ かわいいロガーの設定だよ〜ん💕
logger = logging.getLogger(__name__)

# 🔐 環境変数からAPIキーを取得
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
MAX_CAPTION_LENGTH = int(os.getenv("MAX_CAPTION_LENGTH", "15000"))  # ←ここやで！字幕制限は現在5000文字やで💁‍♀️
MAX_RETRIES = 3
RETRY_DELAY = 2

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
        summary_explanation = self._parse_explanation_option(options.get('explanation', '❌いれない'))  # 🆕 解説オプション追加
        
        # プロンプトの作成
        prompt = self._create_summary_prompt(text, summary_length, summary_style, summary_explanation)  # 修正
        
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
            "📖説明文": "流れのある文章で全体を要約する"
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
            explanation_instruction = "・動画を要約した内容について積極的にキーワードや用語、人物の解説、補足を積極的に加える。その際、(補足)と追記する。\n"
        
        return f"""
【要約対象】YouTube動画の字幕テキスト

【要約ルール】
・長さ: {length}
・形式: {style}
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
