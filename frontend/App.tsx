# ==============================================================================
# PROJECT: PERSONAL_WEB_SPACE
# LOCATION: /frontend/components/BotBuilder.tsx
# VERSION: 1.4.0
# LAST MODIFIED: 2026-05-02
# DESCRIPTION: Ультра-конструктор с 50+ модулями и системой поиска.
# PURPOSE: Визуальное проектирование Telegram бота через расширенную библиотеку.
# DEPENDENCIES: framer-motion, lucide-react, react-dnd
# AUTHORS: Human & AI Collaboration
# STATUS: Development
# ==============================================================================

import React, { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { ArchitectDashboard } from './components/ArchitectDashboard';
import { InsightPanel } from './components/InsightPanel'; // Импорт панели аналитики
import { CommCenter } from './components/CommCenter';

export const BotBuilder = () => {
  const [searchTerm, setSearchTerm] = useState('');

  const filteredModules = ALL_MODULES.filter(m =>
    m.label.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="h-full flex bg-[#020617] text-slate-300 font-mono overflow-hidden">
      {/* ЛЕВАЯ ПАНЕЛЬ С ПОИСКОМ */}
      <div className="w-80 border-r border-cyan-500/10 flex flex-col bg-black/40">
        <div className="p-6 space-y-4">
          <input
            type="text"
            placeholder="SEARCH MODULES..."
            className="w-full bg-slate-900 border border-cyan-500/20 px-3 py-2 text-[10px] focus:outline-none focus:border-cyan-500 transition-all"
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        {/* Рендеринг отфильтрованного списка */}
        <div className="flex-1 overflow-y-auto p-4 space-y-1">
           {filteredModules.map(m => (
             <div key={m.id} className="group p-2 border border-transparent hover:border-cyan-500/30 hover:bg-cyan-500/5 cursor-pointer flex items-center gap-3 transition-all">
                <div className="text-cyan-800 group-hover:text-cyan-400 transition-colors">{m.icon}</div>
                <div className="text-[10px] uppercase">{m.label}</div>
             </div>
           ))}
        </div>
      </div>

export const App = () => {
  const [activeTab, setActiveTab] = useState('architect');

  return (
    <div className="flex h-screen w-screen bg-black overflow-hidden font-mono text-cyan-500">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      <main className="flex-1 relative overflow-hidden">
        {/* Условный рендеринг вкладок */}
        {activeTab === 'architect' && <ArchitectDashboard />}
        {activeTab === 'comms' && <CommCenter />}
        {activeTab === 'insights' && <InsightPanel />} {/* ТОЧКА ВХОДА В АНАЛИТИКУ */}

        <div className="absolute bottom-4 right-6 text-[10px] opacity-30 uppercase tracking-widest">
          Active_Node: {activeTab.toUpperCase()}
        </div>
      </main>
    </div>
  );
};

export const App = () => {
  const [activeTab, setActiveTab] = useState('architect');

  return (
    <div className="flex h-screen w-screen bg-black overflow-hidden font-mono">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      <main className="flex-1 relative">
        {activeTab === 'architect' && <ArchitectDashboard />}
        {activeTab === 'comms' && <CommCenter />}

        {/* Глобальный индикатор нейронной активности */}
        <div className="absolute bottom-4 right-6 flex items-center gap-2 text-[10px] text-cyan-900 pointer-events-none">
          <span className="w-2 h-2 bg-cyan-500 rounded-full animate-ping" />
          GENKIT_CORE_ACTIVE: LINK_ESTABLISHED
        </div>
      </main>
    </div>
  );
};