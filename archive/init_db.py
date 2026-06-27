import psycopg2
import datetime

# Твоя строка подключения из личного кабинета Neon.tech
NEON_DATABASE_URL = "postgresql://neondb_owner:npg_PwedkOSD0oL5@ep-sparkling-sea-ap665555-pooler.c-7.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"


def initialize_neon_database():
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 🚀 Запуск инициализации базы данных Neon.tech...")

    try:
        # Подключаемся к Postgres
        conn = psycopg2.connect(NEON_DATABASE_URL)
        conn.autocommit = True

        with conn.cursor() as cursor:
            # 1. Таблица для регламентных задач и конвейеров (crm_events)
            print("🔹 Создание таблицы crm_events...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS crm_events (
                    id VARCHAR(50) PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    scheduled_time VARCHAR(100) NOT NULL,
                    target_site VARCHAR(255) DEFAULT 'LOCAL_HOST',
                    linked_script VARCHAR(100) DEFAULT 'HEALTH_SCAN',
                    status VARCHAR(50) DEFAULT 'PENDING',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 2. Таблица для системных логов ядра (core_logs)
            print("🔹 Создание таблицы core_logs...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS core_logs (
                    id SERIAL PRIMARY KEY,
                    timestamp VARCHAR(100) NOT NULL,
                    level VARCHAR(20) DEFAULT 'INFO',
                    message TEXT NOT NULL
                );
            """)

            # 3. Заливаем стартовый пул задач (заготовки), чтобы планировщик сразу ожил
            print("🔹 Проверка и заливка стартовых регламентных задач...")
            cursor.execute("SELECT COUNT(*) FROM crm_events;")
            if cursor.fetchone()[0] == 0:
                # Вставляем твои оригинальные системные таски
                default_tasks = [
                    ('t1', 'Backup Genesys Core', 'Резервное копирование локальной БД',
                     datetime.datetime.now().isoformat(), 'GENESYS_NODE', 'CORE_BACKUP', 'PENDING'),
                    ('t2', 'Sync SEO Snapshot', 'Выгрузка поисковых снапшотов', datetime.datetime.now().isoformat(),
                     'OMNI_MAIN', 'SEO_SYNC', 'PENDING'),
                    ('t3', 'Health Scan: Valkyria', 'Проверка доступности узлов', datetime.datetime.now().isoformat(),
                     'VALKYRIA_CORE', 'HEALTH_SCAN', 'PENDING'),
                    ('t4', 'Audit TG_Stars Shroud', 'Сверка кассы биллинга Telegram Stars',
                     datetime.datetime.now().isoformat(), 'TG_SHROUD', 'AUDIT_STARS', 'PENDING'),
                    (
                        't5', 'Re-index ChromaDB Vector', 'Переиндексация векторов ИИ',
                        datetime.datetime.now().isoformat(),
                        'CHROMA_LOCAL', 'REINDEX_VECTORS', 'PENDING')
                ]

                cursor.executemany("""
                    INSERT INTO crm_events (id, title, description, scheduled_time, target_site, linked_script, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s);
                """, default_tasks)
                print(f"✅ Успешно добавлено {len(default_tasks)} стартовых задач.")
            else:
                print("ℹ️ Таблица задач уже содержит данные, пропуск заливки дефолтных тасок.")

        conn.close()
        print(f"\n============================================================")
        print(f"🟢 БАЗА ДАННЫХ NEON.TECH УСПЕШНО ИНИЦИАЛИЗИРОВАНА И ГОТОВА!")
        print(f"============================================================")

    except Exception as e:
        print(f"❌ Ошибка при инициализации базы данных: {e}")


if __name__ == "__main__":
    initialize_neon_database()
