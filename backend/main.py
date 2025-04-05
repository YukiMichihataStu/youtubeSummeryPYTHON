import os
import re
import logging
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import Dict, Optional
from dotenv import load_dotenv  # dotenvで環境変数を読み込むで😎

load_dotenv()  # .envファイルから設定をロードする処理👍

# 🔍 デバッグ用: PERPLEXITY_API_KEYが正しく読み込まれてるかチェックするで！
if os.getenv("PERPLEXITY_API_KEY"):
    print("DEBUG: PERPLEXITY_API_KEY is loaded!")  # キーが読み込まれてる場合の出力😃
else:
    print("DEBUG: PERPLEXITY_API_KEY is NOT loaded!")  # 読み込まれてない場合の出力😢

from .services.youtube import fetch_captions, extract_video_id
from .services.llm import SummaryService

# ✨ かわいいロガーの設定だよ〜ん💕
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] 💬 %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# 🔄 定数は最初に定義しとくよ！分かりやすいでしょ？✨
VIDEO_ID_REGEX = r"^[a-zA-Z0-9_-]{11}$"
MAX_RETRIES = 3
RATE_LIMIT = int(os.getenv("RATE_LIMIT", "10"))

app = FastAPI(
    title="YouTube要約API",
    description="YouTubeビデオを自動要約するAPIだよ〜ん🎬✨",
    version="1.0.0"
)

# CORSの設定 - フロントとバックで仲良くできるようにするよ〜💖
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SummarizeRequest(BaseModel):
    """要約リクエストのスキーマ定義よ〜🎀"""
    url: str
    options: Dict[str, str]
    
    @validator('url')
    def validate_url(cls, v):
        """URLがYouTubeのURLかチェックするで〜💅"""
        if not ("youtube.com" in v or "youtu.be" in v):
            raise ValueError("YouTubeのURLじゃないみたい...😢")
        return v

class APIError(Exception):
    """API用のエラークラスだよ〜🚨"""
    def __init__(self, message: str, code: int):
        super().__init__(message)
        self.code = code

# 📝 レート制限チェック用の関数（実際にはRedisなど使うといいね💭）
def check_rate_limit(request: Request):
    # 本来はRedisなどでIP単位でカウント実装するよ🔒
    logger.info(f"⚡️ リクエスト受信: {request.client.host}")
    return True

@app.get("/")
async def root():
    """ヘルスチェック用のルートエンドポイント🏠"""
    logger.info("🏡 ルートエンドポイントにアクセスがあったよ")
    return {"message": "YouTube要約APIだよ〜✨ /summarize にPOSTしてね💕"}

@app.post("/summarize")
async def summarize_video(request: SummarizeRequest, rate_limit_ok: bool = Depends(check_rate_limit)):
    """ビデオを要約するメインエンドポイントだよ〜🎥✨"""
    try:
        logger.info(f"📝 要約リクエスト: {request.url}")
        
        # YouTubeのビデオIDを抽出
        video_id = extract_video_id(request.url)
        if not video_id or not re.match(VIDEO_ID_REGEX, video_id):
            raise HTTPException(status_code=400, detail="YouTubeのURLから動画IDを取得できへんかった😭")
        
        # 字幕取得
        captions = await fetch_captions(video_id)
        if not captions:
            raise HTTPException(status_code=404, detail="字幕が見つからへんかった😢")
        
        logger.info(f"📃 字幕取得成功！文字数: {len(captions)}")
        
        # 要約生成
        summary_service = SummaryService()
        summary = summary_service.generate_summary(captions, request.options)
        
        logger.info("✅ 要約生成完了!")
        return {"summary": summary, "video_id": video_id}
        
    except HTTPException as e:
        # すでにHTTPExceptionならそのまま投げる
        logger.error(f"🚨 HTTPエラー: {str(e.detail)}")
        raise
    except Exception as e:
        # その他のエラーはログ取ってから500エラーとして返す
        logger.error(f"🔥 エラー発生: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"要約処理に失敗したわ〜💦 エラー: {str(e)}")

@app.get("/health")
async def health_check():
    """システムヘルスチェック用エンドポイント🩺"""
    return {"status": "healthy", "message": "システム絶好調だよ〜✨"}

# 💁‍♀️ サーバー起動時のメッセージ
if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 YouTubeビデオ要約サーバーを起動するよ〜！")
    uvicorn.run(app, host="0.0.0.0", port=8000)
