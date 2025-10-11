"""
Обработчики для главного меню и навигации.
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.filters import Command
from aiogram.types import Message

from bot.keyboards.inline import get_main_menu_keyboard, get_projects_keyboard, get_project_actions_keyboard, get_confirmation_keyboard
from database.crud import get_user_projects

router = Router()


@router.callback_query(F.data == "main_menu")
async def main_menu(callback: CallbackQuery):
    """Показать главное меню."""
    await callback.message.edit_text(
        "Главное меню\n\nВыберите действие:",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_projects")
async def back_to_projects(callback: CallbackQuery):
    """Вернуться к списку проектов."""
    user_id = callback.from_user.id
    
    projects = await get_user_projects(user_id)
    
    if not projects:
        await callback.message.edit_text(
            "У вас пока нет проектов.\n\n"
            "Создайте новый проект для начала работы.",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        projects_list = [(p.id, p.name) for p in projects]
        await callback.message.edit_text(
            f"Ваши проекты ({len(projects)}):\n\n"
            "Выберите проект для работы:",
            reply_markup=get_projects_keyboard(projects_list)
        )
    
    await callback.answer()


@router.callback_query(F.data == "help")
async def show_help(callback: CallbackQuery):
    """Показать помощь."""
    help_text = """
**Инструкция по использованию бота**

**1. Создание проекта:**
- Нажмите "Новый проект"
- Введите название проекта (например, "CBD", "Beeribo")

**2. Загрузка файлов:**
- Откройте проект
- Нажмите "Загрузить файл"
- Отправьте Excel файл (.xlsx или .xls)

**3. Анализ данных:**
- Нажмите "Анализировать"
- Бот автоматически обработает все файлы
- ML-модель определит колонки и извлечет данные

**4. Просмотр результатов:**
- Нажмите "Показать данные"
- Получите статистику в чат
- Скачайте полный список в .txt файле

**Поддерживаемые данные:**
- Название пива/напитка
- Пивоварня
- Стиль
- Объем (кеги, банки, бутылки)
- Цена
- Остаток в штуках

**Фильтрация:**
- Банки/бутылки: показываются только при остатке >= 10 шт
- Кеги: показываются всегда, без ограничений

**Управление:**
- Очистить данные: удалить результаты анализа
- Удалить проект: удалить проект и все файлы
"""
    
    await callback.message.edit_text(
        help_text,
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("clear_data:"))
async def clear_data_confirmation(callback: CallbackQuery):
    """Запросить подтверждение очистки данных."""
    project_id = int(callback.data.split(":")[1])
    
    await callback.message.edit_text(
        "Вы уверены, что хотите очистить все данные проекта?\n\n"
        "Это удалит результаты анализа, но сохранит загруженные файлы.",
        reply_markup=get_confirmation_keyboard("clear_data", project_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_clear_data:"))
async def confirm_clear_data(callback: CallbackQuery):
    """Подтвердить очистку данных."""
    from database.crud import delete_beer_items_by_project
    
    project_id = int(callback.data.split(":")[1])
    
    # Удаляем данные
    deleted = await delete_beer_items_by_project(project_id)
    
    await callback.message.edit_text(
        f"Данные очищены. Удалено позиций: {deleted}\n\n"
        "Вы можете загрузить новые файлы или повторить анализ.",
        reply_markup=get_project_actions_keyboard(project_id)
    )
    await callback.answer("Данные очищены")


@router.callback_query(F.data.startswith("delete_project:"))
async def delete_project_confirmation(callback: CallbackQuery):
    """Запросить подтверждение удаления проекта."""
    project_id = int(callback.data.split(":")[1])
    
    await callback.message.edit_text(
        "Вы уверены, что хотите удалить проект?\n\n"
        "Это удалит:\n"
        "- Все загруженные файлы\n"
        "- Все результаты анализа\n"
        "- Сам проект\n\n"
        "Это действие необратимо!",
        reply_markup=get_confirmation_keyboard("delete_project", project_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_delete_project:"))
async def confirm_delete_project(callback: CallbackQuery):
    """Подтвердить удаление проекта."""
    from database.crud import delete_project
    import shutil
    from pathlib import Path
    
    project_id = int(callback.data.split(":")[1])
    
    # Удаляем файлы проекта
    project_dir = Path(f"data/projects/{project_id}")
    if project_dir.exists():
        shutil.rmtree(project_dir)
    
    # Удаляем проект из БД
    await delete_project(project_id)
    
    await callback.message.edit_text(
        "Проект удален.\n\n"
        "Выберите другой проект или создайте новый.",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer("Проект удален")

