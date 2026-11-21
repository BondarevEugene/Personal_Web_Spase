# GENESIS HR® // GEN-OS

# Knowledge Graph Kernel

Version 1.0 Draft

---

## Purpose

Knowledge Graph Kernel является центральным ядром платформы GEN-OS.

Он представляет собой семантический граф знаний,
используемый всеми сервисами платформы.

Knowledge Registry

↓

Knowledge Graph

↓

Prediction Engine

↓

Recommendation Engine

↓

Career Engine

↓

Simulation Engine

↓

AI Reasoning

---

Status

IN DESIGN
# Responsibilities

Graph отвечает только за:

- хранение узлов

- хранение связей

- индексацию

- поиск

- обход

- построение подграфов

- статистику

- экспорт

- валидацию

Graph НЕ отвечает за:

- импорт

- рекомендации

- предсказания

- карьеру

- AI

- UI
- # Entity Types
- Profession

Skill

Competency

Knowledge

Course

Vacancy

Human

Tool

Task

Ability

Trait

Language

Education

Certificate

Project

Company

Industry

Technology

Concept

# Relation Types
REQUIRES

HAS_SKILL

HAS_COMPETENCY

DEVELOPS

RECOMMENDS

BELONGS_TO

PART_OF

SIMILAR_TO

RELATED_TO

USES

CREATED_BY

DEPENDS_ON

NEXT_STEP

PREVIOUS_STEP

CAN_BECOME

WORKS_WITH

LOCATED_IN

ALTERNATIVE_TO

