import logging
from db.models import Client


class CRMModule:
    async def run(self, context, config):
        db = context.get('db')
        phone = context.get('user_data', {}).get('phone')

        # Поиск по базе
        client = db.query(Client).filter(Client.phone == phone).first()

        if client:
            return {"status": "found", "data": {"name": client.full_name, "notes": client.notes}}
        else:
            # Если новый - регистрируем
            new_client = Client(phone=phone, bot_id=context.get('bot_id'))
            db.add(new_client)
            db.commit()
            return {"status": "registered"}
