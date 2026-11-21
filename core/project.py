# ==============================================================================
# PROJECT: OMNIFACTORY PLATFORM
# MODULE: Project Model
# FILE: core/project.py
# VERSION: 2.0 Enterprise
# ==============================================================================
## DESCRIPTION
# ------------------------------------------------------------------------------
# ProjectModel является центральной моделью всей платформы.
# Любой сервис работает именно с этим объектом.
#
# Builder
# Compiler
# Runtime
# Export
# Marketplace
# AI
#
# ==============================================================================

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4


@dataclass(slots=True)
class ProjectModel:

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    id: str = field(default_factory=lambda: str(uuid4()))
    created: datetime = field(default_factory=datetime.utcnow)
    name: str = "Untitled Project"
    description: str = ""
    version: str = "1.0.0"

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    runtime: str = "python"
    target: str = "telegram"

    # ------------------------------------------------------------------
    # Builder
    # ------------------------------------------------------------------

    nodes: list[dict[str, Any]] = field(default_factory=list)
    connections: list[dict[str, Any]] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Registry
    # ------------------------------------------------------------------

    modules: list[dict[str, Any]] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Components
    # ------------------------------------------------------------------

    components: list[dict[str, Any]] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Sources
    # ------------------------------------------------------------------

    files: list[str] = field(default_factory=list)
    directories: list[str] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    metadata: dict[str, Any] = field(default_factory=dict)
    settings: dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------

    def add_module(self, module):
        self.modules.append(module)

    # ------------------------------------------------------------------

    def add_component(self, component):
        self.components.append(component)

    # ------------------------------------------------------------------

    def add_file(self, filename):
        if filename not in self.files:
            self.files.append(filename)

    # ------------------------------------------------------------------

    def add_directory(self, directory):
        if directory not in self.directories:
            self.directories.append(directory)
