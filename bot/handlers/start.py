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
        "Отправьте Excel файл (.xlsx или .xls) с прайс-листом пива.\n\n"
        "Я помогу вам сформировать заказ:\n"
        "1. Парсинг файла\n"
        "2. Выбор позиций с количеством\n"
        "3. Получение готового Excel с заказом\n\n"
        "Просто отправьте файл для начала работы!"
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

**1. Загрузка файла:**
- Отправьте Excel файл (.xlsx или .xls) с прайс-листом
- Бот автоматически распарсит файл

**2. Выбор позиций:**
- Просмотрите список позиций с пагинацией
- Выберите нужные позиции:
  * `1 3 5` - выбрать позиции 1, 3, 5 (по 1 шт)
  * `1:10 3:5` - позиция 1 (10 шт), 3 (5 шт)

**3. Завершение заказа:**
- Нажмите "Завершить заказ"
- Получите Excel файл с новым листом "Заказ"

**Формат имени файла:**
`день|месяц|год-название_файла.xlsx`
Например: `15|10|2024-paradox_brewery.xlsx`

**Поддерживаемые данные:**
- Название напитка
- Пивоварня
- Стиль
- Объем (кеги, банки, бутылки)
- Цена
- Остаток в штуках

**Команды:**
/start - Начать работу
/help - Эта справка
"""
    
    await message.answer(
        help_text,
        parse_mode="Markdown"
    )

