from flask import Flask, request, redirect
from database import Database
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
db = Database()

@app.route('/track/<short_id>')
def track_link(short_id):
    try:
        # Получаем информацию о клике
        user_agent = request.headers.get('User-Agent', 'Unknown')
        ip_address = request.remote_addr
        referrer = request.headers.get('Referer', 'Direct')
        
        # Получаем оригинальную ссылку из базы данных
        link_data = db.get_link_by_short_id(short_id)
        if not link_data:
            return "Link not found", 404
            
        # Сохраняем информацию о клике
        db.save_link_click(
            original_url=link_data['original_url'],
            short_url=f"/track/{short_id}",
            post_id=link_data['post_id'],
            user_agent=user_agent,
            ip_address=ip_address,
            referrer=referrer
        )
        
        # Перенаправляем на оригинальную ссылку
        return redirect(link_data['original_url'])
    except Exception as e:
        print(f"Ошибка при обработке клика: {e}")
        return "Error", 500

if __name__ == '__main__':
    port = int(os.getenv('WEBHOOK_PORT', 5000))
    app.run(host='0.0.0.0', port=port) 