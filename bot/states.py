"""
FSM состояния для диалогов бота.
"""
from aiogram.fsm.state import State, StatesGroup


class QuickOrderStates(StatesGroup):
    """Состояния быстрого заказа."""
    waiting_for_quantities = State()
    viewing_page = State()
    selecting_quantity = State()  # Новое состояние для выбора количества
    searching = State()  # Поиск по названию
    viewing_cart = State()  # Просмотр корзины
    editing_cart_item = State()  # Редактирование позиции в корзине


class ProjectStates(StatesGroup):
    """Состояния для работы с проектами."""
    
    waiting_for_project_name = State()
    selecting_project = State()


class UploadStates(StatesGroup):
    """Состояния для загрузки файлов."""
    
    waiting_for_file = State()

