// あたし、YouTubeの要約をするJSだよ〜✨オシャレな機能いっぱいあるからね💖

document.addEventListener('DOMContentLoaded', function() {
    // 初期設定 - 全部の要素を取得しとくよ〜😉
    const form = document.getElementById('summarize-form');
    const resultDiv = document.getElementById('result');
    const loadingDiv = document.getElementById('loading');
    const summaryText = document.getElementById('summary-text');
    const copyBtn = document.getElementById('copy-btn');
    
    // APIのURL（バックエンドのあれだよ）😚
    const API_URL = 'http://localhost:8000/summarize';
    
    // キラキラ✨エフェクト追加（めっちゃかわいいやつ）
    addSparkleEffect();
    
    // フォーム送信イベント
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // フォームの内容を取得 📝
        const url = document.getElementById('url').value;
        const language = document.getElementById('language').value;
        const style = document.getElementById('style').value;
        
        // URLチェック 🔍
        if (!url || (!url.includes('youtube.com') && !url.includes('youtu.be'))) {
            showNotification('YouTubeのURLじゃないみたい...もう一度確認してね！', 'error');
            return;
        }
        
        // ローディング表示開始 ⏳
        resultDiv.classList.add('hidden');
        loadingDiv.classList.remove('hidden');
        
        try {
            // バックエンドAPIにリクエスト送信 🚀
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    url: url,
                    options: {
                        language: language,
                        style: style
                    }
                })
            });
            
            // ステータスコードチェック
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || '要約中にエラーが発生したよ😢');
            }
            
            // 結果の処理
            const data = await response.json();
            
            // 要約を表示
            summaryText.textContent = data.summary;
            loadingDiv.classList.add('hidden');
            resultDiv.classList.remove('hidden');
            
            // 結果エリアに華やかに表示させる✨
            animateResult();
            
        } catch (error) {
            console.error('Error:', error);
            loadingDiv.classList.add('hidden');
            showNotification(error.message || 'なんかエラー出ちゃった...もう一回試してみて！', 'error');
        }
    });
    
    // コピーボタンの設定
    copyBtn.addEventListener('click', function() {
        navigator.clipboard.writeText(summaryText.textContent)
            .then(() => {
                showNotification('要約をコピーしたよ✨', 'success');
                
                // コピー成功時のボタンアニメーション
                this.classList.add('bg-green-600');
                this.textContent = 'コピーしたよ！';
                
                setTimeout(() => {
                    this.classList.remove('bg-green-600');
                    this.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2" /></svg>コピー';
                }, 2000);
            })
            .catch(err => {
                showNotification('コピーできへんかった...', 'error');
            });
    });
    
    // キラキラエフェクト追加関数✨
    function addSparkleEffect() {
        document.addEventListener('mousemove', function(e) {
            // マウス移動10回に1回だけキラキラ作る（多すぎると重くなっちゃうからね）
            if (Math.random() > 0.9) {
                const sparkle = document.createElement('div');
                sparkle.className = 'sparkle';
                
                // キラキラのサイズとかランダムで決める
                const size = Math.random() * 10 + 5;
                sparkle.style.width = `${size}px`;
                sparkle.style.height = `${size}px`;
                sparkle.style.left = `${e.clientX}px`;
                sparkle.style.top = `${e.clientY}px`;
                
                document.body.appendChild(sparkle);
                
                // キラキラは2秒後に消える
                setTimeout(() => {
                    sparkle.remove();
                }, 2000);
            }
        });
    }
    
    // 結果表示アニメーション
    function animateResult() {
        resultDiv.style.opacity = '0';
        resultDiv.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            resultDiv.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            resultDiv.style.opacity = '1';
            resultDiv.style.transform = 'translateY(0)';
        }, 10);
    }
    
    // 通知表示機能
    function showNotification(message, type = 'info') {
        // 既存の通知を削除
        const existingNotifications = document.querySelectorAll('.notification');
        existingNotifications.forEach(notification => notification.remove());
        
        // 新しい通知要素を作成
        const notification = document.createElement('div');
        notification.className = `notification fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg z-50 transition-all duration-500 transform translate-x-full`;
        
        // タイプに応じてスタイル変更
        if (type === 'error') {
            notification.classList.add('bg-red-500', 'text-white');
        } else if (type === 'success') {
            notification.classList.add('bg-green-500', 'text-white');
        } else {
            notification.classList.add('bg-blue-500', 'text-white');
        }
        
        notification.textContent = message;
        
        // ボディに追加
        document.body.appendChild(notification);
        
        // アニメーション表示
        setTimeout(() => {
            notification.classList.remove('translate-x-full');
        }, 10);
        
        // 3秒後に消す
        setTimeout(() => {
            notification.classList.add('translate-x-full');
            setTimeout(() => {
                notification.remove();
            }, 500);
        }, 3000);
    }
    
    // かわいいイースターエッグも入れとく💕
    console.log("✨ YouTube要約メーカー起動したよ〜💖 困ったらF12で開発者ツールを開いてね！");
});
