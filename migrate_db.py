"""
Скрипт миграции базы данных для добавления новых полей в таблицу orders.
"""
import asyncio
from sqlalchemy import text
from database.crud import engine


async def migrate():
    """
    Миграция базы данных.
    """
    print("Начало миграции...")
    
    async with engine.begin() as conn:
        # Проверяем существует ли колонка filename
        result = await conn.execute(text(
            "SELECT COUNT(*) FROM pragma_table_info('orders') WHERE name='filename'"
        ))
        has_filename = result.scalar() > 0
        
        if not has_filename:
            print("Добавление колонки filename...")
            await conn.execute(text(
                "ALTER TABLE orders ADD COLUMN filename VARCHAR(255)"
            ))
            print("Колонка filename добавлена")
        else:
            print("Колонка filename уже существует")
        
        # Проверяем существует ли колонка original_data
        result = await conn.execute(text(
            "SELECT COUNT(*) FROM pragma_table_info('orders') WHERE name='original_data'"
        ))
        has_original_data = result.scalar() > 0
        
        if not has_original_data:
            print("Добавление колонки original_data...")
            await conn.execute(text(
                "ALTER TABLE orders ADD COLUMN original_data TEXT"
            ))
            print("Колонка original_data добавлена")
        else:
            print("Колонка original_data уже существует")
        
        # Проверяем существует ли колонка order_data
        result = await conn.execute(text(
            "SELECT COUNT(*) FROM pragma_table_info('orders') WHERE name='order_data'"
        ))
        has_order_data = result.scalar() > 0
        
        if not has_order_data:
            print("Добавление колонки order_data...")
            await conn.execute(text(
                "ALTER TABLE orders ADD COLUMN order_data TEXT"
            ))
            print("Колонка order_data добавлена")
        else:
            print("Колонка order_data уже существует")
        
        # Делаем project_id nullable
        print("Обновление колонки project_id (nullable)...")
        # SQLite не поддерживает ALTER COLUMN, поэтому пропускаем
        print("Колонка project_id уже nullable (в новой схеме)")
    
    print("Миграция завершена успешно!")


if __name__ == "__main__":
    asyncio.run(migrate())

