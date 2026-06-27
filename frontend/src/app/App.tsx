import React, { useState } from 'react';
// XYFlow импорты
import {
  ReactFlow, Background, Controls, MiniMap,
  addEdge, applyNodeChanges, applyEdgeChanges
} from '@xyflow/react';
import type { Node, Edge } from '@xyflow/react';

// Ваши компоненты (проверьте, что пути к ним верны относительно папки src/app/)
import { Sidebar } from '../components/Sidebar';
import { ArchitectDashboard } from '../components/ArchitectDashboard';
import { InsightPanel } from '../components/InsightPanel';
import { CommCenter } from '../components/CommCenter';
import { BotBuilder } from '../components/BotBuilder'; 

export const App = () => {
  const [activeTab, setActiveTab] = useState('architect');

  return (
    <div className="flex h-screen w-screen bg-black overflow-hidden font-mono text-cyan-500">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      <main className="flex-1 relative overflow-hidden">
        {activeTab === 'architect' && <ArchitectDashboard />}
        {activeTab === 'comms' && <CommCenter />}
        {activeTab === 'insights' && <InsightPanel />}
        {activeTab === 'builder' && <BotBuilder />}

        <div className="absolute bottom-4 right-6 flex items-center gap-2 text-[10px] text-cyan-500/50">
          SYSTEM_STATUS: ONLINE
        </div>
      </main>
    </div>
  );
};

export default App; // Добавили экспорт по умолчанию!