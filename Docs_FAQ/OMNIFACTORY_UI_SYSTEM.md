Это единая система проектирования всего портала.

После него любой новый экран будет делаться в одном стиле.

Любой разработчик сможет открыть документ и понять:

как делать страницы;
какие использовать компоненты;
какие отступы;
какие цвета;
как строить интерфейс;
как писать HTML.

Это документ уровня Figma Design System, но адаптированный под FastAPI/Jinja2.

OMNIFACTORY PLATFORM
UI / UX DESIGN SYSTEM
Version 1.0
1. Философия проекта
Что такое OMNIFACTORY

OMNIFACTORY — это не корпоративный сайт.

Не CRM.

Не конструктор ботов.

Не AI Assistant.

OMNIFACTORY — это Enterprise Automation Platform, объединяющая инструменты разработки, автоматизации, управления проектами, искусственного интеллекта и цифровой трансформации бизнеса в единую экосистему.

Сайт является только входной точкой.

Портал является рабочим пространством.

Builder является инженерной средой.

Runtime является исполнительным ядром.

Все компоненты должны восприниматься пользователем как единая система.

2. Основные принципы дизайна

Интерфейс должен создавать ощущение:

дорогого программного продукта;
инженерной точности;
высокой надежности;
спокойствия;
контроля;
профессионализма.

Мы сознательно избегаем агрессивного "хакерского" визуального стиля.

Вместо этого используется современный корпоративный минимализм с технологическими акцентами.

3. Вдохновение

Основные ориентиры:

OpenAI
JetBrains
Linear
Vercel
Stripe
Apple
GitHub Dark
Notion

Не копировать.

Использовать как ориентир качества.

4. Стиль
Тема

Только Dark Theme.

Light Theme может появиться позже.

Атмосфера

Не Cyberpunk.

Не Matrix.

Не Hacker.

А

Enterprise Technology

5. Цветовая палитра
Background
Primary Background

#07090D
Secondary Background

#0D1117
Panels

#141922
Cards

#181F2A
Borders
#2B3442
Typography

Primary

#F3F4F6

Secondary

#B3BDC9

Muted

#6D7786
Accent

Primary Blue

#3B82F6

Primary Violet

#8B5CF6

Success

#22C55E

Warning

#F59E0B

Danger

#EF4444
6. Типографика

Основной шрифт

Inter

Инженерный

JetBrains Mono

Размеры

H1

56

H2

42

H3

32

H4

24

Body

16

Small

14

Caption

12
7. Скругления
Buttons

10px

Cards

14px

Panels

18px

Dialogs

20px
8. Тени

Очень мягкие.

Без Glow.

Без Neon.

Максимум

box-shadow:
0 12px 40px rgba(0,0,0,.25);
9. Контейнер

Максимальная ширина

1440px

Рабочая

1320px

Контент никогда

не касается краев.

10. Сетка

Используем

12-column grid

11. Отступы

Все кратно

8px

Система

8

16

24

32

48

64

96
12. Кнопки

Только четыре вида.

Primary

Secondary

Ghost

Danger

Никаких других.

13. Карточки

Все карточки одинаковые.

Содержат

иконку

↓

заголовок

↓

описание

↓

действия
14. Навигация

Всегда одинаковая.

LOGO

Solutions

Products

Projects

Technology

About

Contacts

Portal

Справа

Login

↓

Book Meeting
15. Hero

Каждая Landing

имеет Hero.

Состав

Badge

↓

Title

↓

Subtitle

↓

Buttons

↓

Preview

↓

Statistics
16. Иконки

Используем только

Lucide Icons

Никаких PNG.

17. Анимации

Продолжительность

150ms

200ms

250ms

Без прыжков.

Без мигания.

Без бесконечных эффектов.

18. Компоненты

Создаем собственную библиотеку.

OFButton

OFCard

OFHero

OFSection

OFBadge

OFInput

OFSelect

OFDialog

OFSidebar

OFNavbar

OFStats

OFTimeline

OFFeatureCard

OFProjectCard

OFTerminal

OFDashboardWidget

Все страницы используют только эти компоненты.

19. Архитектура HTML
base.html

↓

layout

↓

components

↓

page

Никакого копирования кода.

20. Архитектура CSS
reset.css

↓

variables.css

↓

typography.css

↓

layout.css

↓

components.css

↓

animations.css

↓

page.css
21. Архитектура JS
core.js

↓

api.js

↓

navigation.js

↓

animations.js

↓

page.js
22. Принцип разработки

Каждый новый экран обязан отвечать на три вопроса:

Понятно ли пользователю, где он находится?
Может ли он попасть в любую важную часть системы максимум за два клика?
Выглядит ли экран как часть OMNIFACTORY, а не как отдельный проект?

Если хотя бы на один вопрос ответ "нет", экран считается незавершённым.

23. Цель версии 1.0

Создать единый визуальный язык, который позволит безболезненно объединить:

корпоративный сайт;
портал клиентов;
Builder;
CRM;
AI-модули;
Dashboard;
Runtime;
будущие продукты (например, Genesis).
