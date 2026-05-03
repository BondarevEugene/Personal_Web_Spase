# ==============================================================================
# PROJECT: PERSONAL_WEB_SPACE
# LOCATION: /frontend/components/CodePreview.tsx
# VERSION: 1.0.0
# LAST MODIFIED: 2026-05-02
# DESCRIPTION: Виджет предпросмотра генерируемого кода.
# PURPOSE: Визуализация процесса написания кода агентом в стиле "Matrix".
# DEPENDENCIES: framer-motion, prismjs
# AUTHORS: Human & AI Collaboration
# STATUS: Beta
# ==============================================================================

import React from 'react';
import { motion } from 'framer-motion';

export const CodePreview = ({ code }: { code: string }) => {
  return (
    <div className="bg-black/80 border border-cyan-500/30 rounded-lg p-4 font-mono text-[10px] h-full overflow-hidden relative">
      <div className="flex gap-1.5 mb-3 border-b border-white/5 pb-2">
        <div className="w-2 h-2 rounded-full bg-red-500/50" />
        <div className="w-2 h-2 rounded-full bg-yellow-500/50" />
        <div className="w-2 h-2 rounded-full bg-green-500/50" />
        <span className="ml-2 text-slate-500 uppercase tracking-widest text-[8px]">bot_core.py</span>
      </div>
      <motion.pre
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="text-cyan-400/80 leading-relaxed"
      >
        <code>{code || "# Инициализация системы...\n# Выберите модули слева"}</code>
      </motion.pre>
      <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent pointer-events-none" />
    </div>
  );
};