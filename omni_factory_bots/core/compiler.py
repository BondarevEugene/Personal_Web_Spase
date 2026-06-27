# core/compiler.py
import json
import os


class BotCompiler:
    def __init__(self, client_id, bot_id, graph_data):
        self.client_id = client_id
        self.bot_id = bot_id
        self.graph = graph_data
        self.target_dir = f"../omni_factory_bots/client_{client_id}/bot_{bot_id}"

    def build(self):
        os.makedirs(self.target_dir, exist_ok=True)

        # 1. Загружаем базовый каркас aiogram
        code = ["import asyncio", "from aiogram import Bot, Dispatcher", "dp = Dispatcher()", ""]

        # 2. Парсим узлы из graph_data
        nodes = self.graph.get('drawflow', {}).get('Home', {}).get('data', {})
        for node_id, node_data in nodes.items():
            module_name = node_data.get('name')
            config = node_data.get('data', {}).get('config', {})

            # 3. Вызываем bot_factory.py для получения куска кода
            # code.append(BotFactory.get_code_for(module_name, config))

        # 4. Сохраняем в main.py
        with open(f"{self.target_dir}/main.py", "w", encoding="utf-8") as f:
            f.write("\n".join(code))

        return f"Compiled successfully at {self.target_dir}"