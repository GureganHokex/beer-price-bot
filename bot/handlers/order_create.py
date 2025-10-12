"""
Обработчики для формирования заказа.
"""
from datetime import datetime
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message, BufferedInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from collections import defaultdict

from database.crud import (
    get_or_create_order, get_project_beer_items,
    add_item_to_order, get_order_items,
    remove_item_from_order, clear_order, async_session_maker
)
from core.beer_categories import get_category_for_style, get_categories_list
from bot.keyboards.inline import get_project_actions_keyboard

router = Router()


class OrderCreation(StatesGroup):
    """Состояния для создания заказа."""
    selecting_items = State()
    current_project_id = State()
    current_category = State()
    items_list = State()


async def get_breweries_keyboard(project_id: int, container_filter: str = "all") -> InlineKeyboardMarkup:
    """Создать клавиатуру со списком пивоварен для выбранного типа тары."""
    builder = InlineKeyboardBuilder()
    
    # Получаем список пивоварен из проекта
    async with async_session_maker() as session:
        from database.crud import get_project_beer_items
        beer_items = await get_project_beer_items(session, project_id)
    
    # Собираем уникальные пивоварни с учетом фильтра по таре
    breweries = set()
    for item in beer_items:
        if item.brewery:
            # Применяем фильтр по таре
            if container_filter != "all":
                volume_lower = str(item.volume).lower() if item.volume else ""
                if container_filter == "kegs" and "кег" not in volume_lower:
                    continue
                elif container_filter == "cans" and "банка" not in volume_lower:
                    continue
                elif container_filter == "bottles" and "бутылка" not in volume_lower:
                    continue
            
            breweries.add(item.brewery)
    
    # Сортируем по алфавиту
    for brewery in sorted(breweries):
        builder.add(InlineKeyboardButton(
            text=brewery,
            callback_data=f"brewery:{project_id}:{brewery}:{container_filter}"
        ))
    
    builder.add(InlineKeyboardButton(
        text="Назад к выбору тары",
        callback_data=f"create_order:{project_id}"
    ))
    builder.add(InlineKeyboardButton(
        text="Посмотреть заказ",
        callback_data=f"view_order:{project_id}:all"
    ))
    
    builder.adjust(2, 2, 2, 2, 2, 1, 1)
    return builder.as_markup()


def get_back_to_categories_keyboard(project_id: int) -> InlineKeyboardMarkup:
    """Создать клавиатуру с кнопкой возврата."""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="Назад к пивоварням",
        callback_data=f"create_order:{project_id}"
    ))
    builder.add(InlineKeyboardButton(
        text="Посмотреть заказ",
        callback_data=f"view_order:{project_id}:all"
    ))
    
    builder.adjust(2)
    return builder.as_markup()


def get_order_view_keyboard(project_id: int, order_id: int, current_filter: str = "all") -> InlineKeyboardMarkup:
    """Создать клавиатуру для просмотра заказа."""
    builder = InlineKeyboardBuilder()
    
    # Кнопки фильтрации
    builder.add(InlineKeyboardButton(
        text="Все" if current_filter == "all" else "• Все",
        callback_data=f"view_order:{project_id}:all"
    ))
    builder.add(InlineKeyboardButton(
        text="Кеги" if current_filter == "kegs" else "• Кеги",
        callback_data=f"view_order:{project_id}:kegs"
    ))
    builder.add(InlineKeyboardButton(
        text="Банки" if current_filter == "cans" else "• Банки",
        callback_data=f"view_order:{project_id}:cans"
    ))
    builder.add(InlineKeyboardButton(
        text="Бутылки" if current_filter == "bottles" else "• Бутылки",
        callback_data=f"view_order:{project_id}:bottles"
    ))
    
    # Управление заказом
    builder.add(InlineKeyboardButton(
        text="Продолжить выбор",
        callback_data=f"create_order:{project_id}"
    ))
    builder.add(InlineKeyboardButton(
        text="Очистить заказ",
        callback_data=f"clear_order:{project_id}:{order_id}"
    ))
    builder.add(InlineKeyboardButton(
        text="Завершить заказ",
        callback_data=f"finish_order:{project_id}:{order_id}"
    ))
    builder.add(InlineKeyboardButton(
        text="Назад",
        callback_data=f"select_project:{project_id}"
    ))
    
    builder.adjust(4, 1, 2, 1)
    return builder.as_markup()


def get_container_filter_keyboard(project_id: int) -> InlineKeyboardMarkup:
    """Создать клавиатуру выбора типа тары."""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="Кеги",
        callback_data=f"select_container:{project_id}:kegs"
    ))
    builder.add(InlineKeyboardButton(
        text="Банки",
        callback_data=f"select_container:{project_id}:cans"
    ))
    builder.add(InlineKeyboardButton(
        text="Бутылки",
        callback_data=f"select_container:{project_id}:bottles"
    ))
    
    builder.add(InlineKeyboardButton(
        text="Посмотреть заказ",
        callback_data=f"view_order:{project_id}:all"
    ))
    builder.add(InlineKeyboardButton(
        text="Назад",
        callback_data=f"select_project:{project_id}"
    ))
    
    builder.adjust(3, 1, 1)
    return builder.as_markup()


@router.callback_query(F.data.startswith("create_order:"))
async def create_order_handler(callback: CallbackQuery, state: FSMContext):
    """Начать формирование заказа - выбрать тип тары."""
    project_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    
    # Очищаем состояние если было
    await state.clear()
    
    # Создаем или получаем активный заказ
    order = await get_or_create_order(project_id, user_id)
    
    # Получаем количество позиций в текущем заказе
    order_items = await get_order_items(order.id)
    
    message_text = (
        "Формирование заказа\n\n"
        f"Текущий заказ: {len(order_items)} позиций\n\n"
        "Выберите тип тары:"
    )
    
    await callback.message.edit_text(
        message_text,
        reply_markup=get_container_filter_keyboard(project_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("select_container:"))
async def select_container_handler(callback: CallbackQuery, state: FSMContext):
    """Выбрать тип тары и показать пивоварни."""
    parts = callback.data.split(":")
    project_id = int(parts[1])
    container_filter = parts[2]
    user_id = callback.from_user.id
    
    # Получаем заказ
    order = await get_or_create_order(project_id, user_id)
    order_items = await get_order_items(order.id)
    
    filter_names = {
        "kegs": "Кеги",
        "cans": "Банки",
        "bottles": "Бутылки"
    }
    
    message_text = (
        "Формирование заказа\n\n"
        f"Текущий заказ: {len(order_items)} позиций\n"
        f"Тара: {filter_names.get(container_filter)}\n\n"
        "Выберите пивоварню:"
    )
    
    await callback.message.edit_text(
        message_text,
        reply_markup=await get_breweries_keyboard(project_id, container_filter)
    )
    await callback.answer()




@router.callback_query(F.data.startswith("brewery:"))
async def show_brewery_items(callback: CallbackQuery, state: FSMContext):
    """Показать позиции выбранной пивоварни."""
    parts = callback.data.split(":")
    project_id = int(parts[1])
    brewery = parts[2]
    container_filter = parts[3] if len(parts) > 3 else "all"
    
    # Получаем все позиции проекта
    async with async_session_maker() as session:
        from database.crud import get_project_beer_items
        beer_items = await get_project_beer_items(session, project_id)
    
    # Фильтруем по пивоварне и типу тары
    filtered_items = []
    for item in beer_items:
        if item.brewery == brewery:
            # Применяем фильтр по таре
            if container_filter != "all":
                volume_lower = str(item.volume).lower() if item.volume else ""
                if container_filter == "kegs" and "кег" not in volume_lower:
                    continue
                elif container_filter == "cans" and "банка" not in volume_lower:
                    continue
                elif container_filter == "bottles" and "бутылка" not in volume_lower:
                    continue
            
            filtered_items.append(item)
    
    if not filtered_items:
        await callback.answer(f"У пивоварни '{brewery}' нет позиций", show_alert=True)
        return
    
    # Формируем список текстом
    filter_names = {
        "kegs": "Кеги",
        "cans": "Банки",
        "bottles": "Бутылки"
    }
    
    lines = [f"Пивоварня: {brewery}"]
    if container_filter != "all":
        lines.append(f"Тара: {filter_names.get(container_filter)}")
    lines.append(f"Найдено: {len(filtered_items)} позиций\n")
    
    # Если фильтр установлен - не группируем
    if container_filter != "all":
        # Просто список
        items_map = {}
        for idx, item in enumerate(filtered_items, 1):
            line = f"{idx}. {item.name}"
            if item.volume:
                line += f" | {item.volume}"
            if item.price:
                line += f" | {item.price}"
            
            # Добавляем остаток
            if item.raw_data:
                import json
                try:
                    raw = json.loads(item.raw_data)
                    stock = raw.get('остаток')
                    if stock:
                        if isinstance(stock, int):
                            line += f" | Остаток: {stock} шт"
                        else:
                            line += f" | {stock}"
                except:
                    pass
            
            items_map[idx] = item.id
            lines.append(line)
    else:
        # Группируем по типу тары
        kegs = []
        cans = []
        bottles = []
        
        for item in filtered_items:
            volume_lower = str(item.volume).lower() if item.volume else ""
            if "кег" in volume_lower:
                kegs.append(item)
            elif "банка" in volume_lower:
                cans.append(item)
            elif "бутылка" in volume_lower:
                bottles.append(item)
    
        # Формируем нумерованный список по группам
        items_map = {}
        idx = 1
        
        if kegs:
            lines.append("\n=== КЕГИ ===")
            for item in kegs:
                line = f"{idx}. {item.name}"
                if item.volume:
                    line += f" | {item.volume}"
                if item.price:
                    line += f" | {item.price}"
                
                # Добавляем остаток
                if item.raw_data:
                    import json
                    try:
                        raw = json.loads(item.raw_data)
                        stock = raw.get('остаток')
                        if stock:
                            if isinstance(stock, int):
                                line += f" | Остаток: {stock} шт"
                            else:
                                line += f" | {stock}"
                    except:
                        pass
                
                items_map[idx] = item.id
                lines.append(line)
                idx += 1
        
        if cans:
            lines.append("\n=== БАНКИ ===")
            for item in cans:
                line = f"{idx}. {item.name}"
                if item.volume:
                    line += f" | {item.volume}"
                if item.price:
                    line += f" | {item.price}"
                
                # Добавляем остаток
                if item.raw_data:
                    import json
                    try:
                        raw = json.loads(item.raw_data)
                        stock = raw.get('остаток')
                        if stock:
                            if isinstance(stock, int):
                                line += f" | Остаток: {stock} шт"
                            else:
                                line += f" | {stock}"
                    except:
                        pass
                
                items_map[idx] = item.id
                lines.append(line)
                idx += 1
        
        if bottles:
            lines.append("\n=== БУТЫЛКИ ===")
            for item in bottles:
                line = f"{idx}. {item.name}"
                if item.volume:
                    line += f" | {item.volume}"
                if item.price:
                    line += f" | {item.price}"
                
                # Добавляем остаток
                if item.raw_data:
                    import json
                    try:
                        raw = json.loads(item.raw_data)
                        stock = raw.get('остаток')
                        if stock:
                            if isinstance(stock, int):
                                line += f" | Остаток: {stock} шт"
                            else:
                                line += f" | {stock}"
                    except:
                        pass
                
                items_map[idx] = item.id
                lines.append(line)
                idx += 1
    
    lines.append("\nДля заказа напишите номер:количество через пробел")
    lines.append("Например: 1:5 3:2 7:10")
    lines.append("Или просто номера: 1 3 7 (по 1 шт)")
    
    message_text = "\n".join(lines)
    
    # Сохраняем данные в состояние
    await state.set_state(OrderCreation.selecting_items)
    await state.update_data(
        project_id=project_id,
        brewery=brewery,
        items_map=items_map,
        container_filter=container_filter
    )
    
    await callback.message.edit_text(
        message_text[:4000],  # Telegram ограничение
        reply_markup=get_back_to_categories_keyboard(project_id)
    )
    await callback.answer()


@router.message(OrderCreation.selecting_items)
async def process_selected_items(message: Message, state: FSMContext):
    """Обработать введенные номера позиций с количеством."""
    data = await state.get_data()
    project_id = data.get('project_id')
    items_map = data.get('items_map')
    user_id = message.from_user.id
    
    # Получаем или создаем заказ
    order = await get_or_create_order(project_id, user_id)
    
    # Парсим введенные номера с количеством
    text = message.text.replace(',', ' ')
    items_to_add = []  # [(номер, количество)]
    
    for part in text.split():
        if ':' in part:
            # Формат "номер:количество"
            try:
                num_str, qty_str = part.split(':', 1)
                num = int(num_str)
                qty = int(qty_str)
                items_to_add.append((num, qty))
            except ValueError:
                continue
        else:
            # Просто номер (количество = 1)
            try:
                num = int(part)
                items_to_add.append((num, 1))
            except ValueError:
                continue
    
    if not items_to_add:
        await message.answer(
            "Не распознаны позиции.\n\n"
            "Формат: номер:количество\n"
            "Например: 1:5 3:2 7:10\n"
            "Или просто: 1 3 7 (по 1 шт)"
        )
        return
    
    # Добавляем позиции в заказ с проверкой остатков
    added = 0
    total_qty = 0
    warnings = []
    
    # Получаем информацию о позициях для проверки остатков
    async with async_session_maker() as session:
        from sqlalchemy.future import select
        from database.models import BeerItem
        
        for num, qty in items_to_add:
            if num in items_map:
                beer_item_id = items_map[num]
                
                # Получаем информацию о позиции
                result = await session.execute(
                    select(BeerItem).where(BeerItem.id == beer_item_id)
                )
                beer = result.scalars().first()
                
                if beer:
                    # Проверяем остаток
                    stock = None
                    if beer.raw_data:
                        import json
                        try:
                            raw = json.loads(beer.raw_data)
                            stock = raw.get('остаток')
                        except:
                            pass
                    
                    # Если остаток числовой - проверяем
                    if isinstance(stock, int):
                        if qty > stock:
                            warnings.append(f"Поз. {num} ({beer.name[:20]}): заказано {qty}, доступно {stock}")
                            # Ограничиваем количество доступным остатком
                            qty = stock
                    
                    if qty > 0:
                        await add_item_to_order(order.id, beer_item_id, quantity=qty)
                        added += 1
                        total_qty += qty
    
    response = f"Добавлено: {added} позиций ({total_qty} шт)"
    
    if warnings:
        response += "\n\nПревышен остаток:\n" + "\n".join(warnings)
    
    await message.answer(response)
    
    # Очищаем состояние
    await state.clear()
    
    # Возвращаемся к выбору тары
    order_items = await get_order_items(order.id)
    
    message_text = (
        "Формирование заказа\n\n"
        f"Текущий заказ: {len(order_items)} позиций\n\n"
        "Выберите тип тары:"
    )
    
    await message.answer(
        message_text,
        reply_markup=get_container_filter_keyboard(project_id)
    )


@router.callback_query(F.data.startswith("view_order:"))
async def view_order_handler(callback: CallbackQuery):
    """Показать текущий заказ с возможностью фильтрации."""
    parts = callback.data.split(":")
    project_id = int(parts[1])
    filter_type = parts[2] if len(parts) > 2 else "all"
    user_id = callback.from_user.id
    
    # Получаем заказ
    order = await get_or_create_order(project_id, user_id)
    order_items = await get_order_items(order.id)
    
    if not order_items:
        await callback.answer("Заказ пуст", show_alert=True)
        return
    
    # Формируем список позиций
    async with async_session_maker() as session:
        from sqlalchemy.future import select
        from database.models import BeerItem
        
        filter_title = {
            "all": "Ваш заказ:",
            "kegs": "Ваш заказ (Кеги):",
            "cans": "Ваш заказ (Банки):",
            "bottles": "Ваш заказ (Бутылки):"
        }
        
        lines = [filter_title.get(filter_type, "Ваш заказ:") + "\n"]
        total_price = 0.0
        shown_count = 0
        
        for order_item in order_items:
            # Получаем информацию о позиции
            result = await session.execute(
                select(BeerItem).where(BeerItem.id == order_item.beer_item_id)
            )
            beer = result.scalars().first()
            
            if beer:
                # Проверяем фильтр по типу тары
                volume_lower = str(beer.volume).lower() if beer.volume else ""
                
                if filter_type == "kegs" and "кег" not in volume_lower:
                    continue
                elif filter_type == "cans" and "банка" not in volume_lower:
                    continue
                elif filter_type == "bottles" and "бутылка" not in volume_lower:
                    continue
                
                shown_count += 1
                
                # Пивоварня перед названием
                line = f"{shown_count}. "
                if beer.brewery:
                    line += f"{beer.brewery} - "
                line += beer.name
                
                if beer.volume:
                    line += f" | {beer.volume}"
                if beer.price:
                    line += f" | {beer.price}"
                line += f" x {order_item.quantity}"
                lines.append(line)
                
                # Пытаемся посчитать сумму
                if beer.price:
                    try:
                        price_str = beer.price.replace("руб.", "").replace(",", ".").strip().split()[0]
                        price = float(price_str)
                        total_price += price * order_item.quantity
                    except:
                        pass
        
        if shown_count == 0:
            lines.append("В этой категории ничего нет")
        elif total_price > 0:
            lines.append(f"\nПозиций: {shown_count}")
            lines.append(f"Итого: {total_price:.2f} руб.")
    
    message_text = "\n".join(lines)
    
    await callback.message.edit_text(
        message_text,
        reply_markup=get_order_view_keyboard(project_id, order.id, filter_type)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("clear_order:"))
async def clear_order_handler(callback: CallbackQuery):
    """Очистить заказ."""
    parts = callback.data.split(":")
    project_id = int(parts[1])
    order_id = int(parts[2])
    
    await clear_order(order_id)
    
    await callback.answer("Заказ очищен")
    
    # Возвращаемся к выбору категорий
    await callback.message.edit_text(
        "Формирование заказа\n\n"
        "Текущий заказ: 0 позиций\n\n"
        "Выберите категорию напитков:",
        reply_markup=get_categories_keyboard(project_id)
    )


@router.callback_query(F.data.startswith("finish_order:"))
async def finish_order_handler(callback: CallbackQuery):
    """Завершить заказ и сформировать .txt файл."""
    parts = callback.data.split(":")
    project_id = int(parts[1])
    order_id = int(parts[2])
    
    # Получаем все позиции заказа
    order_items = await get_order_items(order_id)
    
    if not order_items:
        await callback.answer("Заказ пуст", show_alert=True)
        return
    
    # Формируем текстовый файл заказа
    async with async_session_maker() as session:
        from sqlalchemy.future import select
        from database.models import Order, BeerItem, Project
        
        # Получаем информацию о проекте
        result = await session.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalars().first()
        
        lines = [f"ЗАКАЗ: {project.name if project else 'Проект'}"]
        lines.append(f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
        
        # Группируем по таре
        kegs = []
        cans = []
        bottles = []
        total_price = 0.0
        
        for order_item in order_items:
            result = await session.execute(
                select(BeerItem).where(BeerItem.id == order_item.beer_item_id)
            )
            beer = result.scalars().first()
            
            if beer:
                item_data = {
                    'beer': beer,
                    'quantity': order_item.quantity
                }
                
                volume_lower = str(beer.volume).lower() if beer.volume else ""
                if "кег" in volume_lower:
                    kegs.append(item_data)
                elif "банка" in volume_lower:
                    cans.append(item_data)
                elif "бутылка" in volume_lower:
                    bottles.append(item_data)
                
                # Считаем сумму
                if beer.price:
                    try:
                        price_str = beer.price.replace("руб.", "").replace(",", ".").strip().split()[0]
                        price = float(price_str)
                        total_price += price * order_item.quantity
                    except:
                        pass
        
        # Формируем по группам
        idx = 1
        
        if kegs:
            lines.append("=== КЕГИ ===\n")
            for item_data in kegs:
                beer = item_data['beer']
                qty = item_data['quantity']
                
                line = f"{idx}. "
                if beer.brewery:
                    line += f"{beer.brewery} - "
                line += beer.name
                if beer.volume:
                    line += f" | {beer.volume}"
                if beer.price:
                    line += f" | {beer.price}"
                line += f" x {qty}"
                
                lines.append(line)
                idx += 1
            lines.append("")
        
        if cans:
            lines.append("=== БАНКИ ===\n")
            for item_data in cans:
                beer = item_data['beer']
                qty = item_data['quantity']
                
                line = f"{idx}. "
                if beer.brewery:
                    line += f"{beer.brewery} - "
                line += beer.name
                if beer.volume:
                    line += f" | {beer.volume}"
                if beer.price:
                    line += f" | {beer.price}"
                line += f" x {qty}"
                
                lines.append(line)
                idx += 1
            lines.append("")
        
        if bottles:
            lines.append("=== БУТЫЛКИ ===\n")
            for item_data in bottles:
                beer = item_data['beer']
                qty = item_data['quantity']
                
                line = f"{idx}. "
                if beer.brewery:
                    line += f"{beer.brewery} - "
                line += beer.name
                if beer.volume:
                    line += f" | {beer.volume}"
                if beer.price:
                    line += f" | {beer.price}"
                line += f" x {qty}"
                
                lines.append(line)
                idx += 1
            lines.append("")
        
        lines.append(f"Всего позиций: {len(order_items)}")
        if total_price > 0:
            lines.append(f"Итого: {total_price:.2f} руб.")
        
        # Обновляем статус заказа
        result = await session.execute(
            select(Order).where(Order.id == order_id)
        )
        order = result.scalars().first()
        
        if order:
            order.status = "confirmed"
            await session.commit()
    
    # Формируем текстовый файл
    txt_content = "\n".join(lines)
    
    txt_file = BufferedInputFile(
        txt_content.encode('utf-8'),
        filename=f"заказ_{project.name if project else 'проект'}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
    )
    
    await callback.answer("Заказ сформирован")
    
    await callback.message.edit_text(
        "Заказ успешно сформирован и сохранен!\n\n"
        f"Позиций: {len(order_items)}\n"
        f"Файл заказа отправлен ниже.",
        reply_markup=get_project_actions_keyboard(project_id)
    )
    
    # Отправляем файл
    await callback.message.answer_document(
        txt_file,
        caption=f"Заказ от {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )

