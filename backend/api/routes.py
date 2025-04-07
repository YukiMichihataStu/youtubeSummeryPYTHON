from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from ..services.youtube import extract_video_id, fetch_captions, CaptionFetchError
from ..services.llm import generate_summary, LLMError
from ..constants import SUMMARY_STYLES, SUMMARY_STYLE_BULLET

router = APIRouter()

@router.get("/summarize")
async def summarize_video(
    url: str,
    style: str = Query(SUMMARY_STYLE_BULLET, description="要約スタイル")
):
    """
    YouTube動画のURLから字幕を取得して要約するエンドポイントだよ〜✨
    
    引数:
        url (str): YouTube動画のURL
        style (str): 要約スタイル（箇条書き、説明文、ギャル口調、おねーさん口調）
        
    戻り値:
        dict: 要約結果を含むJSON
    """
    try:
        # 動画IDを抽出
        video_id = extract_video_id(url)
        if not video_id:
            raise HTTPException(status_code=400, detail="YouTubeのURLから動画IDを抽出できませんでした")
        
        # 字幕を取得
        captions = await fetch_captions(video_id)
        
        # 字幕を要約
        summary = await generate_summary(captions, style=style)
        
        return {
            "video_id": video_id,
            "summary": summary,
            "style": style
        }
        
    except CaptionFetchError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except LLMError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"予期しないエラーが発生しました: {str(e)}")