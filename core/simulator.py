# core/simulator.py
class OmniSimulator:
    def __init__(self, registry):
        self.registry = registry

    def validate_graph(self, graph_json):
        nodes = graph_json.get('drawflow', {}).get('Home', {}).get('data', {})
        report = {"status": "OK", "errors": []}

        for node_id, node in nodes.items():
            # Проверка: есть ли такой модуль в реестре?
            if not self.registry.validate_node(node.get('data')):
                report["errors"].append(f"Узел {node_id} ({node.get('name')}) отсутствует в Registry.")
                report["status"] = "FAIL"

        return report

# Куда вставлять:
# В вашем main.py импортируйте его:
# from core.simulator import OmniSimulator
# simulator = OmniSimulator(registry)
