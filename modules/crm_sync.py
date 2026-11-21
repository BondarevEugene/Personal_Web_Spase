# omni_factory_bots/modules/crm_sync.py
import logging
from db.models import Client

class CRMModule:
    """
    Модуль для интеграции с БД.
    Используется в узле CRM_SYNC на холсте.
    """

    async def run(self, context, config):
        # context должен содержать 'db' (сессию) и 'user_data' (данные от юзера)
        db = context.get('db')
        data = context.get('user_data')  # {'full_name': '...', 'phone': '...'}

        try:
            # Создаем или обновляем запись
            client = Client(
                full_name=data.get('full_name'),
                phone=data.get('phone'),
                bot_id=context.get('bot_id'),
                notes=data.get('notes')
            )
            db.add(client)
            db.commit()
            return {"status": "success", "msg": "Клиент зарегистрирован"}
        except Exception as e:
            db.rollback()
            logging.error(f"CRM Error: {e}")
            return {"status": "error", "msg": str(e)}





class CRMModule:
    async def run(self, context, config):
        db = context.get('db')
        phone = context.get('user_data', {}).get('phone')

        # Поиск клиента по номеру телефона
        client = db.query(Client).filter(Client.phone == phone).first()

        if client:
            return {"status": "found", "data": {"name": client.full_name, "notes": client.notes}}
        else:
            # Если не найден - создаем запись (регистрация)
            new_client = Client(phone=phone, bot_id=context.get('bot_id'))
            db.add(new_client)
            db.commit()
            return {"status": "registered"}