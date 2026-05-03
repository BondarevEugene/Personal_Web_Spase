# ==============================================================================
# PROJECT: PERSONAL_WEB_SPACE
# LOCATION: /frontend/components/DeploySection.tsx
# VERSION: 1.0.0
# LAST MODIFIED: 2026-05-02
# DESCRIPTION: Компонент финализации и скачивания проекта.
# PURPOSE: Обеспечение UX-процесса "сборка -> деплой".
# DEPENDENCIES: framer-motion, lucide-react
# AUTHORS: Human & AI Collaboration
# STATUS: Beta
# ==============================================================================

import { Download, CheckCircle, Loader2 } from 'lucide-react';

export const DeploySection = ({ isGenerating }: { isGenerating: boolean }) => {
  return (
    <div className="absolute bottom-10 left-1/2 -translate-x-1/2 w-full max-w-md bg-slate-900 border border-cyan-500/30 p-6 shadow-2xl backdrop-blur-xl">
      <div className="flex items-center justify-between">
        <div>
          <h4 className="text-xs font-bold text-white uppercase tracking-widest">Production Ready</h4>
          <p className="text-[9px] text-slate-500 uppercase mt-1">Docker & Python config generated</p>
        </div>
        <button className="flex items-center gap-2 px-6 py-3 bg-cyan-500 text-black font-black text-[10px] uppercase hover:bg-white transition-colors">
          {isGenerating ? <Loader2 className="animate-spin" /> : <Download size={14} />}
          Download ZIP
        </button>
      </div>

      {/* Прогресс-бар "компиляции" */}
      {isGenerating && (
        <div className="mt-4 h-1 bg-slate-800 w-full overflow-hidden">
          <div className="h-full bg-cyan-500 animate-[loading_2s_ease-in-out_infinite]" style={{width: '30%'}}></div>
        </div>
      )}
    </div>
  );
};