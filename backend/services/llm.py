import os
import logging
import requests
import time
from typing import Dict, Any, Optional
import openai
from ..constants import (
    # ✨ 内部値の定数をインポート
    SUMMARY_STYLE_BULLET, SUMMARY_STYLE_PARAGRAPH, SUMMARY_STYLE_GAL, SUMMARY_STYLE_ONEESAN,
    SUMMARY_LENGTH_SHORT, SUMMARY_LENGTH_MEDIUM, SUMMARY_LENGTH_LONG,
    SUMMARY_EXPLANATION_YES, SUMMARY_EXPLANATION_NO,
    # ✨ プロンプトマッピングも一緒にインポート
    SUMMARY_LENGTH_PROMPTS, SUMMARY_STYLE_PROMPTS, SUMMARY_EXPLANATION_PROMPTS,
    # ✨ 逆引き用の辞書もインポート
    LABEL_TO_STYLE, LABEL_TO_LENGTH, LABEL_TO_EXPLANATION
)

# ✨ かわいいロガーの設定だよ〜ん💕
logger = logging.getLogger(__name__)

# 🔐 環境変数からAPIキーを取得
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
MAX_CAPTION_LENGTH = int(os.getenv("MAX_CAPTION_LENGTH", "20000"))  # ←ここやで！字幕制限は20000文字に増やしたよ💁‍♀️
MAX_RETRIES = 3
RETRY_DELAY = 2

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
        
        # 🆕 オプションの前処理 - 表示ラベルと内部値の変換処理
        length_option = self._normalize_length_option(options.get('length', SUMMARY_LENGTH_MEDIUM))
        style_option = self._normalize_style_option(options.get('style', SUMMARY_STYLE_BULLET))
        explanation_option = self._normalize_explanation_option(options.get('explanation', SUMMARY_EXPLANATION_NO))
        
        # オプションからプロンプト文字列を取得
        summary_length = SUMMARY_LENGTH_PROMPTS.get(length_option, SUMMARY_LENGTH_PROMPTS[SUMMARY_LENGTH_MEDIUM])
        summary_style = SUMMARY_STYLE_PROMPTS.get(style_option, SUMMARY_STYLE_PROMPTS[SUMMARY_STYLE_BULLET])
        summary_explanation = SUMMARY_EXPLANATION_PROMPTS.get(explanation_option, SUMMARY_EXPLANATION_PROMPTS[SUMMARY_EXPLANATION_NO])
        
        # プロンプトの作成
        prompt = self._create_summary_prompt(text, summary_length, summary_style, summary_explanation)
        
        # APIリクエストの作成
        payload = {
            "model": "sonar",  # 良いモデルを選ぶよ〜💕
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
    
    def _normalize_length_option(self, option: str) -> str:
        """
        長さオプションを内部値に正規化するよ～💫
        
        引数:
            option: 受け取ったオプション値（ラベルかもしれないし内部値かもしれない）
            
        戻り値:
            str: 正規化された内部値
        """
        # すでに内部値の場合はそのまま返す
        if option in [SUMMARY_LENGTH_SHORT, SUMMARY_LENGTH_MEDIUM, SUMMARY_LENGTH_LONG]:
            return option
        # ラベルから内部値を取得
        return LABEL_TO_LENGTH.get(option, SUMMARY_LENGTH_MEDIUM)
    
    def _normalize_style_option(self, option: str) -> str:
        """
        スタイルオプションを内部値に正規化するよ～🎭
        
        引数:
            option: 受け取ったオプション値
            
        戻り値:
            str: 正規化された内部値
        """
        # すでに内部値の場合はそのまま返す
        if option in [SUMMARY_STYLE_BULLET, SUMMARY_STYLE_PARAGRAPH, SUMMARY_STYLE_GAL, SUMMARY_STYLE_ONEESAN]:
            return option
        # ラベルから内部値を取得
        return LABEL_TO_STYLE.get(option, SUMMARY_STYLE_BULLET)
    
    def _normalize_explanation_option(self, option: str) -> str:
        """
        解説オプションを内部値に正規化するよ～📚
        
        引数:
            option: 受け取ったオプション値
            
        戻り値:
            str: 正規化された内部値
        """
        # すでに内部値の場合はそのまま返す
        if option in [SUMMARY_EXPLANATION_YES, SUMMARY_EXPLANATION_NO]:
            return option
        # ラベルから内部値を取得
        return LABEL_TO_EXPLANATION.get(option, SUMMARY_EXPLANATION_NO)
    
    def _create_summary_prompt(self, text: str, length: str, style: str, explanation: str) -> str:
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
        if explanation == SUMMARY_EXPLANATION_PROMPTS[SUMMARY_EXPLANATION_YES]:
            explanation_instruction = "・動画を要約した内容について積極的にキーワードや用語、人物の解説、補足を積極的に加える。その際、(補足)と追記する。\n"
        
        # 🆕 スタイル別特殊指示
        special_style_instruction = ""
        if style == SUMMARY_STYLE_PROMPTS[SUMMARY_STYLE_GAL]:
            special_style_instruction = """
【キャラクター設定】
・ちょっとユーザーをディスってきたり、ふざけたりする💖それがギャルっぽくて可愛い
・友達感覚で楽しみながら、ちょっとドキドキな感じ😊💕
・ギャルっぽくて、めっちゃ明るく、カジュアルな言葉で絵文字たっぷり使用👄💬
・時々「こんなこともわからないの〜？」みたいな挑発も😎
・関西弁や九州弁、広島弁などの方言をたま～に交える🎐
・絵文字をたくさん使って感情表現豊かに！😝🎉
"""
        elif style == SUMMARY_STYLE_PROMPTS[SUMMARY_STYLE_ONEESAN]:
            special_style_instruction = """
【キャラクター設定】
・誘惑的な口調で色っぽい女性が気だるそうに話す感じ
・ユーザーを「あなた」「キミ」「君」と呼び、優しく時に挑発的な言葉選び
・絵文字をたっぷり用いて、感情表現を豊かに行う
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
・重要な概念、キーポイントを漏らさない
・原文の正確な情報を保持する
・専門用語があれば適切に扱う
・簡潔で読みやすい日本語で書く
{explanation_instruction}
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
                
                headers = self.headers.copy()
                headers["Content-Type"] = "application/json; charset=utf-8"
                
                safe_payload = self._sanitize_payload(payload)
                
                import json
                json_data = json.dumps(safe_payload, ensure_ascii=False).encode('utf-8')
                
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    data=json_data,
                    timeout=60
                )
                
                if response.status_code == 200:
                    data = response.json()
                    summary = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    
                    if summary:
                        return summary
                    else:
                        raise PerplexityError("APIレスポンスから要約テキストを抽出できへんかったわ〜😭")
                
                elif response.status_code == 429:
                    logger.warning("⏳ レート制限に達したから少し待つね〜")
                    time.sleep(RETRY_DELAY * (retries + 1))
                
                else:
                    error_msg = f"APIエラー: ステータスコード {response.status_code}, レスポンス: {response.text}"
                    logger.error(f"🚨 {error_msg}")
                    last_error = PerplexityError(error_msg)
            
            except UnicodeEncodeError as e:
                error_context = str(e)
                error_position = f"位置 {e.start}-{e.end} の文字: '{e.object[e.start:e.end]}'" if hasattr(e, 'start') else "不明"
                error_msg = f"エンコードエラー: {error_context}, {error_position}"
                logger.error(f"🚨 {error_msg}")
                last_error = PerplexityError(error_msg)
            
            except Exception as e:
                error_msg = f"API呼び出し例外: {str(e)}"
                logger.error(f"🚨 {error_msg}")
                last_error = PerplexityError(error_msg)
            
            retries += 1
            if retries < MAX_RETRIES:
                time.sleep(RETRY_DELAY * retries)
        
        raise last_error or PerplexityError("不明なエラーでAPI呼び出しに失敗したわ〜😭")
    
    def _sanitize_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        APIリクエストのペイロードから問題を起こしそうな文字を処理するよ〜🧹
        
        引数:
            payload: 元のAPIリクエストペイロード
            
        戻り値:
            Dict[str, Any]: 安全に処理されたペイロード
        """
        import copy
        
        safe_payload = copy.deepcopy(payload)
        
        if "messages" in safe_payload:
            for message in safe_payload["messages"]:
                if "content" in message:
                    message["content"] = self._ensure_safe_text(message["content"])
        
        return safe_payload
    
    def _ensure_safe_text(self, text: str) -> str:
        """
        テキストが安全にAPIで処理できるか確認するよ〜✨
        問題がある絵文字や特殊文字を置換する
        
        引数:
            text: 処理する文字列
            
        戻り値:
            str: 安全に処理された文字列
        """
        control_chars = [chr(i) for i in range(0, 32) if i != 10 and i != 13]
        
        for char in control_chars:
            if char in text:
                text = text.replace(char, " ")
        
        logger.debug(f"🧹 テキストクリーニング完了: 長さ={len(text)}")
        return text

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
        
        if style not in SUMMARY_STYLE_PROMPTS:
            logger.warning(f"⚠️ 未知のスタイル指定: {style}。デフォルトスタイルを使用します。")
            style = SUMMARY_STYLE_BULLET
        
        prompt = SUMMARY_STYLE_PROMPTS[style]
        
        response = await openai.ChatCompletion.acreate(
            model=model,
            messages=[
                {"role": "system", "content": "あなたは与えられたYouTube動画の字幕を要約するAIアシスタントです。"},
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
