# 🎬 YouTube要約くん 💭

YouTubeの動画を自動で要約するウェブアプリケーションだよ〜✨

## 🌟 特徴

- YouTubeの動画URLから字幕を自動取得
- Perplexity APIを使った高度な要約生成
- 要約スタイル（箇条書き・説明文）を選択可能
- 要約の長さをカスタマイズ可能
- レスポンシブなWebインターフェース

## 🛠️ 技術スタック

- **バックエンド**: FastAPI（Python）
- **フロントエンド**: Streamlit（Python）
- **字幕取得**: youtube-transcript-api
- **要約エンジン**: Perplexity API

## 🚀 セットアップ方法

### 前提条件

- Python 3.8以上
- Perplexity APIキー

### インストール

1. リポジトリをクローン
   ```bash
   git clone https://github.com/yourusername/youtube-summarizer.git
   cd youtube-summarizer
   ```

2. 仮想環境を作成してアクティベート
   ```bash
   python -m venv venv
   source venv_youtubeSummery/bin/activate   # Windowsの場合: venv\Scripts\activate
   ```

3. 依存パッケージをインストール
   ```bash
   pip install -r requirements.txt
   ```

4. `.env`ファイルを設定
   ```bash
   cp .env.example .env
   # .envファイルを編集してAPIキーなどを設定
   ```

### 起動方法

1. バックエンドサーバーを起動
   # 方法①: backendディレクトリに移動してから起動する場合
   ```bash
   cd backend
   uvicorn main:app --reload
   ```
   # 方法②: プロジェクトルートから直接起動する場合
   ```bash
   uvicorn backend.main:app --reload
   ```
   
2. 別のターミナルでフロントエンドを起動
   # 方法①: frontendディレクトリに移動してから起動する場合
   ```bash
   cd frontend
   streamlit run app.py
   ```
   # 方法②: プロジェクトルートから直接起動する場合 (必要なら)
   ```bash
   streamlit run frontend/app.py
   ```

3. ブラウザで http://localhost:8501 にアクセス

## 🎮 使い方

1. YouTubeの動画URLをペースト
2. 要約スタイルと長さを選択
3. 「要約スタート！」ボタンをクリック
4. 要約結果を確認

## 📝 ライセンス

MIT License

## 👨‍💻 作者

Yuki Michihata
