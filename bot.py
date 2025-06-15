import os
import asyncio
from datetime import datetime
from telethon import TelegramClient, events, Button
from telethon.tl.functions.channels import GetFullChannelRequest, JoinChannelRequest
from telethon.tl.types import Channel, ChatAdminRights
from telethon.errors import ChannelPrivateError, ChatAdminRequiredError
from dotenv import load_dotenv
from database import Database
from sentiment_analyzer import SentimentAnalyzer

# Загрузка переменных окружения
load_dotenv()

# Инициализация клиента Telegram
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
bot_token = os.getenv('BOT_TOKEN')
webhook_url = os.getenv('WEBHOOK_URL', 'http://localhost:5000')

print(f"API_ID: {api_id}")
print(f"API_HASH: {api_hash}")
print(f"BOT_TOKEN: {bot_token}")
print(f"WEBHOOK_URL: {webhook_url}")

if not all([api_id, api_hash, bot_token]):
    print("Ошибка: Не все необходимые переменные окружения установлены!")
    exit(1)

client = TelegramClient('bot_session', api_id, api_hash)
db = Database()
sentiment_analyzer = SentimentAnalyzer()

# Создаем клавиатуру с основными командами
main_keyboard = [
    [Button.inline("📊 Мониторинг", b"monitor"),
     Button.inline("📝 Новый пост", b"new_post")],
    [Button.inline("📈 Статистика", b"stats"),
     Button.inline("😊 Анализ настроений", b"analyze")],
    [Button.inline("🔗 Статистика ссылок", b"link_stats")],
    [Button.inline("📢 Управление каналами", b"channels")],
    [Button.inline("❓ Помощь", b"help")]
]

@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    print(f"Получена команда /start от {event.sender_id}")
    welcome_text = """
🌟 *Добро пожаловать в SEO-оптимизатор!* 🌟

Я помогу вам оптимизировать работу с контентом в Telegram:
• 📊 Мониторинг активности групп
• 📝 Публикация постов с аналитикой
• 📈 Сбор статистики
• 😊 Анализ настроений аудитории
• 🔗 Отслеживание переходов по ссылкам

Выберите нужное действие на клавиатуре ниже 👇
    """
    await event.respond(welcome_text, buttons=main_keyboard, parse_mode='markdown')

@client.on(events.CallbackQuery(data=b"help"))
async def help_callback(event):
    help_text = """
📚 *Доступные команды:*

/monitor <group_id> - Начать мониторинг группы
/post <text> - Опубликовать новость
/stats - Показать статистику
/analyze - Анализ настроений
/link_stats - Статистика переходов по ссылкам

*Дополнительные функции:*
• Автоматическое сокращение ссылок
• Анализ настроений комментариев
• Мониторинг просмотров
• Статистика активности
• Отслеживание переходов по ссылкам
    """
    await event.respond(help_text, parse_mode='markdown', buttons=main_keyboard)

@client.on(events.CallbackQuery(data=b"link_stats"))
async def link_stats_callback(event):
    try:
        # Получаем последний пост
        last_post = db.session.query(Post).order_by(Post.id.desc()).first()
        if last_post:
            stats = db.get_link_statistics(last_post.id)
            stats_text = "📊 *Статистика переходов по ссылкам:*\n\n"
            for link in stats:
                stats_text += f"🔗 {link['original_url']}\n"
                stats_text += f"👥 Всего переходов: {link['clicks']}\n"
                stats_text += f"👤 Уникальных посетителей: {link['unique_ips']}\n"
                stats_text += f"🌐 Источники: {', '.join(set(link['referrers']))}\n\n"
            await event.respond(stats_text, parse_mode='markdown', buttons=main_keyboard)
        else:
            await event.respond("❌ Нет доступной статистики по ссылкам", buttons=main_keyboard)
    except Exception as e:
        print(f"Ошибка при получении статистики ссылок: {e}")
        await event.respond("❌ Ошибка при получении статистики", buttons=main_keyboard)

@client.on(events.CallbackQuery(data=b"monitor"))
async def monitor_callback(event):
    await event.respond("Введите ID группы для мониторинга в формате:\n/monitor group_id", buttons=main_keyboard)

@client.on(events.CallbackQuery(data=b"new_post"))
async def new_post_callback(event):
    await event.respond("Введите текст поста в формате:\n/post ваш_текст", buttons=main_keyboard)

@client.on(events.CallbackQuery(data=b"stats"))
async def stats_callback(event):
    stats = db.get_statistics()
    await event.respond(f"📊 *Статистика:*\n{stats}", parse_mode='markdown', buttons=main_keyboard)

@client.on(events.CallbackQuery(data=b"analyze"))
async def analyze_callback(event):
    comments = db.get_recent_comments()
    analysis = sentiment_analyzer.analyze_batch(comments)
    await event.respond(f"😊 *Анализ настроений:*\n{analysis}", parse_mode='markdown', buttons=main_keyboard)

async def monitor_group(group_id):
    while True:
        try:
            channel = await client.get_entity(group_id)
            full_channel = await client(GetFullChannelRequest(channel=channel))
            members_count = full_channel.full_chat.participants_count
            
            # Сохраняем данные в БД
            db.save_members_count(group_id, members_count, datetime.now())
            print(f"Обновлена статистика группы {group_id}: {members_count} участников")
            
            await asyncio.sleep(300)  # Пауза 5 минут
        except Exception as e:
            print(f"Ошибка при мониторинге группы: {e}")
            await asyncio.sleep(60)

@client.on(events.NewMessage(pattern='/monitor'))
async def monitor_handler(event):
    print(f"Получена команда /monitor от {event.sender_id}")
    try:
        group_id = event.text.split()[1]
        await event.respond(f"🔄 Начинаю мониторинг группы {group_id}", buttons=main_keyboard)
        asyncio.create_task(monitor_group(group_id))
    except IndexError:
        await event.respond("❌ Пожалуйста, укажите ID группы", buttons=main_keyboard)

@client.on(events.NewMessage(pattern='/post'))
async def post_handler(event):
    print(f"Получена команда /post от {event.sender_id}")
    try:
        text = event.text.split(maxsplit=1)[1]
        # Находим все ссылки в тексте
        links = [word for word in text.split() if word.startswith('http')]
        
        # Сохраняем пост в БД
        post_id = db.save_post(text, datetime.now())
        
        # Создаем короткие ссылки для каждой найденной ссылки
        for link in links:
            short_id = db.create_short_link(post_id, link)
            short_url = f"{webhook_url}/track/{short_id}"
            text = text.replace(link, short_url)
        
        await event.respond(f"✅ Пост опубликован!\nID: {post_id}\n\n{text}", buttons=main_keyboard)
    except IndexError:
        await event.respond("❌ Пожалуйста, укажите текст поста", buttons=main_keyboard)

@client.on(events.NewMessage(pattern='/stats'))
async def stats_handler(event):
    print(f"Получена команда /stats от {event.sender_id}")
    stats = db.get_statistics()
    await event.respond(f"📊 *Статистика:*\n{stats}", parse_mode='markdown', buttons=main_keyboard)

@client.on(events.NewMessage(pattern='/analyze'))
async def analyze_handler(event):
    print(f"Получена команда /analyze от {event.sender_id}")
    comments = db.get_recent_comments()
    analysis = sentiment_analyzer.analyze_batch(comments)
    await event.respond(f"😊 *Анализ настроений:*\n{analysis}", parse_mode='markdown', buttons=main_keyboard)

@client.on(events.CallbackQuery(data=b"channels"))
async def channels_callback(event):
    channels = db.get_active_channels()
    if not channels:
        await event.respond("❌ Нет активных каналов", buttons=main_keyboard)
        return

    text = "📢 *Ваши каналы:*\n\n"
    for channel in channels:
        text += f"• {channel.title} (@{channel.username})\n"
    
    text += "\nВыберите действие:"
    buttons = [
        [Button.inline("➕ Добавить канал", b"add_channel")],
        [Button.inline("📊 Статистика канала", b"channel_stats")],
        [Button.inline("📝 Пост в канал", b"post_to_channel")],
        [Button.inline("🔙 Назад", b"back_to_main")]
    ]
    await event.respond(text, parse_mode='markdown', buttons=buttons)

@client.on(events.CallbackQuery(data=b"add_channel"))
async def add_channel_callback(event):
    await event.respond(
        "Для добавления канала:\n"
        "1. Добавьте бота администратором в канал\n"
        "2. Отправьте ссылку на канал в формате:\n"
        "/add_channel @username_канала",
        buttons=main_keyboard
    )

@client.on(events.NewMessage(pattern='/add_channel'))
async def add_channel_handler(event):
    try:
        channel_username = event.text.split()[1].strip('@')
        # Пробуем получить информацию о канале
        channel = await client.get_entity(channel_username)
        
        if not isinstance(channel, Channel):
            await event.respond("❌ Это не канал!", buttons=main_keyboard)
            return

        # Проверяем права бота
        try:
            await client.get_permissions(channel)
        except (ChannelPrivateError, ChatAdminRequiredError):
            await event.respond(
                "❌ Бот должен быть администратором канала!\n"
                "Добавьте бота администратором и попробуйте снова.",
                buttons=main_keyboard
            )
            return

        # Добавляем канал в базу данных
        db.add_channel(
            channel_id=str(channel.id),
            title=channel.title,
            username=channel_username
        )

        await event.respond(
            f"✅ Канал {channel.title} успешно добавлен!",
            buttons=main_keyboard
        )
    except Exception as e:
        print(f"Ошибка при добавлении канала: {e}")
        await event.respond(
            "❌ Ошибка при добавлении канала. Проверьте правильность ссылки.",
            buttons=main_keyboard
        )

@client.on(events.CallbackQuery(data=b"channel_stats"))
async def channel_stats_callback(event):
    channels = db.get_active_channels()
    if not channels:
        await event.respond("❌ Нет активных каналов", buttons=main_keyboard)
        return

    buttons = []
    for channel in channels:
        buttons.append([Button.inline(f"📊 {channel.title}", f"stats_{channel.channel_id}")])
    buttons.append([Button.inline("🔙 Назад", b"channels")])
    
    await event.respond("Выберите канал для просмотра статистики:", buttons=buttons)

@client.on(events.CallbackQuery(pattern=b"stats_"))
async def show_channel_stats(event):
    channel_id = event.data.decode().split('_')[1]
    stats = db.get_channel_statistics(channel_id)
    
    if not stats:
        await event.respond("❌ Статистика недоступна", buttons=main_keyboard)
        return

    # Основная статистика
    text = f"""
📊 *Статистика канала {stats['channel_title']} (@{stats['username']})*
📅 За последние {stats['period_days']} дней

📝 *Общая статистика:*
• Всего постов: {stats['total_posts']}
• Всего просмотров: {stats['total_views']}
• Среднее количество просмотров: {int(stats['average_views'])}
• Последний пост: {stats['last_post_date'].strftime('%d.%m.%Y %H:%M') if stats['last_post_date'] else 'Нет постов'}

⏰ *Лучшее время для постинга:* {stats['best_posting_hour']}:00

📈 *Топ постов:*
"""
    
    # Добавляем топ постов
    for i, post in enumerate(stats['top_posts'], 1):
        text += f"\n{i}. {post['text']}\n"
        text += f"   👁 {post['views']} просмотров • {post['date'].strftime('%d.%m.%Y')}\n"

    # Добавляем статистику по дням
    text += "\n📅 *Статистика по дням:*\n"
    for day, day_stats in sorted(stats['daily_stats'].items(), reverse=True)[:7]:  # Показываем последние 7 дней
        text += f"• {day.strftime('%d.%m')}: {day_stats['posts']} постов, {day_stats['views']} просмотров\n"

    # Добавляем кнопки для дополнительной статистики
    buttons = [
        [Button.inline("🔗 Статистика ссылок", f"link_stats_{channel_id}")],
        [Button.inline("📊 За 7 дней", f"stats_7_{channel_id}"),
         Button.inline("📊 За 30 дней", f"stats_30_{channel_id}")],
        [Button.inline("🔙 Назад", b"channels")]
    ]
    
    await event.respond(text, parse_mode='markdown', buttons=buttons)

@client.on(events.CallbackQuery(pattern=b"stats_\d+_"))
async def show_channel_stats_period(event):
    try:
        period, channel_id = event.data.decode().split('_')[1:]
        stats = db.get_channel_statistics(channel_id, days=int(period))
        await show_channel_stats(event)
    except Exception as e:
        print(f"Ошибка при получении статистики: {e}")
        await event.respond("❌ Ошибка при получении статистики", buttons=main_keyboard)

@client.on(events.CallbackQuery(pattern=b"link_stats_"))
async def show_channel_link_stats(event):
    channel_id = event.data.decode().split('_')[2]
    stats = db.get_channel_link_statistics(channel_id)
    
    if not stats:
        await event.respond("❌ Статистика ссылок недоступна", buttons=main_keyboard)
        return

    text = f"""
🔗 *Статистика ссылок канала {stats['channel_title']}*

📊 *Общая статистика:*
• Всего ссылок: {stats['total_links']}
• Всего переходов: {stats['total_clicks']}

📈 *Топ ссылок:*
"""
    
    # Добавляем топ ссылок
    for i, link in enumerate(stats['top_links'], 1):
        text += f"\n{i}. {link['original_url']}\n"
        text += f"   👥 {link['clicks']} переходов • {link['unique_ips']} уникальных посетителей\n"
        text += f"   📝 Пост: {link['post_text']}\n"
        text += f"   📅 {link['post_date'].strftime('%d.%m.%Y')}\n"

    buttons = [
        [Button.inline("📊 Общая статистика", f"stats_{channel_id}")],
        [Button.inline("🔙 Назад", b"channels")]
    ]
    
    await event.respond(text, parse_mode='markdown', buttons=buttons)

@client.on(events.CallbackQuery(data=b"post_to_channel"))
async def post_to_channel_callback(event):
    channels = db.get_active_channels()
    if not channels:
        await event.respond("❌ Нет активных каналов", buttons=main_keyboard)
        return

    buttons = []
    for channel in channels:
        buttons.append([Button.inline(f"📝 {channel.title}", f"post_{channel.channel_id}")])
    buttons.append([Button.inline("🔙 Назад", b"channels")])
    
    await event.respond("Выберите канал для публикации:", buttons=buttons)

@client.on(events.CallbackQuery(pattern=b"post_"))
async def prepare_channel_post(event):
    channel_id = event.data.decode().split('_')[1]
    await event.respond(
        f"Введите текст поста в формате:\n"
        f"/post_to {channel_id} ваш_текст",
        buttons=main_keyboard
    )

@client.on(events.NewMessage(pattern='/post_to'))
async def post_to_channel_handler(event):
    try:
        _, channel_id, *text_parts = event.text.split(maxsplit=2)
        if not text_parts:
            await event.respond("❌ Укажите текст поста", buttons=main_keyboard)
            return

        text = text_parts[0]
        channel = db.get_channel(channel_id)
        if not channel:
            await event.respond("❌ Канал не найден", buttons=main_keyboard)
            return

        # Находим все ссылки в тексте
        links = [word for word in text.split() if word.startswith('http')]
        
        # Создаем короткие ссылки для каждой найденной ссылки
        for link in links:
            short_id = db.create_short_link(None, link)
            short_url = f"{webhook_url}/track/{short_id}"
            text = text.replace(link, short_url)

        # Публикуем пост в канал
        message = await client.send_message(channel.username, text)
        
        # Сохраняем пост в базу данных
        post_id = db.save_post(
            text=text,
            timestamp=datetime.now(),
            channel_id=channel.id,
            message_id=message.id
        )

        await event.respond(
            f"✅ Пост успешно опубликован в канал {channel.title}!",
            buttons=main_keyboard
        )
    except Exception as e:
        print(f"Ошибка при публикации в канал: {e}")
        await event.respond(
            "❌ Ошибка при публикации поста",
            buttons=main_keyboard
        )

@client.on(events.CallbackQuery(data=b"back_to_main"))
async def back_to_main_callback(event):
    await event.respond("Главное меню:", buttons=main_keyboard)

async def main():
    print("Запуск бота...")
    await client.start(bot_token=bot_token)
    print("Бот успешно запущен!")
    print("Используйте Ctrl+C для остановки")
    await client.run_until_disconnected()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nБот остановлен")
    except Exception as e:
        print(f"Произошла ошибка: {e}") 