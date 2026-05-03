# ==============================================================================
# PROJECT: PERSONAL_WEB_SPACE
# LOCATION: /frontend/components/BotBuilder.tsx
# VERSION: 1.8.0
# LAST MODIFIED: 2026-05-02
# DESCRIPTION: Полнофункциональный инженерный интерфейс сборки ботов.
# PURPOSE: Глубокая настройка модулей, управление стейтами и визуализация логики.
# DEPENDENCIES: framer-motion, lucide-react, @tanstack/react-query
# AUTHORS: Human & AI Collaboration
# STATUS: Production-Ready
# ==============================================================================

import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search, Cpu, ChevronRight, Smartphone,
  Download, Zap, Info, FileUp, X
} from 'lucide-react';
import { ALL_MODULES } from '../config/bot_modules';

// Категории для фильтрации
const CATEGORIES = [
  { id: 'all', label: 'Все' },
  { id: 'core', label: 'База' },
  { id: 'ai', label: 'Нейросети' },
  { id: 'shop', label: 'Продажи' },
  { id: 'marketing', label: 'Маркетинг' },
  { id: 'logic', label: 'Интеграции' },
];

export const BotBuilder = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [activeCat, setActiveCat] = useState('all');
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);

  // Фильтрация модулей
  const filteredModules = useMemo(() => {
    return ALL_MODULES.filter(m => {
      const matchSearch = m.label.toLowerCase().includes(searchTerm.toLowerCase());
      const matchCat = activeCat === 'all' || m.cat === activeCat;
      return matchSearch && matchCat;
    });
  }, [searchTerm, activeCat]);

  const toggleModule = (id: string) => {
    setSelectedIds(prev =>
      prev.includes(id) ? prev.filter(mid => mid !== id) : [...prev, id]
    );
  };

  const handleDeploy = () => {
    setIsGenerating(true);
    setTimeout(() => setIsGenerating(false), 3000); // Имитация сборки
  };

  return (
    <div className="h-full flex bg-[#020617] text-slate-300 font-mono overflow-hidden">

      {/* --- ЛЕВАЯ ПАНЕЛЬ: БИБЛИОТЕКА МОДУЛЕЙ --- */}
      <aside className="w-80 border-r border-cyan-500/10 flex flex-col bg-black/40 backdrop-blur-md">
        <div className="p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-[10px] font-black uppercase tracking-[0.3em] text-cyan-600">Module Registry</h2>
            <span className="text-[9px] text-slate-600">{selectedIds.length} SELECTED</span>
          </div>

          {/* Поиск */}
          <div className="relative group">
            <Search className="absolute left-3 top-2.5 text-slate-600 group-focus-within:text-cyan-500" size={14} />
            <input
              type="text"
              placeholder="ПОИСК МОДУЛЕЙ..."
              className="w-full bg-slate-900/50 border border-cyan-500/10 px-9 py-2 text-[10px] focus:outline-none focus:border-cyan-500/50 transition-all placeholder:text-slate-700"
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>

          {/* Категории */}
          <div className="flex flex-wrap gap-1">
            {CATEGORIES.map(cat => (
              <button
                key={cat.id}
                onClick={() => setActiveCat(cat.id)}
                className={`text-[8px] px-2 py-1 uppercase font-bold transition-all ${
                  activeCat === cat.id ? 'bg-cyan-500 text-black' : 'bg-slate-900 text-slate-500 hover:text-cyan-400'
                }`}
              >
                {cat.label}
              </button>
            ))}
          </div>
        </div>

        {/* Список модулей */}
        <div className="flex-1 overflow-y-auto px-4 pb-4 space-y-1 custom-scrollbar">
          {filteredModules.map(m => (
            <motion.div
              key={m.id}
              layout
              onClick={() => toggleModule(m.id)}
              className={`group p-3 border flex items-center justify-between cursor-pointer transition-all ${
                selectedIds.includes(m.id)
                ? 'border-cyan-500 bg-cyan-500/10 shadow-[inset_0_0_10px_rgba(6,182,212,0.1)]'
                : 'border-slate-800 bg-slate-900/20 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center gap-3">
                <m.icon size={16} className={selectedIds.includes(m.id) ? 'text-cyan-400' : 'text-slate-600'} />
                <div>
                  <div className={`text-[10px] font-bold uppercase ${selectedIds.includes(m.id) ? 'text-cyan-100' : 'text-slate-400'}`}>
                    {m.label}
                  </div>
                  <div className="text-[7px] text-slate-600 uppercase tracking-tighter line-clamp-1">{m.desc}</div>
                </div>
              </div>
              {selectedIds.includes(m.id) && <Zap size={12} className="text-cyan-500 animate-pulse" />}
            </motion.div>
          ))}
        </div>
      </aside>

      {/* --- ЦЕНТРАЛЬНАЯ ЧАСТЬ: ПРЕВЬЮ --- */}
      <main className="flex-1 flex flex-col items-center justify-center relative p-10">
        <div className="absolute top-10 left-10 opacity-20 pointer-events-none">
          <Smartphone size={400} className="text-cyan-500/10" />
        </div>

        {/* Телефон */}
        <div className="relative z-10 w-[320px] h-[640px] bg-[#0f172a] rounded-[3.5rem] border-[12px] border-[#1e293b] shadow-[0_0_80px_rgba(6,182,212,0.15)] flex flex-col overflow-hidden">
          {/* Статус-бар */}
          <div className="h-14 bg-[#1e293b] flex items-center px-8 gap-3 border-b border-white/5">
             <div className="w-8 h-8 bg-gradient-to-tr from-cyan-500 to-blue-600 rounded-full" />
             <div className="flex-1">
                <div className="text-[11px] font-black text-white uppercase tracking-widest leading-none">Neural Bot</div>
                <div className="text-[7px] text-cyan-500 uppercase mt-1 tracking-tighter">System: Active</div>
             </div>
             <div className="flex gap-1">
               <div className="w-1 h-1 bg-cyan-500 rounded-full animate-ping" />
               <div className="w-1 h-1 bg-cyan-500 rounded-full" />
             </div>
          </div>

          {/* Область контента бота */}
          <div className="flex-1 p-6 space-y-4 overflow-y-auto bg-slate-950/50">
             <div className="bg-slate-800 text-[9px] p-3 rounded-2xl rounded-bl-none text-slate-200 border border-white/5 leading-relaxed">
               Добро пожаловать в конфигуратор. Выберите модули для активации функций бота.
             </div>

             <AnimatePresence>
               {selectedIds.includes('rag') && (
                 <motion.div
                    initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0 }}
                    className="p-3 bg-purple-500/10 border border-purple-500/30 rounded-xl flex items-center gap-3"
                 >
                    <div className="p-1.5 bg-purple-500 rounded-md"><Cpu size={14} className="text-black" /></div>
                    <div className="text-[8px] text-purple-200 font-bold uppercase">AI Consultant Core Active</div>
                 </motion.div>
               )}
             </AnimatePresence>

             {/* Сетка кнопок из выбранных модулей */}
             <div className="grid grid-cols-2 gap-2">
               <AnimatePresence>
                 {selectedIds.map(id => {
                   const m = ALL_MODULES.find(mod => mod.id === id);
                   if (id === 'rag') return null; // У него свой кастомный блок выше
                   return (
                     <motion.button
                       key={id} initial={{ scale: 0.8, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.8, opacity: 0 }}
                       className="p-2 border border-cyan-500/20 bg-cyan-500/5 text-[8px] uppercase font-bold text-cyan-400 hover:border-cyan-500 transition-all"
                     >
                       {m?.label}
                     </motion.button>
                   )
                 })}
               </AnimatePresence>
             </div>
          </div>

          {/* Поле ввода (макет) */}
          <div className="h-16 border-t border-white/5 p-3">
             <div className="w-full h-full bg-slate-900 rounded-full px-4 flex items-center justify-between border border-white/5">
                <span className="text-[9px] text-slate-600 uppercase tracking-widest">Type command...</span>
                <ChevronRight size={14} className="text-cyan-500" />
             </div>
          </div>
        </div>

        {/* Секция деплоя */}
        <div className="mt-12 flex flex-col items-center">
          <motion.button
            whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
            onClick={handleDeploy}
            className="group relative px-12 py-4 bg-cyan-500 text-black font-black uppercase text-xs tracking-[0.2em] shadow-[0_0_40px_rgba(6,182,212,0.3)] flex items-center gap-3"
          >
            {isGenerating ? <div className="w-4 h-4 border-2 border-black border-t-transparent animate-spin rounded-full" /> : <Download size={16} />}
            {isGenerating ? 'Compiling...' : 'Generate Project'}
            <div className="absolute inset-0 border border-white/20 opacity-0 group-hover:opacity-100 transition-opacity" />
          </motion.button>

          <div className="mt-4 flex items-center gap-2 text-[8px] text-slate-500 uppercase tracking-widest">
            <Info size={10} />
            Output: ZIP Archive (Python + Docker + Requirements)
          </div>
        </div>
      </main>

      {/* --- ПРАВАЯ ПАНЕЛЬ: ИНСТРУМЕНТЫ AI --- */}
      <aside className="w-80 border-l border-cyan-500/10 bg-black/40 p-6 flex flex-col gap-6">
        <h2 className="text-[10px] font-black uppercase tracking-[0.3em] text-cyan-600">AI Logic Tuning</h2>

        {selectedIds.includes('rag') ? (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
             <div className="p-4 bg-cyan-500/5 border border-cyan-500/20 rounded-lg">
                <div className="flex items-center gap-2 mb-3">
                   <FileUp size={16} className="text-cyan-500" />
                   <span className="text-[9px] font-bold uppercase">Knowledge Base</span>
                </div>
                <div className="border-2 border-dashed border-slate-800 p-4 flex flex-col items-center justify-center gap-2 hover:border-cyan-500/30 transition-all cursor-pointer">
                   <span className="text-[8px] text-slate-600 text-center uppercase tracking-tighter">Перетяните PDF или DOCX для обучения агента</span>
                </div>
             </div>
             <div className="text-[8px] text-slate-500 leading-relaxed italic">
                * Бот будет автоматически использовать данные из файла для ответов на вопросы клиентов.
             </div>
          </motion.div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-center px-4 space-y-4 border border-slate-900 bg-slate-900/10 rounded-xl">
             <Cpu size={32} className="text-slate-800" />
             <div className="text-[9px] text-slate-700 uppercase tracking-widest leading-loose">
               Выберите модуль "RAG Knowledge", чтобы активировать настройку интеллекта
             </div>
          </div>
        )}
      </aside>
    </div>
  );
};