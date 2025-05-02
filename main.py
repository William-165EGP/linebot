from flask import Flask, request, abort, send_from_directory
from flask import render_template   
import os
import logging
import sqlite3
import datetime
from dotenv import load_dotenv
import google.generativeai as genai

from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    StickerMessage,
    ImageMessage,
    VideoMessage,
    LocationMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    StickerMessageContent,
    ImageMessageContent,
    VideoMessageContent
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)

configuration = Configuration(access_token=os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-2.5-pro-exp-03-25')

DB_PATH = 'line_bot_chat.db'

# 靜態文件夾，用於存放用戶上傳的媒體文件
MEDIA_FOLDER = os.path.join(app.root_path, 'media')
os.makedirs(MEDIA_FOLDER, exist_ok=True)

DEFAULT_STICKER_PACKAGE_ID = '11537'
DEFAULT_STICKER_ID = '52002734'


def init_db():
    """初始化資料庫，創建消息表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        message_type TEXT NOT NULL,
        content TEXT,
        media_url TEXT,
        bot_response TEXT NOT NULL,
        bot_response_type TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    conn.commit()
    conn.close()
    logger.info("資料庫初始化完成")

def save_message(user_id, message_type, content, media_url, bot_response, bot_response_type):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO messages (user_id, message_type, content, media_url, bot_response, bot_response_type, timestamp) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user_id, message_type, content, media_url, bot_response, bot_response_type, timestamp)
    )
    conn.commit()
    conn.close()
    logger.info(f"消息已保存到資料庫: {user_id}, {message_type}")

@app.route("/callback", methods=['POST'])
def callback():
    """處理Line平台的Webhook"""
    signature = request.headers['X-Line-Signature']

    body = request.get_data(as_text=True)
    logger.info(f"Request body: {body}")

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.error("無效的簽名。請檢查您的channel access token/channel secret。")
        abort(400)

    return 'OK'

@app.route('/api/getfile/<path:filename>')
def get_file(filename):
    print(f"Requesting file: {MEDIA_FOLDER}", filename)
    return send_from_directory(MEDIA_FOLDER, filename)

@app.route('/')
def chat_viewer():
    return render_template('index.html')

@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    user_id = event.source.user_id
    user_message = event.message.text
    
    try:
        # 檢查是否是特殊命令
        if user_message.lower() == 'sticker':
            # 回傳貼圖
            with ApiClient(configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[
                            StickerMessage(
                                package_id='11537',
                                sticker_id='52002734'
                            )
                        ]
                    )
                )
            
            # 保存到資料庫
            save_message(
                user_id=user_id,
                message_type="text",
                content=user_message,
                media_url=None,
                bot_response="回傳貼圖 (Package ID: 11537, Sticker ID: 52002734)",
                bot_response_type="sticker"
            )
            
        elif user_message.lower() == 'photo':
            # 回傳圖片
            with ApiClient(configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[
                            ImageMessage(
                                original_content_url='https://line.huan.ng/api/getfile/xjp.jpg',
                                preview_image_url='https://line.huan.ng/api/getfile/xjp.jpg'
                            )
                        ]
                    )
                )
            
            # 保存到資料庫
            save_message(
                user_id=user_id,
                message_type="text",
                content=user_message,
                media_url=None,
                bot_response="回傳圖片 (URL:https://line.huan.ng/api/getfile/1.png)",
                bot_response_type="image"
            )
            
        elif user_message.lower() == 'video':
            # 回傳影片
            with ApiClient(configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[
                            VideoMessage(
                                original_content_url='https://line.huan.ng/api/getfile/xjp_sb.mp4',
                                preview_image_url='https://line.huan.ng/api/getfile/xjp.jpg'
                            )
                        ]
                    )
                )
            
            # 保存到資料庫
            save_message(
                user_id=user_id,
                message_type="text",
                content=user_message,
                media_url=None,
                bot_response="回傳影片 (URL:https://line.huan.ng/api/getfile/xjp.mp4)",
                bot_response_type="video"
            )

        elif user_message.lower() == 'location':
            # 回傳位置
            with ApiClient(configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[
                            LocationMessage(
                                title='LAGOS UNIVERSITY',
                                address='University of Lagos, University Road Lagos Mainland Akoka, Yaba, Lagos, Nigeria',
                                latitude=6.515714,
                                longitude=3.389823,
                            )
                        ]
                    )
                )
    
            # 保存到資料庫
            save_message(
                user_id=user_id,
                message_type="text",
                content=user_message,
                media_url=None,
                bot_response="回傳位置 (LAGOS UNIVERSITY, 緯度: 6.515714, 經度: 3.389823)",
                bot_response_type="location"
            )
            
        else:
            # 一般文字處理 - 使用Gemini生成回應
            response = model.generate_content(user_message)
            
            # 獲取Gemini的回應文本
            if hasattr(response, 'text'):
                reply_text = response.text
            else:
                # 處理複雜回應
                parts = []
                for part in response.parts:
                    if hasattr(part, 'text'):
                        parts.append(part.text)
                reply_text = "\n".join(parts)
            
            # 如果回應太長，Line可能無法處理，所以限制長度
            if len(reply_text) > 5000:
                reply_text = reply_text[:4997] + "..."
            
            # 保存消息到資料庫
            save_message(
                user_id=user_id,
                message_type="text",
                content=user_message,
                media_url=None,
                bot_response=reply_text,
                bot_response_type="text"
            )
            
            # 回復用戶
            with ApiClient(configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=reply_text)]
                    )
                )
                
    except Exception as e:
        logger.error(f"處理文字訊息時發生錯誤: {e}")
        error_message = "抱歉，處理您的訊息時發生錯誤。請稍後再試。"
        
        # 保存錯誤到資料庫
        save_message(
            user_id=user_id,
            message_type="text",
            content=user_message,
            media_url=None,
            bot_response=error_message,
            bot_response_type="text"
        )
        
        # 發送錯誤
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=error_message)]
                )
            )

# 添加API端點：獲取聊天歷史
@app.route("/api/chat-history", methods=['GET'])
def get_chat_history():
    from flask import jsonify
    user_id = request.args.get('user_id')
    limit = request.args.get('limit', default=50, type=int)
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if user_id:
        cursor.execute(
            "SELECT * FROM messages WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
            (user_id, limit)
        )
    else:
        cursor.execute(
            "SELECT * FROM messages ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        )
    
    rows = cursor.fetchall()
    conn.close()
    
    result = []
    for row in rows:
        result.append({
            'id': row['id'],
            'user_id': row['user_id'],
            'message_type': row['message_type'],
            'content': row['content'],
            'media_url': row['media_url'],
            'bot_response': row['bot_response'],
            'bot_response_type': row['bot_response_type'],
            'timestamp': row['timestamp']
        })
    
    return jsonify(result)

# API端點：刪除聊天歷史
@app.route("/api/chat-history", methods=['DELETE'])
def delete_chat_history():
    from flask import jsonify
    user_id = request.args.get('user_id')
    message_id = request.args.get('message_id')
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if message_id:
        cursor.execute("DELETE FROM messages WHERE id = ?", (message_id,))
        affected_rows = cursor.rowcount
    elif user_id:
        cursor.execute("DELETE FROM messages WHERE user_id = ?", (user_id,))
        affected_rows = cursor.rowcount
    else:
        conn.close()
        return jsonify({'error': '必須指定user_id或message_id參數'}), 400
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'deleted_count': affected_rows
    })

if __name__ == "__main__":
    # 確保資料庫初始化
    init_db()
    app.run(port=8964, host='0.0.0.0')