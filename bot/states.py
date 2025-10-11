"""
FSM состояния для диалогов бота.
"""
from aiogram.fsm.state import State, StatesGroup


class ProjectStates(StatesGroup):
    """Состояния для работы с проектами."""
    
    waiting_for_project_name = State()
    selecting_project = State()


class UploadStates(StatesGroup):
    """Состояния для загрузки файлов."""
    
    waiting_for_file = State()

