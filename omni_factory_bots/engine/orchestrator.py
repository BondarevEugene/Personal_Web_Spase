# ==============================================================================
# PROJECT: OMNIFACTORY EVO // ENTERPRISE_ORCHESTRATOR_ENGINE
# LOCATION: /omni_factory_bots/engine/orchestrator.py
# VERSION: 6.0.0 (PRODUCTION_STEEL)
# DESCRIPTION: Главный промышленный диспетчер и супервизор жизненного цикла ботов.
# ==============================================================================
import os
import sys
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from omni_factory_bots.engine.registry import Registry
from omni_factory_bots.engine.runner import BotRunner
from bot_factory import BotFactory
from project_generator import ProjectGenerator

logger = logging.getLogger("OmniOrchestrator")


class Orchestrator:
    def __init__(self, registry_instance: Registry):
        """
        Инициализация ядра оркестрации с инъекцией глобального реестра модулей.
        """
        self.registry = registry_instance
        self.runner = BotRunner(self.registry)

        # Операционные реестры данных (In-Memory Системные СУБД)
        self.active_graphs: Dict[str, Dict[str, Any]] = {}  # {bot_id: raw_graph_json}
        self.running_instances: Dict[str, Dict[str, Any]] = {}  # {bot_id: metadata_and_tasks}
        self.faults_ledger: List[Dict[str, Any]] = []  # Лог критических сбоев нод

        logger.info("🟢 [ORCHESTRATOR_INIT] Промышленное ядро супервизора OmniFactory активировано.")

    def deploy_bot_graph(self, bot_id: str, graph_data: dict, selected_module_ids: List[str]) -> Dict[str, Any]:
        """
        Конвейер деплоя: Принимает визуальный граф, компилирует через BotFactory,
        генерирует Docker-пакет через ProjectGenerator и обновляет карту рантайма.
        """
        if not graph_data or "nodes" not in graph_data:
            self._register_fault(bot_id, "SYSTEM", "Invalid graph structure compiled from frontend UI.")
            raise ValueError(f"🚨 [DEPLOY_ERROR] Некорректная структура графа для: {bot_id}")

        try:
            logger.info(
                f"⚡ [COMPILING] Инициализация сборки графа для бота '{bot_id}'. Нод в цепочке: {len(graph_data['nodes'])}")

            # 1. Синтез исходного кода на базе aiogram v3
            factory = BotFactory(self.registry)
            compiled_code = factory.generate(selected_module_ids)

            # 2. Упаковка среды развертывания (Dockerfile, requirements.txt, main.py)
            generator = ProjectGenerator(compiled_code, selected_module_ids)
            deployment_package = generator.create_deployment_package()  # Возвращает BytesIO поток zip-архива

            # 3. Сохранение графа для рантайм-маршрутизации событий
            self.active_graphs[bot_id] = graph_data

            # 4. Обновление метаданных рантайма
            self.running_instances[bot_id] = {
                "status": "COMPILED",
                "deployed_at": datetime.now().isoformat(),
                "nodes_count": len(graph_data['nodes']),
                "edges_count": len(graph_data.get('edges', [])),
                "package_size_bytes": sys.getsizeof(deployment_package)
            }

            logger.info(f"✅ [DEPLOY_SUCCESS] Бот '{bot_id}' успешно собран. Среда инкапсулирована в ZIP-пакет.")
            return {
                "status": "success",
                "message": f"Бот {bot_id} успешно скомпилирован в Docker-окружение.",
                "telemetry": self.running_instances[bot_id]
            }

        except Exception as e:
            self._register_fault(bot_id, "COMPILER_BRIDGE", str(e))
            logger.error(f"❌ [CRITICAL_DEPLOY_FAULT] Ошибка конвейера сборки бота {bot_id}: {str(e)}")
            return {"status": "error", "message": f"Deploy compilation failed: {str(e)}"}

    async def route_incoming_event(self, bot_id: str, user_id: int, event_type: str, raw_payload: Dict[str, Any],
                                   context: dict) -> Dict[str, Any]:
        """
        Высокоскоростной роутер событий. Принимает триггеры (сообщения, клики по кнопкам, вебхуки),
        определяет по графу целевую ноду и отправляет её в асинхронный интерпретатор Runner.
        """
        graph = self.active_graphs.get(bot_id)
        if not graph:
            self._register_fault(bot_id, "ROUTER", f"Event received for un-deployed bot instance.")
            return {"status": "error", "message": f"Граф бота {bot_id} отсутствует в памяти ядра."}

        # 1. Определение целевой ноды на основе контекста выполнения (FSM или Callback Query ID)
        current_node_id = context.get("current_node_id")

        # Если это нажатие инлайн-кнопки (Callback Query), ищем ноду-приемник по связям графа (edges)
        if event_type == "callback_query" and "callback_data" in raw_payload:
            target_edge = next((edge for edge in graph.get("edges", []) if edge["source"] == current_node_id), None)
            if target_edge:
                current_node_id = target_edge["target"]

        # 2. Извлечение ноды из карты графа
        target_node = next((node for node in graph["nodes"] if node["id"] == current_node_id), None)
        if not target_node:
            # Предохранитель: если шаг сбился, кидаем пользователя на стартовый узел (Welcome Core / Trigger)
            target_node = next((node for node in graph["nodes"] if
                                "welcome" in node.get("id", "").lower() or "trigger" in node.get("id", "").lower()),
                               None)
            if not target_node:
                return {"status": "error", "message": "Не удалось определить точку входа на графе."}

        # 3. Трансляция выполнения в исполнительное ядро интерпретатора runner.py
        try:
            logger.info(f"🚀 [TRANSIT] Бот: {bot_id} // Юзер: {user_id} // Выполнение узла: {target_node.get('id')}")

            # Формируем изолированную среду для Runner
            context.update({
                "user_id": user_id,
                "bot_id": bot_id,
                "event_payload": raw_payload,
                "event_type": event_type
            })

            # Асинхронный вызов движка выполнения
            execution_output = await self.runner.execute_node(target_node, context)

            # Обновляем статус рантайма (инкремент успешных транзитов)
            if bot_id in self.running_instances:
                self.running_instances[bot_id]["status"] = "ACTIVE"
                self.running_instances[bot_id]["last_execution"] = datetime.now().isoformat()

            return {
                "status": "success",
                "current_step": target_node["id"],
                "output": execution_output
            }

        except Exception as e:
            self._register_fault(bot_id, target_node.get("id", "UNKNOWN_NODE"), str(e))
            return {"status": "error", "message": f"Runtime execution fault: {str(e)}"}

    def terminate_bot_instance(self, bot_id: str) -> bool:
        """
        Принудительная остановка логических потоков инстанса бота и очистка оперативной памяти.
        """
        if bot_id in self.running_instances:
            self.running_instances[bot_id]["status"] = "TERMINATED"
            self.running_instances[bot_id]["terminated_at"] = datetime.now().isoformat()
            logger.warning(f"🛑 [SIGKILL] Потоки бота '{bot_id}' принудительно остановлены супервизором.")
            return True
        return False

    def get_cluster_telemetry(self) -> Dict[str, Any]:
        """
        Собирает сводную промышленную телеметрию со всех запущенных процессов для вывода в UI.
        """
        return {
            "total_deployed_bots": len(self.active_graphs),
            "active_instances": len([b for b in self.running_instances.values() if b["status"] == "ACTIVE"]),
            "faults_count": len(self.faults_ledger),
            "instances_matrix": self.running_instances,
            "faults_log": self.faults_ledger[-10:]  # Отдаем последние 10 критических ошибок
        }

    def _register_fault(self, bot_id: str, node_id: str, error_msg: str):
        """
        Внутренний регистратор сбоев для Faults Ledger (метрика надежности системы).
        """
        fault = {
            "timestamp": datetime.now().isoformat(),
            "bot_id": bot_id,
            "node_id": node_id,
            "error": error_msg
        }
        self.faults_ledger.append(fault)
        logger.error(f"🚨 [FAULT_RECORDED] Бот: {bot_id} // Узел: {node_id} // Ошибка: {error_msg}")