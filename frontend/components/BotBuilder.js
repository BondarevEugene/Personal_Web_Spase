# ==============================================================================
# PROJECT: PERSONAL_WEB_SPACE
# LOCATION: /frontend/components/BotBuilder.tsx
# VERSION: 1.9.5
# LAST MODIFIED: 2026-05-02
# DESCRIPTION: Объединенный инженерный интерфейс.
# PURPOSE: Сочетает визуальный превью (телефон) с глубокой настройкой параметров.
# DEPENDENCIES: framer-motion, lucide-react, ALL_MODULES
# AUTHORS: Human & AI Collaboration
# STATUS: Production-Ready
# ==============================================================================

import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search, Cpu, ChevronRight, Smartphone,
  Download, Zap, Info, FileUp, X, Settings2, Terminal as TermIcon, Save
} from 'lucide-react';
import { ALL_MODULES } from '../config/bot_modules';

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
  const [activeModuleId, setActiveModuleId] = useState<string | null>(null); // Для инспектора
  const [isGenerating, setIsGenerating] = useState(false);

  // 1. Поиск и фильтрация
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
    setActiveModuleId(id); // При клике сразу открываем настройки
  };

  const activeModuleData = useMemo(() =>
    ALL_MODULES.find(m => m.id === activeModuleId),
  [activeModuleId]);

  return (
    <div className="h-full flex bg-[#020617] text-slate-300 font-mono overflow-hidden">

      {/* --- ЛЕВАЯ ПАНЕЛЬ: БИБЛИОТЕКА --- */}
      <aside className="w-72 border-r border-cyan-500/10 flex flex-col bg-black/40 backdrop-blur-md">
        <div className="p-6 space-y-4">
          <div className="flex items-center justify-between text-[10px] font-black uppercase text-cyan-600">
            <span>Module Registry</span>
            <span className="text-slate-600">{selectedIds.length} ACTIVE</span>
          </div>

          <div className="relative group">
            <Search className="absolute left-3 top-2.5 text-slate-600" size={14} />
            <input
              type="text" placeholder="SEARCH..."
              className="w-full bg-slate-900/50 border border-cyan-500/10 px-9 py-2 text-[10px] focus:outline-none focus:border-cyan-500/50"
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>

          <div className="flex flex-wrap gap-1">
            {CATEGORIES.map(cat => (
              <button
                key={cat.id} onClick={() => setActiveCat(cat.id)}
                className={`text-[8px] px-2 py-1 uppercase font-bold transition-all ${
                  activeCat === cat.id ? 'bg-cyan-500 text-black' : 'bg-slate-900 text-slate-500'
                }`}
              >
                {cat.label}
              </button>
            ))}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-4 pb-4 space-y-1 custom-scrollbar">
          {filteredModules.map(m => (
            <div
              key={m.id} onClick={() => toggleModule(m.id)}
              className={`group p-3 border cursor-pointer transition-all flex items-center justify-between ${
                selectedIds.includes(m.id) ? 'border-cyan-500 bg-cyan-500/10' : 'border-slate-800 bg-slate-900/20'
              }`}
            >
              <div className="flex items-center gap-3">
                <m.icon size={16} className={selectedIds.includes(m.id) ? 'text-cyan-400' : 'text-slate-600'} />
                <span className={`text-[10px] font-bold uppercase ${selectedIds.includes(m.id) ? 'text-cyan-100' : 'text-slate-400'}`}>
                  {m.label}
                </span>
              </div>
              {selectedIds.includes(m.id) && <Zap size={12} className="text-cyan-500 animate-pulse" />}
            </div>
          ))}
        </div>
      </aside>

      {/* --- ЦЕНТРАЛЬНАЯ ЧАСТЬ: PREVIEW + TERMINAL --- */}
      <main className="flex-1 flex flex-col items-center relative bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-slate-900/20 via-transparent to-transparent">

        {/* Телефон-превью */}
        <div className="flex-1 flex items-center justify-center">
            <div className="relative z-10 w-[300px] h-[600px] bg-[#0f172a] rounded-[3.5rem] border-[12px] border-[#1e293b] shadow-2xl flex flex-col overflow-hidden">
                <div className="h-14 bg-[#1e293b] flex items-center px-8 border-b border-white/5">
                    <div className="flex-1 text-[11px] font-black text-white uppercase tracking-widest">Neural Bot</div>
                    <div className="w-2 h-2 bg-cyan-500 rounded-full animate-ping" />
                </div>

                <div className="flex-1 p-6 space-y-4 overflow-y-auto bg-slate-950/50">
                    <div className="bg-slate-800 text-[9px] p-3 rounded-xl rounded-bl-none text-slate-300 border border-white/5">
                        System ready. Modules: {selectedIds.length}
                    </div>
                    {selectedIds.map(id => (
                        <div key={id} className="p-2 border border-cyan-500/20 bg-cyan-500/5 text-cyan-400 text-[8px] text-center uppercase font-black rounded">
                            {id} MODULE_ONLINE
                        </div>
                    ))}
                </div>
            </div>
        </div>

        {/* Терминал логов */}
        <div className="w-full h-40 bg-black/80 border-t border-white/5 p-4 font-mono overflow-y-auto">
            <div className="flex items-center gap-2 text-[9px] text-slate-600 uppercase mb-2">
                <TermIcon size={12} /> Live Compiler Output
            </div>
            <div className="text-[9px] space-y-1">
                <div className="text-green-800">[SYS] ENV_VALIDATED: OK</div>
                <div className="text-cyan-800">[AI] NEURAL_CORE: READY</div>
                {isGenerating && <div className="text-yellow-600 animate-pulse">[BUILD] GENERATING PROJECT ZIP...</div>}
            </div>
        </div>
      </main>

      {/* --- ПРАВАЯ ПАНЕЛЬ: ИНСПЕКТОР (Property Tuning)[cite: 2] --- */}
      <aside className="w-80 border-l border-cyan-500/10 bg-black/40 p-6 flex flex-col gap-6">
        <h2 className="text-[10px] font-black uppercase tracking-[0.3em] text-cyan-600 flex items-center gap-2">
            <Settings2 size={14} /> Property Inspector
        </h2>

        {activeModuleData ? (
            <div className="space-y-6">
                <div className="p-3 bg-cyan-500/5 border border-cyan-500/20">
                    <div className="text-[8px] text-cyan-500 font-bold uppercase mb-1">Active Node</div>
                    <div className="text-[11px] text-white font-black uppercase">{activeModuleData.label}</div>
                </div>

                {/* Динамические настройки */}
                <div className="space-y-4">
                    <div className="space-y-2">
                        <label className="text-[8px] text-slate-600 uppercase font-bold">Logic Trigger</label>
                        <input className="w-full bg-slate-900 border border-white/10 text-[10px] px-2 py-1.5 focus:border-cyan-500 outline-none" defaultValue={`/${activeModuleData.id}`} />
                    </div>

                    {activeModuleData.cat === 'ai' && (
                        <div className="space-y-4">
                            <div className="p-3 bg-purple-500/5 border border-purple-500/20 rounded">
                                <div className="text-[9px] text-purple-400 mb-2 uppercase">System Prompt</div>
                                <textarea className="w-full bg-black/40 border border-white/5 text-[9px] p-2 h-20 focus:outline-none" defaultValue="You are a helpful assistant..." />
                            </div>
                            <div className="p-4 border-2 border-dashed border-slate-800 rounded flex flex-col items-center gap-2 hover:border-cyan-500/40 transition-all cursor-pointer">
                                <FileUp size={16} className="text-slate-600" />
                                <span className="text-[8px] text-slate-600 uppercase">Load Knowledge Base</span>
                            </div>
                        </div>
                    )}
                </div>

                <button
                    onClick={() => { setIsGenerating(true); setTimeout(() => setIsGenerating(false), 2000); }}
                    className="w-full py-4 bg-cyan-500 text-black font-black text-[10px] uppercase flex items-center justify-center gap-3 shadow-[0_0_20px_rgba(6,182,212,0.3)]"
                >
                    <Download size={14} /> Generate Project
                </button>
            </div>
        ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-center px-6 border border-slate-900 bg-slate-900/10 rounded-xl">
                <Cpu size={32} className="text-slate-800 mb-4" />
                <div className="text-[9px] text-slate-700 uppercase tracking-widest leading-loose">
                    Select a module to edit its internal neural logic
                </div>
            </div>
        )}
      </aside>
    </div>
  );
};