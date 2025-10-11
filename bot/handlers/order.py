"""
Обработчики для работы с проектами.
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from database.crud import (
    async_session_maker,
    get_user_by_telegram_id,
    create_project,
    get_user_projects,
    get_project_by_id
)
from bot.states import ProjectStates
from bot.keyboards.inline import get_projects_keyboard, get_project_actions_keyboard

router = Router()


@router.callback_query(F.data == "new_project")
async def new_project_callback(callback: CallbackQuery, state: FSMContext):
    """
    Начало создания нового проекта.
    
    Args:
        callback: Callback запрос
        state: FSM состояние
    """
    await callback.message.edit_text(
        "Введите название нового проекта (например, название заказчика):"
    )
    await state.set_state(ProjectStates.waiting_for_project_name)
    await callback.answer()


@router.message(ProjectStates.waiting_for_project_name)
async def process_project_name(message: Message, state: FSMContext):
    """
    Обработка названия проекта.
    
    Args:
        message: Входящее сообщение
        state: FSM состояние
    """
    if not message.text:
        await message.answer("Название не может быть пустым. Попробуйте снова:")
        return
    
    project_name = message.text.strip()
    
    if not project_name:
        await message.answer("Название не может быть пустым. Попробуйте снова:")
        return
    
    async with async_session_maker() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)
        if user:
            project = await create_project(session, user.id, project_name)
            await message.answer(
                f"Проект '{project_name}' создан!\n\n"
                f"Что хотите сделать?",
                reply_markup=get_project_actions_keyboard(project.id)
            )
    
    await state.clear()


@router.callback_query(F.data == "my_projects")
async def my_projects_callback(callback: CallbackQuery):
    """
    Показать список проектов пользователя.
    
    Args:
        callback: Callback запрос
    """
    async with async_session_maker() as session:
        user = await get_user_by_telegram_id(session, callback.from_user.id)
        if user:
            projects = await get_user_projects(session, user.id)
            
            if not projects:
                await callback.message.edit_text(
                    "У вас пока нет проектов.\n"
                    "Создайте новый проект с помощью кнопки ниже."
                )
            else:
                projects_list = [(p.id, p.name) for p in projects]
                await callback.message.edit_text(
                    "Ваши проекты:",
                    reply_markup=get_projects_keyboard(projects_list)
                )
    
    await callback.answer()


@router.callback_query(F.data.startswith("select_project:"))
async def select_project(callback: CallbackQuery):
    """
    Выбор проекта из списка.
    
    Args:
        callback: Callback запрос
    """
    project_id = int(callback.data.split(":")[1])
    
    async with async_session_maker() as session:
        project = await get_project_by_id(session, project_id)
        if project:
            await callback.message.edit_text(
                f"Проект: {project.name}\n\n"
                f"Выберите действие:",
                reply_markup=get_project_actions_keyboard(project.id)
            )
    
    await callback.answer()


@router.callback_query(F.data == "back_to_projects")
async def back_to_projects(callback: CallbackQuery):
    """
    Возврат к списку проектов.
    
    Args:
        callback: Callback запрос
    """
    async with async_session_maker() as session:
        user = await get_user_by_telegram_id(session, callback.from_user.id)
        if user:
            projects = await get_user_projects(session, user.id)
            projects_list = [(p.id, p.name) for p in projects]
            await callback.message.edit_text(
                "Ваши проекты:",
                reply_markup=get_projects_keyboard(projects_list)
            )
    
    await callback.answer()

