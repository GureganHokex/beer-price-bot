"""
Обработчик анализа данных.
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile
from database.crud import (
    async_session_maker,
    get_project_by_id,
    get_project_uploads,
    clear_project_beer_items,
    create_beer_item
)
from core.parser import ExcelParser
from core.order_builder import build_json, build_summary
from bot.keyboards.inline import get_project_actions_keyboard
import config

router = Router()


@router.callback_query(F.data.startswith("analyze:"))
async def analyze_project(callback: CallbackQuery):
    """
    Анализ всех файлов в проекте.
    
    Args:
        callback: Callback запрос
    """
    project_id = int(callback.data.split(":")[1])
    
    await callback.message.edit_text("Анализирую файлы...")
    
    async with async_session_maker() as session:
        project = await get_project_by_id(session, project_id)
        if not project:
            await callback.message.edit_text("Проект не найден.")
            await callback.answer()
            return
        
        uploads = await get_project_uploads(session, project_id)
        
        if not uploads:
            await callback.message.edit_text(
                "В проекте нет загруженных файлов.\n"
                "Сначала загрузите Excel файлы.",
                reply_markup=get_project_actions_keyboard(project_id)
            )
            await callback.answer()
            return
        
        # Очистка старых данных
        await clear_project_beer_items(session, project_id)
        
        # Парсинг всех файлов
        parser = ExcelParser(auto_learn=True)
        all_items = []
        
        for upload in uploads:
            try:
                items = parser.parse_file(upload.path)
                all_items.extend(items)
                
                # Сохранение в БД
                for item in items:
                    await create_beer_item(
                        session,
                        project_id=project_id,
                        brewery=item.get('пивоварня'),
                        name=item.get('название'),
                        style=item.get('стиль'),
                        volume=item.get('объем'),
                        price=item.get('цена'),
                        raw_data=item
                    )
            except Exception as e:
                await callback.message.answer(
                    f"Ошибка при обработке файла {upload.filename}: {str(e)}"
                )
        
        # Автоматическое обучение ML-модели на новых данных
        try:
            parser.save_learned_data()
        except Exception as e:
            print(f"Предупреждение: не удалось обучить модель: {e}")
        
        # Формирование отчета
        summary = build_summary(all_items)
        
        # Сохранение JSON (только локально, не отправляем пользователю)
        json_path = config.PROJECTS_DIR / str(project_id) / "result.json"
        build_json(all_items, str(json_path))
        
        await callback.message.edit_text(
            f"Анализ завершен!\n\n"
            f"Найдено позиций: {summary['total_items']}\n"
            f"Пивоварен: {len(summary['breweries'])}\n"
            f"Стилей: {len(summary['styles'])}\n\n"
            f"Результаты сохранены.",
            reply_markup=get_project_actions_keyboard(project_id)
        )
    
    await callback.answer()

