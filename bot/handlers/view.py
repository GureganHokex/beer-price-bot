"""
Обработчик просмотра данных.
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, BufferedInputFile
from database.crud import async_session_maker, get_project_by_id, get_project_beer_items
from core.order_builder import build_text_report
from bot.keyboards.inline import get_project_actions_keyboard

router = Router()


@router.callback_query(F.data.startswith("show_data:"))
async def show_data(callback: CallbackQuery):
    """
    Показать данные проекта.
    
    Args:
        callback: Callback запрос
    """
    project_id = int(callback.data.split(":")[1])
    
    async with async_session_maker() as session:
        project = await get_project_by_id(session, project_id)
        if not project:
            await callback.message.edit_text("Проект не найден.")
            await callback.answer()
            return
        
        beer_items = await get_project_beer_items(session, project_id)
        
        if not beer_items:
            await callback.message.edit_text(
                "В проекте пока нет данных.\n"
                "Загрузите файлы и запустите анализ.",
                reply_markup=get_project_actions_keyboard(project_id)
            )
            await callback.answer()
            return
        
        # Формирование ПОЛНОГО списка для всех позиций
        import json
        all_items_for_report = []
        for item in beer_items:  # ВСЕ позиции
            # Извлекаем остаток из raw_data (JSON) - может быть число или текст
            stock = None
            if item.raw_data:
                try:
                    raw = json.loads(item.raw_data)
                    stock = raw.get('остаток')
                except:
                    pass
            
            all_items_for_report.append({
                'пивоварня': item.brewery,
                'название': item.name,
                'стиль': item.style,
                'объем': item.volume,
                'цена': item.price,
                'остаток': stock
            })
        
        # Полный отчет для .txt файла
        full_report = build_text_report(all_items_for_report)
        
        # Группируем по названию для подсчета уникальных
        from collections import defaultdict
        grouped = defaultdict(list)
        for item in all_items_for_report:
            name = item.get('название')
            grouped[name].append(item)
        
        # Статистика по таре
        kegs = [i for i in all_items_for_report if 'кег' in str(i.get('объем', '')).lower()]
        bottles = [i for i in all_items_for_report if 'бутылка' in str(i.get('объем', '')).lower()]
        cans = [i for i in all_items_for_report if 'банка' in str(i.get('объем', '')).lower()]
        
        # Краткое сообщение в чат (БЕЗ списка позиций)
        message = (
            f"Найдено позиций: {len(beer_items)}\n"
            f"Уникальных сортов: {len(grouped)}\n\n"
            f"По типу тары:\n"
            f"Кеги: {len(kegs)} шт\n"
            f"Бутылки: {len(bottles)} шт\n"
            f"Банки: {len(cans)} шт\n\n"
            f"Полный список в файле ниже"
        )
        
        await callback.message.edit_text(
            message,
            reply_markup=get_project_actions_keyboard(project_id)
        )
        
        # Отправляем .txt файл со ВСЕМИ позициями
        txt_content = full_report.encode('utf-8')
        txt_file = BufferedInputFile(
            txt_content,
            filename=f"{project.name}_позиции.txt"
        )
        await callback.message.answer_document(
            txt_file,
            caption=f"Полный список всех позиций: {len(beer_items)} шт"
        )
    
    await callback.answer()

