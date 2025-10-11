"""
Инициализация и запуск Telegram бота.
"""
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.handlers import start, order, upload, history, view, filter, menu
from database.crud import init_db
import config

logger = logging.getLogger(__name__)


async def main():
    """
    Главная функция запуска бота.
    """
    # Проверка токена
    if not config.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не установлен в .env файле")
        return
    
    # Инициализация базы данных
    logger.info("Инициализация базы данных...")
    await init_db()
    
    # Инициализация бота и диспетчера
    bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Настройка меню команд (левая панель в Telegram)
    from aiogram.types import BotCommand
    commands = [
        BotCommand(command="start", description="Главное меню"),
        BotCommand(command="newproject", description="Создать новый проект"),
        BotCommand(command="projects", description="Мои проекты"),
        BotCommand(command="help", description="Помощь и инструкции"),
    ]
    await bot.set_my_commands(commands)
    logger.info("Меню команд установлено")
    
    # Регистрация роутеров
    dp.include_router(start.router)
    dp.include_router(menu.router)
    dp.include_router(order.router)
    dp.include_router(upload.router)
    dp.include_router(history.router)
    dp.include_router(view.router)
    dp.include_router(filter.router)
    
    logger.info("Бот запущен")
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    asyncio.run(main())

