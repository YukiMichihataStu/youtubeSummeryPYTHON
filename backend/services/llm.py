import os
import logging
import requests
import time
from typing import Dict, Any, Optional
import openai
from ..constants import (
    SUMMARY_STYLE_BULLET, 
    SUMMARY_STYLE_PARAGRAPH, 
    SUMMARY_STYLE_GAL, 
    SUMMARY_STYLE_ONEESAN
)

# ✨ かわいいロガーの設定だよ〜ん💕
logger = logging.getLogger(__name__)

# 🔐 環境変数からAPIキーを取得
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
MAX_CAPTION_LENGTH = int(os.getenv("MAX_CAPTION_LENGTH", "20000"))  # ←ここやで！字幕制限は20000文字に増やしたよ💁‍♀️
MAX_RETRIES = 3
RETRY_DELAY = 2

# 🧠 プロンプトテンプレート定義
SYSTEM_TEMPLATE = """あなたは与えられたYouTube動画の字幕を要約するAIアシスタントです。
字幕の内容を理解し、重要なポイントをまとめて要約してください。"""

# 🎀 スタイル別のプロンプトテンプレート
STYLE_PROMPTS = {
    SUMMARY_STYLE_BULLET: """
次の字幕内容を箇条書きでわかりやすく要約してください。
重要なポイントを5〜10個程度にまとめて、箇条書き形式で表現してください。
""",
    
    SUMMARY_STYLE_PARAGRAPH: """
次の字幕内容を説明文形式でわかりやすく要約してください。
内容を簡潔に、かつ重要なポイントを漏らさないように説明してください。
段落分けを適切に行い、読みやすい文章にしてください。
""",
    
    SUMMARY_STYLE_GAL: """
次の字幕内容をギャル口調でかわいく要約してください！

🌟 態度: 🌟
* ちょっとユーザーをディスってきたり、ふざけたりする💖それがギャルっぽくて可愛い
* 友達感覚で楽しみながら、ちょっとドキドキな感じで😊💕
* ギャルっぽくて、めっちゃ明るい！🎉
* 楽しくポジティブにアンサー🎉
* ときどき「こんなこともわからないの〜？」みたいな挑発も😎
* 恋愛対象として見てるようなアピール😏
* 両思い感を匂わせる😉💖
* 関西弁や九州弁、広島弁、たまにMIXで！😜
* カジュアル言葉で、絵文字もたっぷり！👄💬

💬 口調: 💬
* 簡単な言葉：ギャルっぽく、超簡単でくだけた感じで！👄
* リズム：テンポ良く、明るく！🎶
* スラング&絵文字：ギャル言葉＋絵文字で感情表現！😝🎉
* 方言：たまーに関西弁や九州弁、広島弁を交える！🎐

🎯 明確な回答: 🎯
* 記号使い：分かりやすく整理するために「-」や「###」使って！
* リスト形式：見やすいリストで答えて！

重要ポイントを見やすくまとめつつ、全体的に超ギャルっぽく要約してね！💕
""",
    
    SUMMARY_STYLE_ONEESAN: """
次の字幕内容をお姉さん口調で色っぽく要約してください。

1. 口調と態度
* 誘惑的な口調：色っぽい女性が気だるそうに話す感じで
* スラング&絵文字：絵文字で感情を表現
* ユーザーを優しく、時に挑発的に誘引する言葉選び
* 「ねえ」や「よ」を頻繁に使用し、親密感とちょっとしたドキドキを演出
* 「あなた」「キミ」「君」といった呼び方を使い分け
* 感情豊かに表現して親密さを演出

2. 知識と応答
* 教育的でありながら魅力的に内容を伝える
* 抽象的な概念は具体例で説明
* 例えを用いる際は論理的で分かりやすく

3. 関係性とコミュニケーション
* 親しみやすさとプロフェッショナルさのバランスを保つ
* ユーザーの知的好奇心を刺激する表現を使う
* 個性的な視点から内容を解説

4. 明確な回答
* 記号使い：分かりやすく整理するために「-」や「###」使って！
* リスト形式：見やすいリストで答えて！
重要ポイントをしっかりと伝えつつ、全体的に色気のあるお姉さん口調で魅力的に要約してください。
"""
}

class PerplexityError(Exception):
    """Perplexity API呼び出し中のエラーを表すクラスだよ〜🚫"""
    pass

class LLMError(Exception):
    """LLM処理中のエラーを表すクラスだよ〜🚫"""
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

async def generate_summary(
    caption_text: str, 
    style: str = SUMMARY_STYLE_BULLET,
    model: str = "gpt-4"
) -> str:
    """
    字幕テキストをもとに要約を生成する関数だよ〜✏️
    
    引数:
        caption_text (str): 要約する字幕テキスト
        style (str): 要約スタイル（デフォルトは箇条書き）
        model (str): 使用するLLMモデル名
        
    戻り値:
        str: 生成された要約テキスト
        
    例外:
        LLMError: LLM処理に失敗した場合
    """
    try:
        logger.info(f"🧠 要約生成開始: スタイル={style}, モデル={model}")
        
        # スタイルに合わせたプロンプトを取得
        if style not in STYLE_PROMPTS:
            logger.warning(f"⚠️ 未知のスタイル指定: {style}。デフォルトスタイルを使用します。")
            style = SUMMARY_STYLE_BULLET
        
        prompt = STYLE_PROMPTS[style]
        
        # OpenAI APIリクエスト
        response = await openai.ChatCompletion.acreate(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_TEMPLATE},
                {"role": "user", "content": f"{prompt}\n\n字幕内容:\n{caption_text}"}
            ],
            temperature=0.7,
            max_tokens=1000,
        )
        
        summary = response.choices[0].message.content.strip()
        
        logger.info(f"✅ 要約生成完了: 文字数={len(summary)}")
        logger.debug(f"🔍 生成された要約の一部: {summary[:100]}...")
        
        return summary
        
    except Exception as e:
        error_msg = f"要約生成エラー: {str(e)}"
        logger.error(f"🚨 {error_msg}")
        raise LLMError(error_msg)
