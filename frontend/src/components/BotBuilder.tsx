# ==============================================================================
# PROJECT: PERSONAL_WEB_SPACE
# LOCATION: /frontend/components/BotBuilder.tsx
# VERSION: 4.5.0 (INTEGRATED_CORE)
# LAST MODIFIED: 2026-05-02
# DESCRIPTION: Полнофункциональный инженерный интерфейс сборки ботов.  Full-scale engineering console with Live Backend Sync.
# PURPOSE: Глубокая настройка модулей, управление стейтами и визуализация логики.
# DEPENDENCIES: framer-motion, lucide-react, @tanstack/react-query
# AUTHORS: Human & AI Collaboration
# STATUS: Production-Ready
# ==============================================================================


import React, { useState, useMemo, useEffect } from 'react';
import { motion, AnimatePresence, Reorder } from 'framer-motion';
import {
  Search, Cpu, ChevronRight, Smartphone,
  Download, Zap, Info, FileUp, X, History,
  Activity, Layers, Fingerprint, ShoppingCart, Code, Network
} from 'lucide-react';
import { ALL_MODULES } from '../config/bot_modules';

// Категории (System Registry)
const CATEGORIES = [
  { id: 'all', label: 'SYSTEM_ALL' },
  { id: 'core', label: 'CORE_KERNEL' },
  { id: 'ai', label: 'NEURAL_LINK' },
  { id: 'shop', label: 'TRANS_MATRIX' },
  { id: 'marketing', label: 'SIGNAL_ADS' },
  { id: 'logic', label: 'LOGIC_GATE' },
];

interface BuildRecord {
  id: string;
  timestamp: string;
  author: string;
  modules: string[];
  status: 'SUCCESS' | 'FAILED';
}

export const BotBuilder = () => {
  // --- STATES ---
  const [searchTerm, setSearchTerm] = useState('');
  const [activeCat, setActiveCat] = useState('all');
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [buildProgress, setBuildProgress] = useState(0);
  const [buildLogs, setBuildLogs] = useState<string[]>([]);
  const [buildHistory, setBuildHistory] = useState<BuildRecord[]>([]);
  const [activeModuleId, setActiveModuleId] = useState<string | null>(null);

  // --- LOGIC: FILTERING ---
  const filteredModules = useMemo(() => {
    return ALL_MODULES.filter(m => {
      const matchSearch = m.label.toLowerCase().includes(searchTerm.toLowerCase());
      const matchCat = activeCat === 'all' || m.cat === activeCat;
      return matchSearch && matchCat;
    });
  }, [searchTerm, activeCat]);

  const activeModuleData = useMemo(() =>
    ALL_MODULES.find(m => m.id === activeModuleId),
  [activeModuleId]);

  const toggleModule = (id: string) => {
    setSelectedIds(prev =>
      prev.includes(id) ? prev.filter(mid => mid !== id) : [...prev, id]
    );
    setActiveModuleId(id);
  };

  // --- REAL BACKEND EXECUTION (СВЯЗЬ С MAIN.PY) ---
  const handleDeploy = async () => {
    if (selectedIds.length === 0) return;

    setIsGenerating(true);
    setBuildProgress(10);
    setBuildLogs(["[SYSTEM] INITIALIZING_BUILD_SEQUENCE..."]);

    try {
      // Шаг 1: Локальный анализ (UX)
      await new Promise(r => setTimeout(r, 600));
      setBuildLogs(prev => [...prev, "[DNA] ANALYZING_MODULE_STABILITY..."]);
      setBuildProgress(30);

      // Шаг 2: Реальный запрос к твоему FastAPI (main.py)
      const response = await fetch('http://127.0.0.1:8080/api/builder/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          modules: selectedIds,
          author: 'Bondarev_E'
        })
      });

      if (!response.ok) throw new Error("BACKEND_OFFLINE");

      const result = await response.json();

      setBuildLogs(prev => [...prev, `[SERVER] CORE_RESPONDED: ${result.build_id}`]);
      setBuildProgress(70);

      // Шаг 3: Финализация
      await new Promise(r => setTimeout(r, 800));
      setBuildProgress(100);
      setBuildLogs(prev => [...prev, "[SUCCESS] PROJECT_MANIFEST_READY_FOR_DOWNLOAD"]);

      // Запись в историю (локально + уже ушло в Firestore через main.py)
      const newRecord: BuildRecord = {
        id: result.build_id,
        timestamp: new Date().toLocaleTimeString(),
        author: 'Bondarev_E',
        modules: [...selectedIds],
        status: 'SUCCESS'
      };
      setBuildHistory(prev => [newRecord, ...prev]);

    } catch (e) {
      setBuildLogs(prev => [...prev, "[CRITICAL_ERROR] CONNECTION_TO_CORE_FAILED"]);
      setBuildProgress(0);
    } finally {
      setTimeout(() => {
        setIsGenerating(false);
        // Не очищаем логи сразу, чтобы пользователь успел прочитать
      }, 2000);
    }
  };

  return (
    <div className="h-full flex bg-[#020617] text-slate-300 font-mono overflow-hidden selection:bg-cyan-500 selection:text-black">

      {/* --- LEFT PANEL: REGISTRY --- */}
      <aside className="w-80 border-r border-cyan-500/10 flex flex-col bg-black/40 backdrop-blur-md z-20">
        <div className="p-6 space-y-6">
          <div className="flex items-center justify-between border-b border-white/5 pb-4">
            <h2 className="text-[10px] font-black uppercase tracking-[0.3em] text-cyan-500 flex items-center gap-2">
              <Layers size={14}/> Registry
            </h2>
            <span className="text-[9px] text-slate-600 font-bold">{selectedIds.length} ACTIVE_NODES</span>
          </div>

          {/* Search */}
          <div className="relative group">
            <Search className="absolute left-3 top-2.5 text-slate-600 group-focus-within:text-cyan-500" size={14} />
            <input
              type="text" placeholder="EXECUTE_SEARCH..."
              className="w-full bg-slate-900/50 border border-cyan-500/10 px-9 py-3 text-[10px] focus:outline-none focus:border-cyan-500 transition-all rounded-lg"
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>

          {/* Categories */}
          <div className="grid grid-cols-2 gap-1">
            {CATEGORIES.map(cat => (
              <button
                key={cat.id} onClick={() => setActiveCat(cat.id)}
                className={`text-[8px] p-2 uppercase font-black border transition-all ${
                  activeCat === cat.id ? 'bg-cyan-500 border-cyan-500 text-black' : 'bg-transparent border-white/5 text-slate-500 hover:border-white/20'
                }`}
              >
                {cat.label}
              </button>
            ))}
          </div>
        </div>

        {/* Module List */}
        <div className="flex-1 overflow-y-auto px-4 pb-4 space-y-2 custom-scrollbar">
          {filteredModules.map(m => (
            <motion.div
              key={m.id} layout onClick={() => toggleModule(m.id)}
              className={`group p-4 border rounded-xl flex items-center justify-between cursor-pointer transition-all ${
                selectedIds.includes(m.id)
                ? 'border-cyan-500 bg-cyan-500/10 shadow-[0_0_15px_rgba(6,182,212,0.1)]'
                : 'border-white/5 bg-white/[0.02] hover:bg-white/[0.05]'
              }`}
            >
              <div className="flex items-center gap-4">
                <div className={`p-2 rounded-lg ${selectedIds.includes(m.id) ? 'bg-cyan-500 text-black' : 'bg-slate-800 text-slate-600'}`}>
                    <m.icon size={16} />
                </div>
                <div>
                  <div className={`text-[11px] font-black uppercase tracking-tight ${selectedIds.includes(m.id) ? 'text-white' : 'text-slate-400'}`}>
                    {m.label}
                  </div>
                  <div className="text-[7px] text-slate-600 uppercase font-bold">{m.id} // v1.0</div>
                </div>
              </div>
              {selectedIds.includes(m.id) && <Zap size={12} className="text-cyan-500 animate-pulse" />}
            </motion.div>
          ))}
        </div>

        {/* Mini History Log */}
        <div className="p-6 border-t border-white/5 bg-black/60">
             <div className="text-[9px] font-black text-slate-500 uppercase tracking-widest flex items-center gap-2 mb-4">
                <History size={12}/> Build_Session_Logs
             </div>
             <div className="space-y-3">
                {buildHistory.length === 0 && <div className="text-[8px] text-slate-700 italic">No active builds in current session...</div>}
                {buildHistory.slice(0, 2).map(h => (
                    <div key={h.id} className="p-2 border border-white/5 rounded bg-white/[0.02]">
                        <div className="text-[9px] text-cyan-500 font-black">{h.id}</div>
                        <div className="text-[7px] text-slate-600 uppercase">{h.timestamp} // SUCCESS</div>
                    </div>
                ))}
             </div>
        </div>
      </aside>

      {/* --- CENTER: NEURAL DNA PREVIEW --- */}
      <main className="flex-1 flex flex-col items-center justify-center relative p-10 z-10">

        {/* Background Visualizer */}
        <div className="absolute inset-0 flex items-center justify-center opacity-[0.03] pointer-events-none">
            <Fingerprint size={600} className="text-cyan-500" />
        </div>

        {/* Smartphone Shell */}
        <div className="relative z-10 w-[340px] h-[680px] bg-black rounded-[4rem] border-[14px] border-[#161b22] shadow-[0_0_100px_rgba(0,0,0,0.8)] flex flex-col overflow-hidden ring-1 ring-white/10">

          {/* Header */}
          <div className="h-20 bg-[#161b22] flex items-center px-10 border-b border-white/5">
             <div className="w-10 h-10 bg-gradient-to-tr from-cyan-500 to-blue-600 rounded-2xl rotate-3 shadow-lg shadow-cyan-500/20" />
             <div className="ml-4 flex-1">
                <div className="text-[14px] font-black text-white uppercase tracking-tighter">Neural DNA</div>
                <div className="text-[8px] text-cyan-500 uppercase font-black tracking-widest">Logic_Flow: Active</div>
             </div>
             <Activity size={18} className="text-cyan-500 animate-pulse" />
          </div>

          {/* Content Area with REORDER LOGIC */}
          <div className="flex-1 p-6 space-y-4 overflow-y-auto bg-slate-950/40 custom-scrollbar">
             <div className="bg-slate-900/80 p-4 rounded-3xl rounded-bl-none text-[10px] text-slate-300 leading-relaxed border border-white/5 italic">
               System initialized. Awaiting module DNA sequence for project synthesis.
             </div>

             <Reorder.Group axis="y" values={selectedIds} onReorder={setSelectedIds} className="space-y-3">
               {selectedIds.map(id => {
                 const m = ALL_MODULES.find(mod => mod.id === id);
                 return (
                   <Reorder.Item
                    key={id} value={id}
                    className="p-4 bg-black/60 border border-cyan-500/30 rounded-2xl cursor-grab active:cursor-grabbing flex items-center gap-4 group"
                   >
                    <div className="p-2 bg-cyan-500/10 rounded-lg text-cyan-500">
                      {m?.cat === 'ai' ? <Network size={16} /> : m?.cat === 'shop' ? <ShoppingCart size={16} /> : <Code size={16} />}
                    </div>
                    <div className="flex-1">
                      <div className="text-[11px] font-black text-white uppercase italic">{m?.label}</div>
                      <div className="text-[7px] text-slate-500 font-bold uppercase tracking-widest">Component_Ready</div>
                    </div>
                    <div className="opacity-0 group-hover:opacity-100 transition-opacity"><ChevronRight size={14} className="text-slate-700"/></div>
                   </Reorder.Item>
                 )
               })}
             </Reorder.Group>

             {selectedIds.length === 0 && (
                <div className="h-full flex flex-col items-center justify-center opacity-10">
                    <Cpu size={80} className="mb-4" />
                    <div className="text-[10px] font-black uppercase tracking-[0.3em]">No_Data_Input</div>
                </div>
             )}
          </div>

          {/* Fake Input */}
          <div className="h-20 border-t border-white/5 p-4 bg-black/40">
             <div className="w-full h-full bg-slate-900 rounded-2xl px-5 flex items-center justify-between border border-white/5">
                <span className="text-[10px] text-slate-600 font-black uppercase tracking-[0.2em]">Matrix command...</span>
                <div className="p-1.5 bg-cyan-500 rounded-lg text-black"><ChevronRight size={16} /></div>
             </div>
          </div>
        </div>

        {/* Build Panel (Best Practice UX) */}
        <div className="mt-10 w-[340px] space-y-4">
          <AnimatePresence>
            {isGenerating && (
                <motion.div
                    initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }}
                    className="overflow-hidden bg-slate-900/80 border border-cyan-500/20 rounded-3xl p-5"
                >
                    <div className="flex justify-between items-end mb-2">
                        <span className="text-[10px] font-black text-cyan-500 uppercase">Process_Status</span>
                        <span className="text-[14px] font-black text-white">{buildProgress}%</span>
                    </div>
                    <div className="h-1.5 bg-black rounded-full overflow-hidden mb-4 border border-white/5">
                        <motion.div animate={{ width: `${buildProgress}%` }} className="h-full bg-cyan-500 shadow-[0_0_15px_#06b6d4]" />
                    </div>
                    <div className="h-20 overflow-y-auto custom-scrollbar text-[8px] font-mono text-slate-500 space-y-1">
                        {buildLogs.map((log, i) => (
                            <div key={i} className="flex gap-2">
                                <span className="text-cyan-800">[{new Date().toLocaleTimeString()}]</span>
                                <span>{log}</span>
                            </div>
                        ))}
                    </div>
                </motion.div>
            )}
          </AnimatePresence>

          <motion.button
            whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
            onClick={handleDeploy}
            disabled={isGenerating || selectedIds.length === 0}
            className={`w-full py-6 font-black uppercase text-xs tracking-[0.3em] flex items-center justify-center gap-4 transition-all rounded-[2rem] border-2 ${
                isGenerating
                ? 'bg-slate-900 border-slate-800 text-slate-600'
                : 'bg-cyan-500 border-cyan-400 text-black shadow-[0_20px_50px_rgba(6,182,212,0.2)]'
            }`}
          >
            {isGenerating ? <Activity className="animate-spin" size={18} /> : <Download size={18} />}
            {isGenerating ? 'Compiling_Assets...' : 'Execute_Build'}
          </motion.button>
        </div>
      </main>

      {/* --- RIGHT PANEL: INSPECTOR --- */}
      <aside className="w-96 border-l border-cyan-500/10 bg-black/40 p-8 flex flex-col gap-8 z-20">
        <div className="flex items-center gap-4 border-b border-white/5 pb-6">
            <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-2xl text-amber-500">
                <Info size={24} />
            </div>
            <h2 className="text-[14px] font-black uppercase tracking-[0.3em] text-white">Inspector</h2>
        </div>

        {activeModuleData ? (
          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="space-y-8 flex-1 overflow-y-auto custom-scrollbar pr-2">
             <div className="p-6 bg-gradient-to-br from-cyan-500/10 to-transparent border border-cyan-500/20 rounded-[2.5rem]">
                <div className="text-[10px] text-cyan-500 font-black uppercase mb-2">Module_Focused</div>
                <div className="text-2xl text-white font-black uppercase italic leading-tight">{activeModuleData.label}</div>
                <div className="mt-4 text-[11px] text-slate-400 leading-relaxed font-bold border-t border-white/5 pt-4">
                   {activeModuleData.desc || "No extended documentation found for this node."}
                </div>
             </div>

             {activeModuleId === 'rag' && (
                <div className="space-y-4">
                    <label className="text-[10px] text-slate-500 font-black uppercase ml-2 tracking-widest">Knowledge_Base_Upload</label>
                    <div className="border-2 border-dashed border-white/10 rounded-3xl p-8 flex flex-col items-center justify-center gap-4 hover:border-cyan-500/40 transition-all cursor-pointer bg-white/[0.01] group">
                        <FileUp size={32} className="text-slate-700 group-hover:text-cyan-500 transition-colors" />
                        <span className="text-[9px] text-slate-600 text-center uppercase font-black">Drop PDF/DOCX to train AI agent</span>
                    </div>
                </div>
             )}

             <div className="p-6 bg-slate-900/40 rounded-3xl border border-white/5">
                <div className="text-[10px] text-slate-500 font-black uppercase mb-4 tracking-widest">Logic_Gate_Settings</div>
                <div className="space-y-4">
                    <div className="flex justify-between items-center">
                        <span className="text-[10px] font-bold text-slate-400">AUTO_RESPOND</span>
                        <div className="w-10 h-5 bg-cyan-500 rounded-full relative"><div className="absolute right-1 top-1 w-3 h-3 bg-white rounded-full"/></div>
                    </div>
                    <div className="flex justify-between items-center">
                        <span className="text-[10px] font-bold text-slate-400">DATA_LOGGING</span>
                        <div className="w-10 h-5 bg-slate-800 rounded-full relative"><div className="absolute left-1 top-1 w-3 h-3 bg-slate-600 rounded-full"/></div>
                    </div>
                </div>
             </div>
          </motion.div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-center opacity-20 grayscale">
             <Cpu size={60} className="mb-6 animate-pulse" />
             <div className="text-[10px] text-slate-500 uppercase font-black tracking-[0.4em]">Awaiting_Input_Data</div>
          </div>
        )}

        <div className="text-[8px] text-slate-600 leading-relaxed font-bold border-t border-white/5 pt-6 uppercase italic">
            * Warning: Building a project will consume 1 API Credit. Ensure all module DNA sequences are correct before execution.
        </div>
      </aside>
    </div>
  );
};