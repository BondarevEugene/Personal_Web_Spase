# ==============================================================================
# PROJECT: PERSONAL_WEB_SPACE
# LOCATION: /frontend/components/ArchitectDashboard.tsx
# VERSION: 1.2.0
# LAST MODIFIED: 2026-05-02
# DESCRIPTION: Высокотехнологичный UI Dashboard.
# PURPOSE: Управление агентом, визуализация графа проекта и live-кодинг.
# DEPENDENCIES: tailwindcss, framer-motion, react-flow-renderer, lucide-react
# AUTHORS: Human & AI Collaboration
# STATUS: Development
# ==============================================================================

import React, { useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import ReactFlow, { Background, Controls, Edge, Node } from 'reactflow';
import 'reactflow/dist/style.css';
import { Terminal, Shield, Zap, Box, Activity } from 'lucide-react';

export const ArchitectDashboard = () => {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [loading, setLoading] = useState(false);

  const triggerCoreFlow = async (idea: string) => {
    setLoading(true);
    try {
      const response = await fetch('/api/plan-project', {
        method: 'POST',
        body: JSON.stringify({ idea }),
        headers: { 'Content-Type': 'application/json' }
      });
      const data = await response.json();

      // Маппим данные в узлы графа
      setNodes(data.nodes.map((n: any, i: number) => ({
        id: n.id,
        data: { label: n.label },
        position: { x: 100 + (i * 150), y: 100 + (i * 50) },
        style: { background: '#083344', color: '#22d3ee', border: '1px solid #06b6d4' }
      })));
      setEdges(data.edges);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-screen w-screen bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-slate-900 via-black to-black text-cyan-500 flex flex-col overflow-hidden">

      {/* TOP NAV: Сканнер состояния */}
      <div className="h-16 border-b border-cyan-500/20 flex items-center px-6 justify-between bg-black/50 backdrop-blur-xl">
        <div className="flex items-center gap-4">
          <div className="relative">
             <div className="absolute inset-0 bg-cyan-500 blur-sm opacity-20 animate-pulse"></div>
             <Zap className="relative text-cyan-400" />
          </div>
          <span className="font-bold tracking-[0.3em] text-sm uppercase">Neural Architect Node</span>
        </div>
        <div className="flex gap-8 text-[10px] uppercase tracking-widest text-cyan-800">
          <div className="flex items-center gap-2"><Activity size={12}/> CPU: 12%</div>
          <div className="flex items-center gap-2 text-green-500"><Shield size={12}/> Firewall: Active</div>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">

        {/* LEFT: INPUT & LOGS */}
        <aside className="w-96 border-r border-cyan-500/10 flex flex-col bg-black/20">
          <div className="p-6 space-y-4">
            <h2 className="text-xs font-black text-cyan-700 uppercase">Input Stream</h2>
            <textarea
               className="w-full h-40 bg-slate-950 border border-cyan-500/30 rounded-none p-4 text-xs focus:ring-1 focus:ring-cyan-500 outline-none resize-none transition-all hover:border-cyan-500/60"
               placeholder="Enter concept parameters..."
            />
            <button
              onClick={() => triggerCoreFlow("Test Idea")}
              className="w-full py-3 border border-cyan-500/50 hover:bg-cyan-500 hover:text-black transition-all font-mono text-xs uppercase"
            >
              {loading ? "Decrypting..." : "Initialize Synthesis"}
            </button>
          </div>

          <div className="flex-1 p-6 border-t border-cyan-500/10 font-[JetBrains Mono] text-[10px]">
            <div className="flex items-center gap-2 mb-4 text-cyan-700"><Terminal size={12}/> Kernel Output</div>
            <div className="space-y-2 opacity-60">
                <p>{`[2026-05-02 18:00] > System: Ready`}</p>
                <p className="text-cyan-400">{`[2026-05-02 18:01] > Plugin: Genkit Python Loaded`}</p>
            </div>
          </div>
        </aside>

        {/* MAIN: VISUALIZER */}
        <main className="flex-1 relative">
           {/* Фон с сеткой */}
           <div className="absolute inset-0 pointer-events-none opacity-10"
                style={{backgroundImage: 'radial-gradient(#22d3ee 0.5px, transparent 0.5px)', backgroundSize: '24px 24px'}}>
           </div>

           <div className="h-full w-full">
              <ReactFlow nodes={nodes} edges={edges}>
                <Background color="#0ea5e9" gap={20} />
                <Controls />
              </ReactFlow>
           </div>

           {/* Floating Info Box */}
           <motion.div
             initial={{ x: 300 }} animate={{ x: 0 }}
             className="absolute top-6 right-6 w-80 bg-slate-950/80 border border-cyan-500/30 backdrop-blur-md p-5"
           >
              <div className="flex items-center gap-2 mb-4 border-b border-cyan-500/20 pb-2">
                <Box size={16} /> <span className="text-xs font-bold uppercase">Component Data</span>
              </div>
              <div className="text-[11px] space-y-3">
                 <div className="flex justify-between"><span>Status:</span> <span className="text-green-500">Verified</span></div>
                 <div className="flex justify-between"><span>Stack:</span> <span className="text-white">Python, FastAPI</span></div>
                 <p className="text-slate-500 pt-2 border-t border-cyan-500/10 italic">Select node to view documentation...</p>
              </div>
           </motion.div>
        </main>
      </div>
    </div>
  );
};
