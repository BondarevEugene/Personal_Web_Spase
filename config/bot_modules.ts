# ==============================================================================
# PROJECT: PERSONAL_WEB_SPACE
# LOCATION: /config/bot_modules.ts
# VERSION: 1.1.0
# LAST MODIFIED: 2026-05-02
# DESCRIPTION: Полный реестр (51 модуль) для конструктора Telegram-ботов.
# PURPOSE: Централизованное хранение метаданных для UI и генератора кода.
# DEPENDENCIES: lucide-react
# AUTHORS: Human & AI Collaboration
# STATUS: Production
# ==============================================================================

import {
  Globe, Mic, ShoppingCart, Percent, Share2, ShieldCheck,
  Database, MessageSquare, CreditCard, MapPin, Bell, Cpu,
  Search, Gift, Calendar, Mail, Terminal, Lock, Star,
  Volume2, Image, Layout, List, Hash, RefreshCcw,
  Zap, BarChart3, HelpCircle, UserCheck, Trash2,
  Target, PenTool, Layers, FileText, Smartphone,
  CloudLightning, Key, Eye, Clock, PieChart,
  Navigation, Truck, CheckCircle, Smile, Settings,
  Briefcase, Activity, HardDrive, QrCode, Filter
} from 'lucide-react';

export const ALL_MODULES = [
  // --- 1. CORE & UI (База и Интерфейс) ---
  { id: 'welcome', cat: 'core', label: 'Welcome Core', icon: MessageSquare, desc: 'Приветствие и базовая инициализация пользователя' },
  { id: 'menu', cat: 'core', label: 'Persistent Menu', icon: List, desc: 'Постоянное нижнее меню навигации' },
  { id: 'commands', cat: 'core', label: 'Command Customizer', icon: Terminal, desc: 'Создание кастомных команд управления' },
  { id: 'lang', cat: 'core', label: 'Multi-Language', icon: Globe, desc: 'Динамическая смена языков интерфейса' },
  { id: 'inline_search', cat: 'core', label: 'Inline Search', icon: Search, desc: 'Поиск товаров/контента в строке ввода' },
  { id: 'help', cat: 'core', label: 'Auto-Help System', icon: HelpCircle, desc: 'Интерактивная справка по функциям бота' },
  { id: 'deeplink', cat: 'core', label: 'Deep Linking', icon: Hash, desc: 'Обработка реферальных и маркетинговых ссылок' },

  // --- 2. AI & SMART (Интеллект и Нейросети) ---
  { id: 'rag', cat: 'ai', label: 'RAG Knowledge', icon: Database, desc: 'Ответы по вашей базе документов (PDF/Docs)' },
  { id: 'voice_to_text', cat: 'ai', label: 'Voice-to-Text', icon: Mic, desc: 'Распознавание голосовых сообщений клиента' },
  { id: 'text_to_speech', cat: 'ai', label: 'Text-to-Speech', icon: Volume2, desc: 'Озвучивание текстовых ответов бота' },
  { id: 'ai_gen', cat: 'ai', label: 'AI Image Gen', icon: Image, desc: 'Генерация изображений (мебель/дизайн) через DALL-E' },
  { id: 'sentiment', cat: 'ai', label: 'Sentiment Analysis', icon: Smile, desc: 'Анализ настроения и тональности клиента' },
  { id: 'context', cat: 'ai', label: 'Context Manager', icon: Layers, desc: 'Умное сохранение истории и контекста беседы' },
  { id: 'summary', cat: 'ai', label: 'Auto-Summary', icon: FileText, desc: 'Краткое содержание диалога для администратора' },

  // --- 3. E-COMMERCE & PAY (Продажи и Платежи) ---
  { id: 'catalog', cat: 'shop', label: 'Visual Catalog', icon: Layout, desc: 'Галерея товаров с инлайн-кнопками' },
  { id: 'cart', cat: 'shop', label: 'Smart Basket', icon: ShoppingCart, desc: 'Корзина с расчетом параметров заказа' },
  { id: 'pay_stars', cat: 'shop', label: 'TG Stars Pay', icon: Star, desc: 'Прием платежей в валюте Telegram Stars' },
  { id: 'pay_crypto', cat: 'shop', label: 'Crypto Gateway', icon: CloudLightning, desc: 'Прием оплаты в TON, USDT и BTC' },
  { id: 'promo', cat: 'shop', label: 'Promo Engine', icon: Gift, desc: 'Система скидок, купонов и акций' },
  { id: 'stock', cat: 'shop', label: 'Stock Controller', icon: RefreshCcw, desc: 'Авто-скрытие позиций при отсутствии на складе' },
  { id: 'invoice', cat: 'shop', label: 'Invoice Gen', icon: FileText, desc: 'Генерация счетов на оплату в PDF' },
  { id: 'upsell', cat: 'shop', label: 'Upsell Logic', icon: Zap, desc: 'Рекомендация сопутствующих товаров' },

  // --- 4. MARKETING & RETENTION (Маркетинг) ---
  { id: 'broadcast', cat: 'marketing', label: 'Broadcast Pro', icon: Bell, desc: 'Рассылки с сегментацией по интересам' },
  { id: 'ab_test', cat: 'marketing', label: 'A/B Tester', icon: Target, desc: 'Тестирование разных офферов и воронок' },
  { id: 'referral', cat: 'marketing', label: 'Referral System', icon: Share2, desc: 'Многоуровневая партнерская программа' },
  { id: 'loyalty', cat: 'marketing', label: 'Loyalty Cards', icon: Smartphone, desc: 'Виртуальная карта и накопление баллов' },
  { id: 'retention', cat: 'marketing', label: 'Retention Bot', icon: Activity, desc: 'Возврат клиентов, забросивших воронку' },
  { id: 'quiz', cat: 'marketing', label: 'Quiz Builder', icon: PenTool, desc: 'Квизы для квалификации лидов' },
  { id: 'story', cat: 'marketing', label: 'Story-telling', icon: BookOpenCheck, desc: 'Пошаговый прогрев через серию постов' },

  // --- 5. LOGIC & INTEGRATION (Интеграции) ---
  { id: 'google_sheets', cat: 'logic', label: 'Sheets Sync', icon: Database, desc: 'Запись заказов в Google Таблицы' },
  { id: 'crm', cat: 'logic', label: 'CRM Connector', icon: Lock, desc: 'Передача лидов в Bitrix24 / amoCRM' },
  { id: 'webview', cat: 'logic', label: 'Mini App Interface', icon: Smartphone, desc: 'Запуск внешних веб-форм внутри бота' },
  { id: 'webhook', cat: 'logic', label: 'Zapier Webhook', icon: Zap, desc: 'Связь с Zapier, Make или Pipedream' },
  { id: 'email', cat: 'logic', label: 'Email Bridge', icon: Mail, desc: 'Дублирование заявок на электронную почту' },
  { id: 'calendar', cat: 'logic', label: 'Calendar Booking', icon: Calendar, desc: 'Бронирование времени (Google Calendar)' },
  { id: 'parser', cat: 'logic', label: 'Live Parser', icon: Filter, desc: 'Подгрузка цен или новостей с сайтов' },

  // --- 6. ADMIN & SUPPORT (Управление) ---
  { id: 'livechat', cat: 'admin', label: 'Live Chat Bridge', icon: MessageSquare, desc: 'Переключение клиента на оператора' },
  { id: 'tickets', cat: 'admin', label: 'Ticket System', icon: Briefcase, desc: 'Система тикетов для службы поддержки' },
  { id: 'admin_panel', cat: 'admin', label: 'Admin Dashboard', icon: Settings, desc: 'Внутреннее управление ботом из чата' },
  { id: 'antispam', cat: 'admin', label: 'Anti-Flood', icon: ShieldCheck, desc: 'Защита системы от спам-атак' },
  { id: 'logger', cat: 'admin', label: 'Action Logger', icon: Eye, desc: 'Логирование действий пользователей' },
  { id: 'stats', cat: 'admin', label: 'Bot Analytics', icon: BarChart3, desc: 'Детальная статистика использования модулей' },
  { id: 'feedback', cat: 'admin', label: 'Feedback Stars', icon: Star, desc: 'Сбор оценок качества обслуживания' },

  // --- 7. GEO & DELIVERY (Логистика) ---
  { id: 'geo_picker', cat: 'geo', label: 'Geo Picker', icon: Navigation, desc: 'Автоопределение адреса по геолокации' },
  { id: 'distance', cat: 'geo', label: 'Distance Calc', icon: Activity, desc: 'Расчет стоимости доставки от склада' },
  { id: 'pickup', cat: 'geo', label: 'Pickup Points', icon: MapPin, desc: 'Выбор пунктов самовывоза на карте' },
  { id: 'tracking', cat: 'geo', label: 'Order Tracking', icon: Truck, desc: 'Проверка статуса доставки по номеру' },

  // --- 8. UTILS & EXTRA (Утилиты) ---
  { id: 'weather', cat: 'utils', label: 'Weather Info', icon: CloudLightning, desc: 'Информер погоды для планирования' },
  { id: 'qr_gen', cat: 'utils', label: 'QR Generator', icon: QrCode, desc: 'Создание QR-кодов внутри бота' },
  { id: 'reminders', cat: 'utils', label: 'Reminder Bot', icon: Clock, desc: 'Создание уведомлений для пользователя' },
  { id: 'polls', cat: 'utils', label: 'Poll Expert', icon: PieChart, desc: 'Создание сложных опросов с графиками' }
];