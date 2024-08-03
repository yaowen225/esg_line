from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import requests
import json

app = Flask(__name__)

# Linebot Channel Secret & Access Token 
CHANNEL_SECRET = '855e08eb92383be77288f8150f46891e'
CHANNEL_ACCESS_TOKEN = 'xVQvGQxkOFmPC9aLewVx9y0VSjfGNeJyIAqwV25AQVY/GkCxn8R1HGfHMAhp9ocs0ESAcM8WbHLbwA6w3GUA/YQVOWcyuepOwQzEQS3xeGkfaEgXr/7m+YImpvP98NkhX/U9zSR4Zt3RMl4ox5NdaQdB04t89/1O/w1cDnyilFU='

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# Dify workflow API URL
WORKFLOW_API_URL = 'https://api.dify.ai/v1/workflows/run'
DIFY_API_KEY = 'app-IRo186junshP2lv9bHBZPgul'  

@app.route("/webhook", methods=['POST'])
def webhook():
    # 獲取 HTTP 標頭中的 X-Line-Signature
    signature = request.headers['X-Line-Signature']
    
    # 獲取請求正文
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        # 驗證請求並解析事件
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # 使用者發送的文字消息
    user_message = event.message.text
    print(user_message)
    # 這裡將訊息轉發到 Dify workflow
    try:
        response = requests.post(
            WORKFLOW_API_URL,
            headers={
                'Authorization': f'Bearer {DIFY_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'inputs': {'query': user_message},
                'response_mode': 'blocking',
                'user': 'abc-123'
            }
        )

        # 檢查響應狀態碼
        if response.status_code != 200:
            app.logger.error(f"Error: Received status code {response.status_code}")
            app.logger.error(f"Response text: {response.text}")
            workflow_response = '無法獲得有效的回應'
        else:
            try:
                # 解析並獲得回應中的 text
                response_data = response.json()
                workflow_response = response_data.get('data', {}).get('outputs', {}).get('text', '無法獲得回應')
            except (requests.exceptions.JSONDecodeError, KeyError) as e:
                app.logger.error(f"Error parsing response: {e}")
                workflow_response = 'API 回應的格式無效'
        print(workflow_response)
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error during API request: {e}")
        workflow_response = f"Error: {str(e)}"
    
    # 回應用戶
    line_bot_api.reply_message(
        reply_token=event.reply_token,
        messages=[TextSendMessage(text=workflow_response)]
    )

if __name__ == "__main__":
    app.run(port=3000)
