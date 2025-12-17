import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

flask_app = None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Простой старт бота"""
    await update.message.reply_text("🤖 Бот ReqImple\n/ideas - идеи\nОтправь: название|описание")


async def ideas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать последние идеи"""
    if not flask_app:
        await update.message.reply_text("❌ Нет подключения")
        return

    try:
        with flask_app.app_context():
            from app.models import Idea
            ideas_list = Idea.query.filter_by(status='active').limit(5).all()

            if not ideas_list:
                await update.message.reply_text("📭 Идей нет")
                return

            text = "🔥 Идеи:\n"
            for idea in ideas_list:
                text += f"\n• {idea.title}\n👤 {idea.author.username}\n"

            await update.message.reply_text(text)
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await update.message.reply_text("❌ Ошибка")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик создания идеи"""
    text = update.message.text

    if '|' not in text:
        await update.message.reply_text("Используй: название|описание")
        return

    try:
        title, description = text.split('|', 1)
        title, description = title.strip(), description.strip()

        if not flask_app:
            await update.message.reply_text("❌ Нет подключения")
            return

        with flask_app.app_context():
            from app.models import User, Idea, db

            user_id = update.message.from_user.id
            username = f"bot_{user_id}"

            user = User.query.filter_by(username=username).first()
            if not user:
                user = User(
                    email=f"{username}@telegram",
                    username=username,
                    display_name=update.message.from_user.first_name or "User",
                    is_admin=False
                )
                user.set_password("telegram")
                db.session.add(user)
                db.session.commit()

            idea = Idea(
                title=title,
                description=description,
                author=user,
                status='active'
            )
            db.session.add(idea)
            db.session.commit()

            await update.message.reply_text(f"✅ Идея: {title}")

    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await update.message.reply_text("❌ Ошибка")


def run_bot_with_app(app_instance):
    """Запуск бота с Flask"""
    global flask_app
    flask_app = app_instance

    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print("❌ Нет токена бота")
        return

    try:
        # Создаем и настраиваем бота
        application = Application.builder().token(token).build()

        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("ideas", ideas))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

        print("🤖 Telegram бот запущен")

        # Запускаем бота с правильным event loop
        import asyncio

        # Для Python 3.13+ нужно явно создать event loop
        if hasattr(asyncio, 'WindowsSelectorEventLoopPolicy'):
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(application.run_polling())
        except KeyboardInterrupt:
            print("\n🛑 Бот остановлен")
        finally:
            loop.close()

    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")