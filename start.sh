#!/bin/bash

# めっちゃ便利なサーバー起動スクリプト💖

echo "✨ YouTube要約アプリ起動スクリプト ✨"
echo "バックエンドとStreamlitフロントエンドを同時に起動するでー！"

# ターミナルの色設定
PINK='\033[0;35m'
BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${PINK}💅 おしゃれに準備開始...${NC}"
sleep 1

# バックエンド起動（バックグラウンド）
echo -e "${BLUE}🚀 バックエンド起動中...${NC}"
cd /Users/yukimichihata/youtubeSummeryPYTHON/backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo -e "${GREEN}✅ バックエンドのサーバー起動完了！(PID: $BACKEND_PID)${NC}"

sleep 2

# Streamlitフロントエンド起動
echo -e "${BLUE}💻 Streamlitフロントエンド起動中...${NC}"
cd /Users/yukimichihata/youtubeSummeryPYTHON/frontend
streamlit run app.py --server.port 3000 &
FRONTEND_PID=$!
echo -e "${GREEN}✅ Streamlitフロントエンド起動完了！(PID: $FRONTEND_PID)${NC}"

echo -e "${PINK}🌟 全部準備完了！以下のURLでアクセスしてね：${NC}"
echo -e "   フロントエンド: ${GREEN}http://localhost:3000${NC}"
echo -e "   バックエンドAPI: ${GREEN}http://localhost:8000${NC}"
echo -e "${PINK}💕 このウィンドウを閉じると両方のサーバーが終了するよ！${NC}"

# Ctrl+Cが押されたときの処理
trap 'echo -e "${PINK}👋 終了するね〜！${NC}"; kill $BACKEND_PID $FRONTEND_PID; exit 0' INT

# スクリプトを実行し続ける
wait
