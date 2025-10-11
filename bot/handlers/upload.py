"""
Обработчики загрузки файлов.
"""
import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from database.crud import async_session_maker, get_project_by_id, create_upload
from bot.states import UploadStates
from bot.keyboards.inline import get_project_actions_keyboard
import config

router = Router()


@router.callback_query(F.data.startswith("upload_file:"))
async def start_upload(callback: CallbackQuery, state: FSMContext):
    """
    Начало загрузки файла.
    
    Args:
        callback: Callback запрос
        state: FSM состояние
    """
    project_id = int(callback.data.split(":")[1])
    
    await state.update_data(project_id=project_id)
    await state.set_state(UploadStates.waiting_for_file)
    
    await callback.message.answer(
        "Отправьте Excel файл (.xlsx или .xls) с прайс-листом."
    )
    await callback.answer()


@router.message(UploadStates.waiting_for_file, F.document)
async def process_file_upload(message: Message, state: FSMContext):
    """
    Обработка загруженного файла.
    
    Args:
        message: Входящее сообщение
        state: FSM состояние
    """
    document = message.document
    
    # Проверка типа файла
    if not document.file_name.endswith(('.xlsx', '.xls')):
        await message.answer(
            "Пожалуйста, отправьте файл в формате Excel (.xlsx или .xls)."
        )
        return
    
    data = await state.get_data()
    project_id = data.get('project_id')
    
    async with async_session_maker() as session:
        project = await get_project_by_id(session, project_id)
        if not project:
            await message.answer("Проект не найден.")
            await state.clear()
            return
        
        # Создание директории для проекта
        project_dir = config.PROJECTS_DIR / str(project_id)
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Сохранение файла
        file_path = project_dir / document.file_name
        await message.bot.download(document, destination=file_path)
        
        # Сохранение записи в БД
        await create_upload(session, project_id, document.file_name, str(file_path))
        
        await message.answer(
            f"Файл '{document.file_name}' успешно загружен!\n\n"
            f"Теперь вы можете запустить анализ.",
            reply_markup=get_project_actions_keyboard(project_id)
        )
    
    await state.clear()


@router.message(UploadStates.waiting_for_file)
async def wrong_file_type(message: Message):
    """
    Обработка неверного типа файла.
    
    Args:
        message: Входящее сообщение
    """
    await message.answer(
        "Пожалуйста, отправьте документ (Excel файл).\n"
        "Используйте скрепку для отправки файла."
    )

