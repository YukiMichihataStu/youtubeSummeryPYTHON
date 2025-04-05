import re
import logging
from typing import Optional, List, Dict, Any
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

# ✨ かわいいロガーの設定だよ〜ん💕
logger = logging.getLogger(__name__)

# 🔗 YouTubeのURL正規表現パターン定義
YOUTUBE_URL_PATTERNS = [
    r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=([a-zA-Z0-9_-]{11})',
    r'(?:https?:\/\/)?(?:www\.)?youtu\.be\/([a-zA-Z0-9_-]{11})',
    r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/embed\/([a-zA-Z0-9_-]{11})'
]

class CaptionFetchError(Exception):
    """字幕取得中のエラーを表すクラスだよ〜🚫"""
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

async def fetch_captions(video_id: str) -> str:
    """
    YouTube動画から字幕を取得するよ〜📝
    
    引数:
        video_id (str): YouTube動画ID
        
    戻り値:
        str: 取得した字幕テキスト
        
    例外:
        CaptionFetchError: 字幕取得に失敗した場合
    """
    try:
        logger.info(f"🔄 字幕取得開始: {video_id}")
        
        # まずは日本語字幕を試す、なければ英語、それでもなければ利用可能な字幕
        languages = ['ja', 'en']
        transcript = None
        errors = []
        
        # 優先言語で試してみる
        for lang in languages:
            try:
                transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])
                logger.info(f"✅ {lang}の字幕を取得できたよ！")
                break
            except (TranscriptsDisabled, NoTranscriptFound) as e:
                errors.append(f"{lang}: {str(e)}")
                continue
        
        # 優先言語で見つからなかった場合は利用可能な字幕を取得
        if transcript is None:
            try:
                transcript = YouTubeTranscriptApi.list_transcripts(video_id)
                transcript = transcript.find_generated_transcript(languages)
                logger.info("📝 自動生成字幕を取得したよ！")
            except Exception as e:
                errors.append(f"自動生成: {str(e)}")
                raise CaptionFetchError(f"字幕取得失敗: {', '.join(errors)}")
        
        # 字幕テキストの結合
        if transcript:
            # 時間順に並び替え
            transcript.sort(key=lambda x: float(x.get('start', 0)))
            
            # テキスト結合（改行をスペースに置き換え）
            caption_text = ' '.join([t['text'].replace('\n', ' ') for t in transcript])
            
            logger.info(f"📊 字幕取得完了: 文字数={len(caption_text)}")
            return caption_text
            
    except Exception as e:
        error_msg = f"YouTube字幕取得エラー: {str(e)}"
        logger.error(f"🚨 {error_msg}")
        raise CaptionFetchError(error_msg)
    
    return ""

def format_captions(transcript_list: List[Dict[str, Any]]) -> str:
    """
    字幕リストをフォーマットして1つの文字列にするよ〜✨
    
    引数:
        transcript_list: 字幕のリスト
        
    戻り値:
        str: フォーマット済みの字幕テキスト
    """
    if not transcript_list:
        return ""
    
    formatted_text = ""
    for item in transcript_list:
        text = item.get('text', '').strip()
        start = item.get('start', 0)
        duration = item.get('duration', 0)
        
        # 時間をHH:MM:SS形式に変換
        start_time = format_time(start)
        
        # 字幕テキストに時間を付加
        formatted_text += f"[{start_time}] {text}\n"
    
    return formatted_text

def format_time(seconds: float) -> str:
    """
    秒数をHH:MM:SS形式に変換するよ〜⏰
    
    引数:
        seconds: 秒数
        
    戻り値:
        str: フォーマット済みの時間文字列
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
