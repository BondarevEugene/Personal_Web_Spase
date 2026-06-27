import React, { useState } from 'react';
import { BotBuilder } from '@/features/bot-builder';
// XYFlow импорты
import {ReactFlow, Background, Controls, MiniMap, addEdge, applyNodeChanges, applyEdgeChanges} from '@xyflow/react';
import type { Node, Edge } from '@xyflow/react';
import { CustomNode } from './CustomNode'; // импорт нашего дизайна

// Ваши компоненты
import { Sidebar } from './components/Sidebar';
import { ArchitectDashboard } from './components/ArchitectDashboard';
import { InsightPanel } from './components/InsightPanel';
import { CommCenter } from './components/CommCenter';
import { BotBuilder } from './components/BotBuilder'; // Убедитесь, что он перенесен в components

const ALL_MODULES = [
  { id: '1', label: 'Trigger', icon: '⚡' },
  { id: '2', label: 'Action', icon: '⚙️' }
];

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

        <div className="absolute bottom-4 right-6 flex items-center gap-2 text-[10px] text-cyan-900 pointer-events-none">
          <span className="w-2 h-2 bg-cyan-500 rounded-full animate-ping" />
          GENKIT_CORE_ACTIVE: LINK_ESTABLISHED
        </div>
      </main>
    </div>
  );
};

const nodeTypes = { customNode: CustomNode };

const MyBuilder = () => {
  return (
    <div style={{ width: '100vw', height: '100vh' }}>
      <ReactFlow
        nodes={getNodesRegistry()}
        nodeTypes={nodeTypes}
        fitView
      >
        <Background />
        <Controls />
      </ReactFlow>
    </div>
  );
};

export default App;