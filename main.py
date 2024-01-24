from flask import Flask, request
import requests
import yt_dlp

application = Flask(__name__)

# Replace 'YOUR_BOT_TOKEN' with the actual token obtained from the BotFather
TELEGRAM_API_TOKEN = '6599078590:AAEN3AgDJD7KrZVcBvFwq9Av5L1pVqxa5WE'

# Define the base URL for the Telegram API
BASE_URL = f'https://api.telegram.org/bot{TELEGRAM_API_TOKEN}/'

@application.route('/')
def index():
    return "Telegram Bot is running!"

@application.route(f'/{TELEGRAM_API_TOKEN}', methods=['POST'])
def webhook():
    data = request.get_json()

    if 'message' in data:
        chat_id = data['message']['chat']['id']
        message_text = data['message']['text']

        # Handle the incoming message
        if '/start' in message_text:
            send_message(chat_id, "Привет. Это вот типа бот такой. Не знаю зачем. Но просто пусть будет. Кстати ты пидр.")
        else:
            send_message(chat_id, "Все равно пидр. Что бы ты ни написал - ты пидр.")

    return '', 200

def send_message(chat_id, text):
    url = BASE_URL + 'sendMessage'
    params = {'chat_id': chat_id, 'text': text}
    requests.post(url, json=params)

def send_audio(chat_id, audio_file_path):
    url = BASE_URL + 'sendAudio'
    files = {'audio': open(audio_file_path, 'rb')}
    params = {'chat_id': chat_id}
    requests.post(url, params=params, files=files)

def convert_youtube_to_m4a(chat_id, youtube_url):
    ydl_opts = {
        'format': 'm4a',
        'outtmpl': f'/home/David92/mysite/static/audio/%(title)s.%(ext)s',
        'force_ipv6': False,
        'verbose': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(youtube_url, download=False)
        video_url = info_dict['url']

        m4a_file_path = f'/home/David92/mysite/static/audio/{info_dict["title"]}.m4a'
        ydl.download([youtube_url])

        send_audio(chat_id, m4a_file_path)

if __name__ == '__main__':
    # Set up the webhook URL for Telegram
    webhook_url = f'https://podcast-telegram-bot.onrender.com/{TELEGRAM_API_TOKEN}'
    set_webhook_url = BASE_URL + 'setWebhook'
    params = {'url': webhook_url}
    requests.post(set_webhook_url, json=params)

    # Run the Flask app
    application.run()
