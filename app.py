import streamlit as st
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import openai
import os

# エラーハンドラーをインポート
from utils.error_handler import identify_youtube_error, display_error_message

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
    st.title("YouTube動画要約ツール")

    # 💁‍♀️ 目立つ警告メッセージを追加（めっちゃ目立つ位置！）
    st.warning("""
    ## ⚠️ 注意事項やで〜！⚠️

    **デプロイ環境では YouTube API のレート制限にぶち当たる可能性大やねん！** 😱

    レート制限にかかると要約できへんくなるから、もしエラー出たらちょっと時間空けて試してみてな〜！⏰

    あんまりしつこく連打すると余計にダメになるから、グッと我慢よ〜！😘💕
    """)

    video_url = st.text_input("YouTube動画のURLを入力してください:")
    if st.button("要約を生成"):
        if video_url:
            video_id = video_url.split("v=")[-1]
            transcript = get_video_transcript(video_id)
            if transcript:
                summary = summarize_text(transcript)
                st.subheader("要約")
                st.write(summary)
            else:
                st.error("動画の字幕を取得できませんでした。")
        else:
            st.error("有効なYouTube動画のURLを入力してください。")

    try:
        # 要約処理の実行部分
        pass
    except Exception as e:
        # エラータイプを特定して適切なメッセージを表示
        error_type = identify_youtube_error(str(e))
        display_error_message(error_type, str(e))
        
        # コンソールにもエラー内容を出力
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()