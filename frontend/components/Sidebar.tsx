# ==============================================================================
# PROJECT: PERSONAL_WEB_SPACE
# LOCATION: /frontend/components/Sidebar.tsx
# VERSION: 1.0.0
# LAST MODIFIED: 2026-05-02
# DESCRIPTION: Боковая панель навигации.
# PURPOSE: Переключение между модулями Архитектора, Коммуникаций и Настроек.
# DEPENDENCIES: lucide-react, framer-motion
# AUTHORS: Human & AI Collaboration
# STATUS: Beta
# ==============================================================================

import React from 'react';
import { LayoutDashboard, MessageSquare, Settings, Database, Layers } from 'lucide-react';

export const Sidebar = ({ activeTab, setActiveTab }: { activeTab: string, setActiveTab: (t: string) => void }) => {
  const menuItems = [
    { id: 'architect', icon: <Layers size={20} />, label: 'Architect' },
    { id: 'comms', icon: <MessageSquare size={20} />, label: 'Comm Center' },
    { id: 'database', icon: <Database size={20} />, label: 'Inventory' },
    { id: 'settings', icon: <Settings size={20} />, label: 'System' },
  ];

  return (
    <aside className="w-20 hover:w-64 transition-all duration-300 bg-black border-r border-cyan-500/20 flex flex-col items-center py-8 z-50 group">
      <div className="mb-12">
        <div className="w-10 h-10 bg-cyan-500 rounded-sm flex items-center justify-center shadow-[0_0_15px_rgba(6,182,212,0.5)]">
          <LayoutDashboard className="text-black" />
        </div>
      </div>

      <nav className="flex-1 w-full space-y-4 px-4">
        {menuItems.map((item) => (
          <button
            key={item.id}
            onClick={() => setActiveTab(item.id)}
            className={`w-full flex items-center gap-4 p-3 rounded-none transition-all ${
              activeTab === item.id
              ? 'bg-cyan-500/10 text-cyan-400 border-r-2 border-cyan-500'
              : 'text-slate-500 hover:text-cyan-200'
            }`}
          >
            {item.icon}
            <span className="opacity-0 group-hover:opacity-100 transition-opacity text-xs uppercase font-bold tracking-widest">
              {item.label}
            </span>
          </button>
        ))}
      </nav>
    </aside>
  );
};