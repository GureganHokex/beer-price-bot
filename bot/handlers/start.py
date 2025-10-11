"""
Обработчик команды /start и основных команд.
"""
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from database.crud import async_session_maker, get_or_create_user, get_user_projects
from bot.keyboards.inline import get_main_menu_keyboard, get_projects_keyboard

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """
    Обработка команды /start.
    
    Args:
        message: Входящее сообщение
    """
    async with async_session_maker() as session:
        await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            username=message.from_user.username
        )
    
    await message.answer(
        "Добро пожаловать в Beer Price Bot!\n\n"
        "Я помогу проанализировать прайс-листы пива от разных поставщиков.\n\n"
        "Что вы хотите сделать?",
        reply_markup=get_main_menu_keyboard()
    )


@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    """
    Возврат в главное меню.
    
    Args:
        callback: Callback запрос
    """
    await callback.message.edit_text(
        "Что вы хотите сделать?",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()


@router.message(Command("newproject"))
async def cmd_newproject(message: Message):
    """
    Обработка команды /newproject.
    
    Args:
        message: Входящее сообщение
    """
    from bot.states import CreateProject
    from aiogram.fsm.context import FSMContext
    
    await message.answer(
        "Создание нового проекта\n\n"
        "Введите название проекта:",
        reply_markup=get_main_menu_keyboard()
    )


@router.message(Command("projects"))
async def cmd_projects(message: Message):
    """
    Обработка команды /projects.
    
    Args:
        message: Входящее сообщение
    """
    user_id = message.from_user.id
    
    async with async_session_maker() as session:
        projects = await get_user_projects(session, user_id)
    
    if not projects:
        await message.answer(
            "У вас пока нет проектов.\n\n"
            "Создайте новый проект для начала работы.",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        projects_list = [(p.id, p.name) for p in projects]
        await message.answer(
            f"Ваши проекты ({len(projects)}):\n\n"
            "Выберите проект для работы:",
            reply_markup=get_projects_keyboard(projects_list)
        )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """
    Обработка команды /help.
    
    Args:
        message: Входящее сообщение
    """
    help_text = """
**Инструкция по использованию бота**

**1. Создание проекта:**
- Команда /newproject или кнопка "Новый проект"
- Введите название проекта

**2. Загрузка файлов:**
- Откройте проект
- Нажмите "Загрузить файл"
- Отправьте Excel файл (.xlsx или .xls)

**3. Анализ данных:**
- Нажмите "Анализировать"
- Бот обработает все файлы автоматически

**4. Просмотр результатов:**
- Нажмите "Показать данные"
- Получите статистику и .txt файл

**Поддерживаемые данные:**
- Название напитка
- Пивоварня
- Стиль
- Объем (кеги, банки, бутылки)
- Цена
- Остаток в штуках

**Фильтрация:**
- Банки и бутылки: остаток >= 10 штук
- Кеги: показываются всегда

**Команды:**
/start - Главное меню
/newproject - Создать проект
/projects - Мои проекты
/help - Эта справка
"""
    
    await message.answer(
        help_text,
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard()
    )

