import React, { useState, useMemo } from 'react';
import * as Icons from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// --- ДИНАМИЧЕСКИЙ КАТАЛОГ БИБЛИОТЕК (МАСШТАБИРУЕМЫЙ) ---
const LIBRARY_RESOURCES = [
  { id: 'db_pg', label: 'PostgreSQL_Stream', cat: 'ИНФРАСТРУКТУРА', icon: 'Database', desc: 'Высокопроизводительное хранилище данных.' },
  { id: 'db_redis', label: 'Redis_Cache', cat: 'ИНФРАСТРУКТУРА', icon: 'Zap', desc: 'Мгновенный кэш для сессий пользователей.' },
  { id: 'api_crm', label: 'Bitrix24_Link', cat: 'ИНТЕГРАЦИИ', icon: 'Link', desc: 'Авто-передача лидов в вашу CRM.' },
  { id: 'api_amo', label: 'amoCRM_Sync', cat: 'ИНТЕГРАЦИИ', icon: 'RefreshCw', desc: 'Синхронизация сделок и воронки продаж.' },
  { id: 'ai_gpt4', label: 'GPT-4_Turbo', cat: 'ИНТЕЛЛЕКТ', icon: 'Brain', desc: 'Нейросетевое мышление для сложных задач.' },
  { id: 'ai_whisper', label: 'Whisper_Voice', cat: 'ИНТЕЛЛЕКТ', icon: 'Mic', desc: 'Перевод голосовых сообщений в текст.' },
  { id: 'biz_sales', label: 'Sales_Funnel', cat: 'БИЗНЕС-ЛОГИКА', icon: 'BarChart3', desc: 'Сценарий прогрева и дожима клиента.' },
  { id: 'biz_ecom', label: 'E-com_Engine', cat: 'БИЗНЕС-ЛОГИКА', icon: 'ShoppingBag', desc: 'Полный цикл: от корзины до чека.' },
];

const CATEGORIES = ['ВСЕ', 'ИНФРАСТРУКТУРА', 'ИНТЕГРАЦИИ', 'ИНТЕЛЛЕКТ', 'БИЗНЕС-ЛОГИКА'];

export const BotBuilder = () => {
  const [activeView, setActiveView] = useState<'ARCHITECT' | 'DEPLOY'>('ARCHITECT');
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('ВСЕ');
  const [selectedNodes, setSelectedNodes] = useState<string[]>(['db_pg']);
  const [inspectId, setInspectId] = useState<string | null>('db_pg');

  // Фильтрация библиотек
  const filteredLibrary = useMemo(() => {
    return LIBRARY_RESOURCES.filter(m =>
      (filter === 'ВСЕ' || m.cat === filter) &&
      (m.label.toLowerCase().includes(search.toLowerCase()) || m.desc.toLowerCase().includes(search.toLowerCase()))
    );
  }, [search, filter]);

  const inspected = useMemo(() => LIBRARY_RESOURCES.find(m => m.id === inspectId), [inspectId]);

  return (
    <div className="h-screen w-full bg-[#020202] text-white flex overflow-hidden font-sans">

      {/* 1. ЛЕВАЯ ПАНЕЛЬ: ГЛОБАЛЬНЫЙ КАТАЛОГ (30% ширины) */}
      <aside className="w-[30%] border-r border-white/5 bg-zinc-900/20 flex flex-col p-6 shadow-2xl z-10">
        <div className="mb-8">
          <h1 className="text-4xl font-black italic tracking-tighter uppercase mb-2">FACTORY<span className="text-orange-500">_IDE</span></h1>
          <p className="text-[10px] text-zinc-500 font-mono tracking-widest">ECOSYSTEM ACCESS V.9.4.1</p>
        </div>

        {/* ПОИСК И ФИЛЬТРЫ */}
        <div className="space-y-4 mb-8">
          <div className="relative">
            <Icons.Search className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-500" size={18} />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Поиск по 500,000+ модулей..."
              className="w-full bg-black border border-white/10 rounded-2xl py-4 pl-12 pr-4 text-sm font-bold focus:border-orange-500 outline-none transition-all"
            />
          </div>
          <div className="flex flex-wrap gap-2">
            {CATEGORIES.map(c => (
              <button
                key={c}
                onClick={() => setFilter(c)}
                className={`px-3 py-1.5 rounded-full text-[10px] font-black tracking-tight transition-all ${filter === c ? 'bg-orange-500 text-black shadow-lg shadow-orange-500/20' : 'bg-white/5 text-zinc-500 hover:text-white'}`}
              >
                {c}
              </button>
            ))}
          </div>
        </div>

        {/* СПИСОК МОДУЛЕЙ (Скролл) */}
        <div className="flex-1 overflow-y-auto space-y-3 pr-2 custom-scrollbar">
          {filteredLibrary.map(m => {
            const Icon = (Icons as any)[m.icon];
            const isAdded = selectedNodes.includes(m.id);
            return (
              <div
                key={m.id}
                onClick={() => { setInspectId(m.id); if(!isAdded) setSelectedNodes([...selectedNodes, m.id]); }}
                className={`p-4 rounded-3xl border-2 transition-all cursor-pointer group flex items-center gap-4 ${isAdded ? 'border-orange-500 bg-orange-500/5' : 'border-white/5 bg-zinc-900/40 hover:border-white/10'}`}
              >
                <div className={`p-3 rounded-2xl ${isAdded ? 'bg-orange-500 text-black' : 'bg-black text-zinc-600 group-hover:text-white'}`}>
                  <Icon size={22} />
                </div>
                <div className="flex-1">
                  <h4 className="text-sm font-black uppercase tracking-tight">{m.label}</h4>
                  <p className="text-[10px] text-zinc-500 truncate">{m.desc}</p>
                </div>
                {isAdded && <Icons.CheckCircle2 className="text-orange-500" size={18} />}
              </div>
            );
          })}
        </div>

        <div className="mt-4 pt-4 border-t border-white/5 text-[10px] text-zinc-700 flex justify-between uppercase font-black">
          <span>Ecosystem: Stable</span>
          <span>Nodes: 512,042</span>
        </div>
      </aside>

      {/* 2. ЦЕНТРАЛЬНАЯ ЧАСТЬ: MIND MAP (Крупный масштаб) */}
      <main className="flex-1 bg-black relative flex flex-col overflow-hidden">

        {/* Хедер управления видом */}
        <div className="h-20 border-b border-white/5 flex items-center justify-between px-10 bg-zinc-900/10">
          <div className="flex gap-8">
            <button onClick={() => setActiveView('ARCHITECT')} className={`text-xs font-black uppercase tracking-widest ${activeView === 'ARCHITECT' ? 'text-orange-500' : 'text-zinc-600'}`}>Архитектор</button>
            <button onClick={() => setActiveView('DEPLOY')} className={`text-xs font-black uppercase tracking-widest ${activeView === 'DEPLOY' ? 'text-orange-500' : 'text-zinc-600'}`}>Развертывание</button>
          </div>
          <div className="text-[10px] font-mono text-orange-500 bg-orange-500/10 px-4 py-1 rounded-full">PROJECT_UUID: {Math.random().toString(16).slice(2, 10).toUpperCase()}</div>
        </div>

        {activeView === 'ARCHITECT' ? (
          <div className="flex-1 relative overflow-auto custom-scrollbar p-20 flex items-center gap-24 min-w-max">
            {selectedNodes.map((id, index) => {
              const m = LIBRARY_RESOURCES.find(mod => mod.id === id);
              if (!m) return null;
              return (
                <motion.div
                  key={id} layout
                  initial={{ scale: 0.5, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
                  className={`w-80 h-[450px] shrink-0 rounded-[4rem] border-4 p-10 flex flex-col relative transition-all ${inspectId === id ? 'border-orange-500 bg-zinc-900 shadow-[0_0_60px_rgba(249,115,22,0.15)]' : 'border-white/5 bg-zinc-900/40'}`}
                  onClick={() => setInspectId(id)}
                >
                  <div className="text-[10px] font-black text-zinc-600 mb-6 tracking-widest">MODULE_ID: {index}</div>
                  <h3 className="text-3xl font-black italic uppercase leading-none mb-8 truncate">{m.label}</h3>

                  <div className="flex-1 bg-black/40 rounded-[2.5rem] p-6 border border-white/5 flex flex-col justify-center">
                    <div className="text-center italic text-zinc-500 text-sm mb-4">"Пропишите сценарий взаимодействия для этой ноды"</div>
                    <div className="h-1 w-12 bg-orange-500 mx-auto" />
                  </div>

                  {/* Коннекторы (стрелки) */}
                  {index < selectedNodes.length - 1 && (
                    <div className="absolute -right-24 top-1/2 -translate-y-1/2 flex items-center">
                      <div className="w-24 h-1 bg-orange-500/20" />
                      <Icons.ChevronRight size={24} className="text-orange-500/50 -ml-4" />
                    </div>
                  )}
                </motion.div>
              );
            })}
          </div>
        ) : (
          /* ДЕПЛОЙ ЭКРАН */
          <div className="flex-1 flex flex-col items-center justify-center p-20 text-center">
             <Icons.Cpu size={80} className="text-orange-500 mb-8" />
             <h2 className="text-6xl font-black italic uppercase mb-6">Интеграция Фабрики</h2>
             <p className="max-w-2xl text-xl text-zinc-500 leading-relaxed mb-12 italic">Система автоматически подготовит Docker-контейнер, настроит SSL и развернет вашу архитектуру на защищенных узлах WebFactory Cloud.</p>
             <button className="px-20 py-8 bg-white text-black font-black text-3xl uppercase tracking-tighter rounded-full hover:bg-orange-500 transition-all">Запустить деплой</button>
          </div>
        )}

        {/* Панель экспорта (Футер) */}
        <div className="p-10 border-t border-white/5 bg-black flex justify-between items-center">
          <div>
            <div className="text-[10px] font-black text-zinc-700 uppercase mb-1">Сложность проекта:</div>
            <div className="text-2xl font-black italic uppercase">{selectedNodes.length} Уровней / {selectedNodes.length * 4} API-связей</div>
          </div>
          <button className="bg-orange-500 hover:bg-orange-400 text-black px-16 py-6 rounded-3xl font-black text-2xl uppercase tracking-widest shadow-2xl transition-all active:scale-95">Скомпилировать</button>
        </div>
      </main>

      {/* 3. ПРАВАЯ ПАНЕЛЬ: ГЛУБОКИЙ ИНСПЕКТОР (Управление диалогом) */}
      <aside className="w-[30%] border-l border-white/5 bg-zinc-900/20 p-12 flex flex-col overflow-hidden">
        <AnimatePresence mode="wait">
          {inspected ? (
            <motion.div key={inspected.id} initial={{ x: 100, opacity: 0 }} animate={{ x: 0, opacity: 1 }} className="h-full flex flex-col">
              <div className="mb-12">
                <span className="text-orange-500 font-black text-[10px] tracking-[0.4em] uppercase">{inspected.cat}</span>
                <h2 className="text-5xl font-black italic uppercase text-white tracking-tighter leading-none mt-2 mb-6">{inspected.label}</h2>
                <p className="text-lg text-zinc-500 leading-snug italic">"{inspected.desc}"</p>
              </div>

              {/* УПРАВЛЕНИЕ ЛОГИКОЙ (КРУПНЫЕ ШРИФТЫ) */}
              <div className="flex-1 space-y-10 overflow-y-auto pr-4 custom-scrollbar">
                <div className="space-y-4">
                  <label className="text-xs font-black text-zinc-700 uppercase tracking-widest">Текст сообщения бота:</label>
                  <textarea
                    placeholder="Напишите, что бот должен ответить в этой ноде..."
                    className="w-full h-48 bg-black border-2 border-white/5 rounded-[3rem] p-8 text-xl font-bold text-white focus:border-orange-500 outline-none resize-none transition-all"
                  />
                </div>

                <div className="space-y-4">
                  <label className="text-xs font-black text-zinc-700 uppercase tracking-widest">Кнопки действий:</label>
                  <div className="grid grid-cols-1 gap-3">
                    <div className="p-5 bg-white/5 rounded-2xl border border-white/10 flex justify-between items-center group hover:border-orange-500/50">
                      <span className="text-sm font-black uppercase tracking-tight">Перейти в каталог</span>
                      <Icons.Trash2 size={16} className="text-zinc-800 group-hover:text-red-500 cursor-pointer" />
                    </div>
                    <button className="w-full py-5 border-2 border-dashed border-orange-500/20 text-orange-500 font-black text-xs uppercase tracking-widest rounded-2xl">+ Добавить кнопку</button>
                  </div>
                </div>
              </div>

              <button
                onClick={() => setSelectedNodes(selectedNodes.filter(n => n !== inspected.id))}
                className="mt-10 py-6 text-red-500 font-black uppercase text-xs tracking-widest border border-red-500/20 rounded-2xl hover:bg-red-500/10 transition-all"
              >
                Исключить из архитектуры
              </button>
            </motion.div>
          ) : (
            <div className="h-full flex items-center justify-center text-center opacity-20 italic text-2xl font-black uppercase p-10 border-4 border-dashed border-white/10 rounded-[4rem]">
              Выберите узел<br/>для настройки
            </div>
          )}
        </AnimatePresence>
      </aside>
    </div>
  );
};