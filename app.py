import streamlit as st
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import openai
import os
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.errors import NoTranscriptFound, TranscriptsDisabled, VideoUnavailable

# YouTube APIキーの設定
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# OpenAI APIキーの設定
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

def get_video_transcript(video_id):
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    try:
        response = youtube.captions().list(
            part="snippet",
            videoId=video_id
        ).execute()
        captions = response.get("items", [])
        if not captions:
            return None
        caption_id = captions[0]["id"]
        caption = youtube.captions().download(
            id=caption_id,
            tfmt="srt"
        ).execute()
        return caption.decode("utf-8")
    except HttpError as e:
        error_message = str(e)
        if "subtitles" in error_message.lower():
            st.error("要約処理に失敗したわ〜💦 エラー: 😢 この動画には字幕がないみたい…他の動画を試してみてね！😢")
        else:
            st.error(f"""
            ### あちゃー！😱 要約処理に失敗しちゃった！

            **もしかして、YouTubeのAPIレート制限にぶち当たっちゃったかも〜！** 💔
            
            デプロイ環境だとYouTube APIの使用回数制限があるから、アクセスが集中すると制限かかっちゃうねん！😫
            
            ### 対処法 💪
            - 数分待ってからもう一回試してみて〜 ⏰
            - 別の動画URLで試してみるのもアリやで〜 🎬
            - 何回も失敗するなら、しばらく時間置いてからにしてみてね〜 🕒
            
            エラー詳細: {error_message}
            """)
        print(f"Error occurred: {error_message}")
        return None

def summarize_text(text):
    response = openai.Completion.create(
        engine="davinci",
        prompt=f"次のテキストを要約してください:\n\n{text}",
        max_tokens=150
    )
    summary = response.choices[0].text.strip()
    return summary

def main():
    st.title("YouTube動画要約アプリ 🎥✨")
    
    # 警告メッセージを目立つように表示
    st.warning("⚠️ **注意**: デプロイ環境ではYouTube Transcript APIのレート制限にかかる可能性があるで！😱 \n\n"
               "エラーが出たら少し時間をおいてから再度試してみてな！💖 \n\n"
               "ローカル環境での実行がおすすめやで〜👍")
    
    youtube_url = st.text_input("YouTube動画のURLを入力してね 👇", key="youtube_url")
    
    if st.button("要約スタート！🚀"):
        if youtube_url:
            with st.spinner("要約中やで...ちょっと待ってな！🔍"):
                try:
                    # YouTubeのビデオIDを取得
                    video_id = extract_video_id(youtube_url)
                    if not video_id:
                        st.error("😓 有効なYouTube URLじゃないみたい...もう一度確認してな！")
                        return
                    
                    # 字幕を取得
                    try:
                        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['ja', 'en'])
                    except NoTranscriptFound:
                        st.error("😢 この動画には字幕がないみたい…他の動画を試してみてね！💔")
                        return
                    except TranscriptsDisabled:
                        st.error("🔒 この動画は字幕が無効になっとるわ！別の動画を試してみてな！")
                        return
                    except VideoUnavailable:
                        st.error("⛔ この動画は見れへんわ...削除されたか非公開になってるかも！")
                        return
                    except Exception as e:
                        st.error(f"😭 API制限にかかったかも！少し時間おいてから試してみて！\nエラー詳細: {str(e)}")
                        return
                    
                    # ...existing code...
                    
                except Exception as e:
                    st.error(f"要約処理に失敗したわ〜💦 エラー: {str(e)}")
        else:
            st.warning("URLを入力してからボタン押してな〜！🙏")

    try:
        # 要約処理の実行部分
        pass
    except Exception as e:
        error_message = str(e).lower()
        
        # 💁‍♀️ エラーメッセージを詳細に場合分け
        if "quota" in error_message or "rate" in error_message or "limit" in error_message:
            # レート制限エラーの場合
            st.error("""
            ## 🚫 API制限に引っかかったみたい〜！😭

            **YouTube API のレート制限に達しちゃったわ！** これよくあるやつ〜！

            ### 💡 対処法：
            - しばらく待って（30分〜1時間くらい）からもう一回試してみて！⏰
            - 同じURLで連続して試さないでね！🙅‍♀️
            - 今日はもう無理かも...明日また来てね〜💕

            技術的に言うと：YouTube Data API の1日の割り当て量を使い切っちゃったのよ〜！
            """)
            # デバッグ用にログ出力
            print(f"Rate limit error occurred: {error_message}")
            
        elif "subtitle" in error_message or "captions" in error_message:
            # 字幕が存在しない場合
            st.error("要約処理に失敗したわ〜💦 エラー: 😢 この動画には字幕がないみたい…他の動画を試してみてね！😢")
            # デバッグ用にログ出力
            print(f"No subtitles error: {error_message}")
            
        elif "network" in error_message or "connect" in error_message:
            # ネットワークエラーの場合
            st.error("""
            ## 📶 ネットワークエラー発生！😵

            YouTubeサーバーに接続できへんかったみたい...

            ### 💪 試してみて：
            - ちょっと待ってからリロードしてみて！🔄
            - インターネット接続を確認してみて〜📱
            
            YouTubeさんのサーバーが忙しいのかも...💭
            """)
            # デバッグ用にログ出力
            print(f"Network error: {error_message}")
            
        else:
            # その他のエラー
            st.error(f"""
            ## 😱 なんかエラー出ちゃった！

            予期せぬエラーが発生したっぽい...ごめんね〜！💦

            ### 🔍 原因かも？：
            - URLが間違ってるかも？🔗
            - 非公開動画かも？🔒
            - 別の動画で試してみて！🎬

            エラー詳細：{str(e)}
            """)
            # デバッグ用にログ出力
            print(f"Unknown error: {error_message}")

if __name__ == "__main__":
    main()