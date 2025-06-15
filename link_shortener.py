import pyshorteners
import os
from dotenv import load_dotenv

load_dotenv()

class LinkShortener:
    def __init__(self):
        self.shortener = pyshorteners.Shortener()
        # Можно использовать разные сервисы для сокращения ссылок
        self.bitly_token = os.getenv('BITLY_TOKEN')
        if self.bitly_token:
            self.shortener = pyshorteners.Shortener(api_key=self.bitly_token)

    def shorten(self, url):
        try:
            # Пробуем использовать Bitly, если есть токен
            if self.bitly_token:
                return self.shortener.bitly.short(url)
            # Иначе используем TinyURL
            return self.shortener.tinyurl.short(url)
        except Exception as e:
            print(f"Ошибка при сокращении ссылки: {e}")
            return url  # Возвращаем оригинальную ссылку в случае ошибки 