"""Regression tests for generated bot runtime and SQLite dialogue recovery."""
import ast
import json
import sqlite3

from api.simple_builder import _RUNTIME_SOURCE


def storage_functions(tmp_path):
    tree = ast.parse(_RUNTIME_SOURCE)
    names = {"init_state", "save_state"}
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    assert len(functions) == 2
    namespace = {
        "sqlite3": sqlite3,
        "json": json,
        "DB_PATH": tmp_path / "state.sqlite3",
        "CURSORS": {},
        "VALUES": {},
        "NODES": {"ask": {}, "end": {}},
    }
    module = ast.Module(body=functions, type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), "<generated-storage>", "exec"), namespace)
    return namespace


def test_generated_bot_compiles():
    compile(_RUNTIME_SOURCE, "<generated-bot>", "exec")


def test_dialogue_survives_restart(tmp_path):
    state = storage_functions(tmp_path)
    state["init_state"]()
    state["CURSORS"][(12, 34)] = "ask"
    state["VALUES"][(12, 34)] = {"name": "Анна"}
    state["save_state"]((12, 34))
    restored = storage_functions(tmp_path)
    restored["init_state"]()
    assert restored["CURSORS"] == {(12, 34): "ask"}
    assert restored["VALUES"][(12, 34)] == {"name": "Анна"}


def test_completed_dialogue_is_deleted(tmp_path):
    state = storage_functions(tmp_path)
    state["init_state"]()
    state["CURSORS"][(12, 34)] = "ask"
    state["save_state"]((12, 34))
    state["CURSORS"].clear()
    state["VALUES"].clear()
    state["save_state"]((12, 34))
    restored = storage_functions(tmp_path)
    restored["init_state"]()
    assert restored["CURSORS"] == {}
    assert restored["VALUES"] == {}


def test_stale_node_does_not_restore_cursor(tmp_path):
    state = storage_functions(tmp_path)
    state["init_state"]()
    with sqlite3.connect(state["DB_PATH"]) as db:
        db.execute(
            "INSERT INTO conversations VALUES (?, ?, ?, ?)",
            (12, 34, "removed", "{}"),
        )
    state["init_state"]()
    assert (12, 34) not in state["CURSORS"]


def test_runtime_uses_storage_on_start_and_mutation():
    tree = ast.parse(_RUNTIME_SOURCE)
    assert any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
               and node.func.id == "init_state" for node in ast.walk(
                   next(node for node in tree.body if isinstance(node, ast.AsyncFunctionDef)
                        and node.name == "main")
               ))
    assert _RUNTIME_SOURCE.count("save_state(") >= 8
