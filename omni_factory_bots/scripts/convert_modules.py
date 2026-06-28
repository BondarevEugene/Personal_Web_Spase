# ==============================================================================
# PROJECT: OMNIFACTORY // EVO_CORE
# LOCATION: /omni_factory_bots/scripts/convert_modules.py
# DESCRIPTION: Устойчивый конвертер TS -> JSON (учитывает путь в omni_factory_bots)
# ==============================================================================

import re
import json
import os

# Скрипт лежит в omni_factory_bots/scripts/
# config лежит в omni_factory_bots/config/
# Значит, от скрипта нужно подняться на ОДИН уровень вверх (..)
script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(script_dir)

ts_path = os.path.join(base_dir, 'config', 'bot_modules.ts')
output_path = os.path.join(base_dir, 'config', 'registry.json')


def convert_ts_to_json():
    print(f"DEBUG: Пытаюсь открыть файл по пути: {ts_path}")

    if not os.path.exists(ts_path):
        print(f"ОШИБКА: Файл не найден! Проверь, что он точно лежит здесь: {ts_path}")
        return

    with open(ts_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Регулярка для захвата модулей из TS
    pattern = r"\{ id: '([^']+)', cat: '([^']+)', label: '([^']+)', icon: ([^,]+), desc: '([^']+)' \}"
    matches = re.findall(pattern, content)

    registry = {}
    for mid, cat, label, icon, desc in matches:
        cat_key = cat.upper()
        if cat_key not in registry:
            registry[cat_key] = []
        registry[cat_key].append({
            "id": mid,
            "label": label,
            "cat": cat,
            "icon": str(icon),
            "desc": desc
        })

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)

    print(f"SUCCESS: Сконвертировано {len(matches)} модулей в {output_path}")


if __name__ == "__main__":
    convert_ts_to_json()