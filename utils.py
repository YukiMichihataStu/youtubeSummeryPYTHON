import re
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.errors import NoTranscriptFound, TranscriptsDisabled, VideoUnavailable

def extract_video_id(url):
    """YouTube URLからビデオIDを抽出するんやで〜😊"""
    youtube_regex = r'(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
    match = re.search(youtube_regex, url)
    return match.group(1) if match else None

def get_youtube_transcript(video_id, languages=['ja', 'en']):
    """
    YouTubeの字幕を取得する関数やで〜🎬
    エラーもちゃんと種類別に処理するで！
    """
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
        return transcript, None
    except NoTranscriptFound:
        return None, "字幕がないみたい…他の動画を試してみてね！💔"
    except TranscriptsDisabled:
        return None, "この動画は字幕が無効になっとるわ！別の動画を試してみてな！🔒"
    except VideoUnavailable:
        return None, "この動画は見れへんわ...削除されたか非公開になってるかも！⛔"
    except Exception as e:
        return None, f"API制限にかかったかも！少し時間おいてから試してみて！😭\n詳細: {str(e)}"
