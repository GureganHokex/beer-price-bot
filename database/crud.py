"""
CRUD операции для работы с базой данных.
"""
import json
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.future import select
from sqlalchemy import delete

from database.models import Base, User, Project, Upload, BeerItem, Order, OrderItem
import config


engine = create_async_engine(config.DB_URL, echo=False)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """
    Инициализация базы данных.
    Создает все таблицы.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    """
    Получить сессию базы данных.
    
    Returns:
        AsyncSession: Асинхронная сессия
    """
    async with async_session_maker() as session:
        yield session


# User CRUD
async def get_or_create_user(session: AsyncSession, telegram_id: int, username: Optional[str] = None) -> User:
    """
    Получить или создать пользователя.
    
    Args:
        session: Сессия базы данных
        telegram_id: ID пользователя в Telegram
        username: Имя пользователя
        
    Returns:
        User: Объект пользователя
    """
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(telegram_id=telegram_id, username=username)
        session.add(user)
        await session.commit()
        await session.refresh(user)
    
    return user


async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> Optional[User]:
    """
    Получить пользователя по Telegram ID.
    
    Args:
        session: Сессия базы данных
        telegram_id: ID пользователя в Telegram
        
    Returns:
        Optional[User]: Объект пользователя или None
    """
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()


# Project CRUD
async def create_project(session: AsyncSession, user_id: int, name: str) -> Project:
    """
    Создать новый проект.
    
    Args:
        session: Сессия базы данных
        user_id: ID пользователя
        name: Название проекта
        
    Returns:
        Project: Созданный проект
    """
    project = Project(user_id=user_id, name=name)
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return project


async def get_user_projects(session: AsyncSession, user_id: int) -> List[Project]:
    """
    Получить все проекты пользователя.
    
    Args:
        session: Сессия базы данных
        user_id: ID пользователя
        
    Returns:
        List[Project]: Список проектов
    """
    result = await session.execute(
        select(Project).where(Project.user_id == user_id).order_by(Project.created_at.desc())
    )
    return result.scalars().all()


async def get_project_by_id(session: AsyncSession, project_id: int) -> Optional[Project]:
    """
    Получить проект по ID.
    
    Args:
        session: Сессия базы данных
        project_id: ID проекта
        
    Returns:
        Optional[Project]: Объект проекта или None
    """
    result = await session.execute(select(Project).where(Project.id == project_id))
    return result.scalar_one_or_none()


# Upload CRUD
async def create_upload(session: AsyncSession, project_id: int, filename: str, path: str) -> Upload:
    """
    Создать запись о загруженном файле.
    
    Args:
        session: Сессия базы данных
        project_id: ID проекта
        filename: Имя файла
        path: Путь к файлу
        
    Returns:
        Upload: Созданная запись
    """
    upload = Upload(project_id=project_id, filename=filename, path=path)
    session.add(upload)
    await session.commit()
    await session.refresh(upload)
    return upload


async def get_project_uploads(session: AsyncSession, project_id: int) -> List[Upload]:
    """
    Получить все загруженные файлы проекта.
    
    Args:
        session: Сессия базы данных
        project_id: ID проекта
        
    Returns:
        List[Upload]: Список загруженных файлов
    """
    result = await session.execute(
        select(Upload).where(Upload.project_id == project_id).order_by(Upload.uploaded_at.desc())
    )
    return result.scalars().all()


# BeerItem CRUD
async def create_beer_item(
    session: AsyncSession,
    project_id: int,
    brewery: Optional[str] = None,
    name: Optional[str] = None,
    style: Optional[str] = None,
    volume: Optional[str] = None,
    price: Optional[str] = None,
    raw_data: Optional[dict] = None
) -> BeerItem:
    """
    Создать позицию пива.
    
    Args:
        session: Сессия базы данных
        project_id: ID проекта
        brewery: Пивоварня
        name: Название
        style: Стиль
        volume: Объем
        price: Цена
        raw_data: Сырые данные в виде dict
        
    Returns:
        BeerItem: Созданная позиция
    """
    beer_item = BeerItem(
        project_id=project_id,
        brewery=brewery,
        name=name,
        style=style,
        volume=volume,
        price=price,
        raw_data=json.dumps(raw_data, ensure_ascii=False) if raw_data else None
    )
    session.add(beer_item)
    await session.commit()
    await session.refresh(beer_item)
    return beer_item


async def get_project_beer_items(session: AsyncSession, project_id: int) -> List[BeerItem]:
    """
    Получить все позиции пива в проекте.
    
    Args:
        session: Сессия базы данных
        project_id: ID проекта
        
    Returns:
        List[BeerItem]: Список позиций пива
    """
    result = await session.execute(
        select(BeerItem).where(BeerItem.project_id == project_id).order_by(BeerItem.created_at.desc())
    )
    return result.scalars().all()


async def clear_project_beer_items(session: AsyncSession, project_id: int) -> None:
    """
    Удалить все позиции пива из проекта.
    
    Args:
        session: Сессия базы данных
        project_id: ID проекта
    """
    await session.execute(delete(BeerItem).where(BeerItem.project_id == project_id))
    await session.commit()


async def delete_beer_items_by_project(project_id: int) -> int:
    """
    Удалить все позиции пива из проекта и вернуть количество.
    
    Args:
        project_id: ID проекта
        
    Returns:
        int: Количество удаленных позиций
    """
    async with async_session_maker() as session:
        # Получаем количество перед удалением
        result = await session.execute(
            select(BeerItem).where(BeerItem.project_id == project_id)
        )
        count = len(result.scalars().all())
        
        # Удаляем
        await session.execute(delete(BeerItem).where(BeerItem.project_id == project_id))
        await session.commit()
        
        return count


async def delete_project(project_id: int) -> None:
    """
    Удалить проект и все связанные данные.
    
    Args:
        project_id: ID проекта
    """
    async with async_session_maker() as session:
        # Удаляем все связанные данные (каскадное удаление настроено в моделях)
        await session.execute(delete(Project).where(Project.id == project_id))
        await session.commit()


# Order CRUD
async def get_or_create_order(project_id: int, user_id: int) -> Order:
    """
    Получить или создать активный заказ для проекта.
    
    Args:
        project_id: ID проекта
        user_id: ID пользователя
        
    Returns:
        Order: Объект заказа
    """
    async with async_session_maker() as session:
        # Ищем активный заказ (статус draft)
        result = await session.execute(
            select(Order).where(
                Order.project_id == project_id,
                Order.user_id == user_id,
                Order.status == "draft"
            )
        )
        order = result.scalars().first()
        
        if not order:
            # Создаем новый заказ
            order = Order(
                project_id=project_id,
                user_id=user_id,
                status="draft"
            )
            session.add(order)
            await session.commit()
            await session.refresh(order)
        
        return order


async def add_item_to_order(order_id: int, beer_item_id: int, quantity: int = 1) -> OrderItem:
    """
    Добавить позицию в заказ или обновить количество.
    
    Args:
        order_id: ID заказа
        beer_item_id: ID позиции пива
        quantity: Количество
        
    Returns:
        OrderItem: Объект позиции заказа
    """
    async with async_session_maker() as session:
        # Проверяем есть ли уже эта позиция в заказе
        result = await session.execute(
            select(OrderItem).where(
                OrderItem.order_id == order_id,
                OrderItem.beer_item_id == beer_item_id
            )
        )
        order_item = result.scalars().first()
        
        if order_item:
            # Обновляем количество
            order_item.quantity += quantity
        else:
            # Создаем новую позицию
            order_item = OrderItem(
                order_id=order_id,
                beer_item_id=beer_item_id,
                quantity=quantity
            )
            session.add(order_item)
        
        await session.commit()
        await session.refresh(order_item)
        return order_item


async def get_order_items(order_id: int) -> List[OrderItem]:
    """
    Получить все позиции заказа.
    
    Args:
        order_id: ID заказа
        
    Returns:
        List[OrderItem]: Список позиций заказа
    """
    async with async_session_maker() as session:
        result = await session.execute(
            select(OrderItem).where(OrderItem.order_id == order_id)
        )
        return result.scalars().all()


async def remove_item_from_order(order_item_id: int) -> None:
    """
    Удалить позицию из заказа.
    
    Args:
        order_item_id: ID позиции заказа
    """
    async with async_session_maker() as session:
        await session.execute(delete(OrderItem).where(OrderItem.id == order_item_id))
        await session.commit()


async def clear_order(order_id: int) -> None:
    """
    Очистить все позиции заказа.
    
    Args:
        order_id: ID заказа
    """
    async with async_session_maker() as session:
        await session.execute(delete(OrderItem).where(OrderItem.order_id == order_id))
        await session.commit()


async def get_order_by_id(order_id: int) -> Optional[Order]:
    """
    Получить заказ по ID.
    
    Args:
        order_id: ID заказа
        
    Returns:
        Optional[Order]: Объект заказа или None
    """
    async with async_session_maker() as session:
        result = await session.execute(
            select(Order).where(Order.id == order_id)
        )
        return result.scalars().first()


async def create_quick_order(
    session: AsyncSession,
    user_id: int,
    filename: str,
    original_data: str,
    order_data: str
) -> Order:
    """
    Создать быстрый заказ (без проекта).
    
    Args:
        session: Сессия базы данных
        user_id: ID пользователя
        filename: Имя загруженного файла
        original_data: JSON исходных данных
        order_data: JSON данных заказа
        
    Returns:
        Order: Созданный заказ
    """
    order = Order(
        user_id=user_id,
        project_id=None,
        status="confirmed",
        filename=filename,
        original_data=original_data,
        order_data=order_data
    )
    session.add(order)
    await session.commit()
    await session.refresh(order)
    return order

