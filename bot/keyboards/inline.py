"""
Inline клавиатуры для бота.
"""
from typing import List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_projects_keyboard(projects: List[tuple]) -> InlineKeyboardMarkup:
    """
    Создать клавиатуру со списком проектов.
    
    Args:
        projects: Список кортежей (project_id, project_name)
        
    Returns:
        InlineKeyboardMarkup: Клавиатура
    """
    builder = InlineKeyboardBuilder()
    
    for project_id, project_name in projects:
        builder.add(InlineKeyboardButton(
            text=project_name,
            callback_data=f"select_project:{project_id}"
        ))
    
    # Кнопка возврата
    builder.add(InlineKeyboardButton(
        text="Главное меню",
        callback_data="main_menu"
    ))
    
    builder.adjust(1)
    return builder.as_markup()


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Создать главное меню.
    
    Returns:
        InlineKeyboardMarkup: Клавиатура
    """
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(text="Новый проект", callback_data="new_project"))
    builder.add(InlineKeyboardButton(text="Мои проекты", callback_data="my_projects"))
    builder.add(InlineKeyboardButton(text="Помощь", callback_data="help"))
    
    builder.adjust(2, 1)
    return builder.as_markup()


def get_project_actions_keyboard(project_id: int) -> InlineKeyboardMarkup:
    """
    Создать клавиатуру с действиями для проекта.
    
    Args:
        project_id: ID проекта
        
    Returns:
        InlineKeyboardMarkup: Клавиатура
    """
    builder = InlineKeyboardBuilder()
    
    # Основные действия
    builder.add(InlineKeyboardButton(
        text="Загрузить файл",
        callback_data=f"upload_file:{project_id}"
    ))
    builder.add(InlineKeyboardButton(
        text="Анализировать",
        callback_data=f"analyze:{project_id}"
    ))
    builder.add(InlineKeyboardButton(
        text="Показать данные",
        callback_data=f"show_data:{project_id}"
    ))
    builder.add(InlineKeyboardButton(
        text="Сформировать заказ",
        callback_data=f"create_order:{project_id}"
    ))
    
    # Дополнительные действия
    builder.add(InlineKeyboardButton(
        text="Очистить данные",
        callback_data=f"clear_data:{project_id}"
    ))
    builder.add(InlineKeyboardButton(
        text="Удалить проект",
        callback_data=f"delete_project:{project_id}"
    ))
    
    # Навигация
    builder.add(InlineKeyboardButton(
        text="Назад",
        callback_data="back_to_projects"
    ))
    builder.add(InlineKeyboardButton(
        text="Главное меню",
        callback_data="main_menu"
    ))
    
    builder.adjust(1, 1, 1, 1, 2, 2)
    return builder.as_markup()


def get_confirmation_keyboard(action: str, project_id: int) -> InlineKeyboardMarkup:
    """
    Создать клавиатуру подтверждения действия.
    
    Args:
        action: Действие для подтверждения
        project_id: ID проекта
        
    Returns:
        InlineKeyboardMarkup: Клавиатура
    """
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="Да",
        callback_data=f"confirm_{action}:{project_id}"
    ))
    builder.add(InlineKeyboardButton(
        text="Нет",
        callback_data=f"select_project:{project_id}"
    ))
    
    builder.adjust(2)
    return builder.as_markup()
