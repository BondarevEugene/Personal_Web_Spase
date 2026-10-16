Sprint 1
Создаем фундамент

Документы

docs/

UI_SYSTEM.md               ✔

PORTAL_ARCHITECTURE.md

DEVELOPMENT_GUIDE.md

CODING_STANDARD.md

ROADMAP.md

Потом

templates/

base.html

layouts/

landing.html

portal.html

components/

navbar.html

hero.html

footer.html

button.html

card.html

stats.html

cta.html

Потом

static/

css/

variables.css

reset.css

typography.css

layout.css

components.css

landing.css

animations.css

theme.css

Потом

js/

core.js

api.js

navigation.js

animations.js

landing.js
Sprint 2

Создаем новую Landing.

Не переделываем.

Пишем новую.

Я ее уже вижу.

──────────────────────────────

Navigation

──────────────────────────────

Hero

"Complexity Engineered"

──────────────────────────────

Наши решения

──────────────────────────────

Как мы работаем

──────────────────────────────

Технологии

──────────────────────────────

Наши проекты

──────────────────────────────

Почему OmniFactory

──────────────────────────────

CTA

──────────────────────────────

Footer
Sprint 3

Начинается портал.

Portal

↓

Dashboard

↓

Projects

↓

CRM

↓

Builder

↓

AI

↓

Settings
Sprint 4

Builder

Полностью приводим к новой архитектуре.

Sprint 5

Runtime

Sprint 6

Deploy

Sprint 7

PWA

Sprint 8

Android

Теперь самое главное.
Я придумал правило проекта.

Оно будет называться

Zero Technical Debt Policy

Смысл простой.

Мы НИКОГДА больше не будем писать код

который

"потом перепишем."

Любой новый файл

сразу

делается

как Production.

Второе правило.

Никаких файлов

по 1500 строк.

Максимум

300-400 строк.

Если больше —

разбиваем.

Третье правило.

Вообще запрещаем

<style>

<script>

в HTML.

Все

только

через

static/
Четвертое правило.

Каждый HTML

обязан выглядеть так

extends

↓

components

↓

content

↓

scripts

Никаких

2000 строк html.

Пятое правило.

Теперь начинается самое интересное.

Мы НЕ будем делать

"страницы"

Мы будем делать

КОМПОНЕНТЫ.

Например.

Один раз делаем

OFButton

И потом

используем

везде.

Потом

OFCard

Используем

везде.

Потом

OFHero

Используем

везде.

В итоге

через месяц

весь портал

будет состоять

из

примерно

40 компонентов.

Это именно так строятся большие продукты.

Еще одна идея.

Мне кажется,

нам нужен

OmniFactory Component Catalog

Что-то вроде Storybook, но без React.

/components

↓

Button

↓

Card

↓

Input

↓

Dialog

↓

Hero

↓

Sidebar

↓

Navbar

И можно открыть

любой компонент

отдельно.