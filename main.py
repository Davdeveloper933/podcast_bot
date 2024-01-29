from flask import Flask, request
from pydub import AudioSegment
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
import yt_dlp
import os
import io
import requests


app = Flask(__name__)

# Замените на свои данные
TELEGRAM_BOT_TOKEN = '6599078590:AAEN3AgDJD7KrZVcBvFwq9Av5L1pVqxa5WE'
WEBHOOK_URL = 'https://podcast-telegram-bot.onrender.com'
GOOGLE_DRIVE_FOLDER_ID = '1X3UDsSfzqsT44qrJe4YSAxnk36xTi4K-'

# Установка вебхука
def set_webhook():
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook'
    params = {
        'url': f'{WEBHOOK_URL}/webhook',
    }
    response = requests.get(url, params=params)
    return response.json()

# Аутентификация в Google Drive
def authenticate_google_drive():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json')
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', ['https://www.googleapis.com/auth/drive'])
            creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

# Загрузка аудио в Google Drive
def upload_audio_to_drive(audio_path, drive_folder_id):
    creds = authenticate_google_drive()
    drive_service = build('drive', 'v3', credentials=creds)

    file_metadata = {
        'name': os.path.basename(audio_path),
        'parents': [drive_folder_id],
    }
    media = MediaFileUpload(audio_path, mimetype='audio/mpeg')
    uploaded_file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()

    return uploaded_file['id']

# Обработка входящих обновлений
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    message = data.get('message')
    
    if message and message.get('text'):
        youtube_url = message['text']
        audio_path = download_and_convert_video(youtube_url)
        drive_file_id = upload_audio_to_drive(audio_path, GOOGLE_DRIVE_FOLDER_ID)
        send_audio_message(message['chat']['id'], drive_file_id)

    return '', 200

# Загрузка видео с YouTube и конвертация в аудио
def download_and_convert_video(youtube_url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': 'temp/%(title)s.%(ext)s',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=True)
        audio_path = f'temp/{info["title"]}.mp3'
    return audio_path

# Отправка аудио-сообщения пользователю
def send_audio_message(chat_id, drive_file_id):
    audio_url = f'https://drive.google.com/uc?id={drive_file_id}'
    audio_message = {
        'chat_id': chat_id,
        'audio': audio_url,
    }
    requests.post('https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendAudio', json=audio_message)

if __name__ == '__main__':
    set_webhook()
    app.run(port=int(os.environ.get('PORT', 5000)), debug=True)
