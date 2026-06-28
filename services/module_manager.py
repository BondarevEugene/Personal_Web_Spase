# ==============================================================================
# PROJECT: OMNIFACTORY // EVO_CORE
# LOCATION: /services/module_manager.py
# ==============================================================================
class ModuleManager:
    def __init__(self, registry):
        self.registry = registry

    def get_ui_registry(self):
        data = self.registry.modules
        return {
            "modules": [
                {"id": mod["id"], "label": mod["label"], "cat": mod["cat"], "desc": mod["desc"]}
                for cat in data.values() for mod in cat
            ]
        }