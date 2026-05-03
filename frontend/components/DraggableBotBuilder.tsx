# ==============================================================================
# PROJECT: PERSONAL_WEB_SPACE
# LOCATION: /frontend/components/DraggableBotBuilder.tsx
# VERSION: 1.5.0
# LAST MODIFIED: 2026-05-02
# DESCRIPTION: Улучшенный конструктор с поддержкой Drag-and-Drop.
# PURPOSE: Обеспечение визуального взаимодействия пользователя с модулями бота.
# DEPENDENCIES: @dnd-kit/core, framer-motion, ALL_MODULES registry
# AUTHORS: Human & AI Collaboration
# STATUS: Development
# ==============================================================================

import React, { useState } from 'react';
import { DndContext, useDraggable, useDroppable } from '@dnd-kit/core';
import { ALL_MODULES } from '../config/bot_modules';
import { CodePreview } from './CodePreview';

// Компонент перетаскиваемого модуля
const DraggableModule = ({ module }: { module: any }) => {
  const { attributes, listeners, setNodeRef, transform } = useDraggable({
    id: module.id,
  });

  const style = transform ? {
    transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`,
  } : undefined;

  return (
    <div
      ref={setNodeRef} style={style} {...listeners} {...attributes}
      className="p-3 mb-2 bg-slate-900 border border-cyan-500/20 hover:border-cyan-500 cursor-grab active:cursor-grabbing flex items-center gap-3 transition-colors"
    >
      <module.icon size={14} className="text-cyan-500" />
      <span className="text-[10px] uppercase font-bold">{module.label}</span>
    </div>
  );
};

// Зона сброса (Телефон)
const PhoneDropZone = ({ activeModules }: { activeModules: any[] }) => {
  const { setNodeRef, isOver } = useDroppable({ id: 'phone-area' });

  return (
    <div
      ref={setNodeRef}
      className={`w-[300px] h-[600px] rounded-[3rem] border-8 transition-colors ${isOver ? 'border-cyan-500 bg-cyan-500/5' : 'border-slate-800 bg-slate-900'} relative flex flex-col overflow-hidden`}
    >
      <div className="h-12 bg-slate-800 flex items-center justify-center text-[10px] text-slate-500 font-bold uppercase">Telegram Bot Preview</div>
      <div className="flex-1 p-6 space-y-2">
        {activeModules.map(m => (
          <div key={m.id} className="p-2 bg-cyan-600/20 border border-cyan-500/40 text-cyan-400 text-center text-[9px] rounded uppercase">
            {m.label} Activated
          </div>
        ))}
      </div>
    </div>
  );
};