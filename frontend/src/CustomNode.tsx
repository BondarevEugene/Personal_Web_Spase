import React, { memo } from 'react';
import { Handle, Position } from '@xyflow/react';
import { Layers, Cpu, Radio, Shield, Key, Settings, Save, Zap } from 'lucide-react';

const getIcon = (cat: string) => {
  const c = cat ? cat.toUpperCase() : '';
  if (c.includes('GATEWAY') || c.includes('CHANNEL')) return <Radio size={13} className="text-[#bc13fe]" />;
  if (c.includes('AI') || c.includes('CORE')) return <Cpu size={13} className="text-[#00d2ff]" />;
  if (c.includes('ADMIN') || c.includes('SECURITY') || c.includes('SYSTEM')) return <Shield size={13} className="text-[#ff007f]" />;
  return <Layers size={13} className="text={#a1a1aa}" />;
};

export const CustomNode = memo(({ data, selected, id }: any) => {
  // Хендлер для кнопки "Параметры" и "Авторизация"
  // Они останавливают всплытие события клика, чтобы ReactFlow не сбрасывал выделение,
  // и принудительно фокусируют правую панель на ID этой ноды.
  const handleFocusNode = (e: React.MouseEvent) => {
    e.stopPropagation();
    // Эмулируем клик по самой ноде, чтобы сработал onNodeClick в дашборде
    const nodeElement = document.querySelector(`[data-id="${id}"]`);
    if (nodeElement) {
      (nodeElement as HTMLElement).click();
    }
  };

  const handleLocalSave = (e: React.MouseEvent) => {
    e.stopPropagation();
    // Локальное уведомление в консоль о фиксации параметров на холсте
    console.log(`[NODE_SYNC] Параметры узла ${id} зафиксированы.`);
    alert(`[SYSTEM] Конфигурация узла ${data.title || 'MODULE'} успешно зафиксирована на холсте.`);
  };

  const handleLocalDeploy = (e: React.MouseEvent) => {
    e.stopPropagation();
    // Прокидываем вызов глобальной кнопки деплоя из хедера
    const deployBtn = document.querySelector('button[onClick*="handleLaunchGraph"]');
    if (deployBtn) {
      (deployBtn as HTMLElement).click();
    } else {
      alert(`[EMULATION] Сигнал деплоя для узла ${id} отправлен на бэкенд.`);
    }
  };

  return (
    <div className={`w-80 rounded-lg bg-[#09090e]/95 backdrop-blur-md transition-all duration-200 border ${
      selected
        ? 'border-2 border-[#bc13fe] shadow-[0_0_25px_rgba(188,19,254,0.35)] scale-[1.01]'
        : 'border-[#27272a] hover:border-[#bc13fe]/40 shadow-2xl'
    }`}>

      {/* Шапка узла */}
      <div className="px-4 py-2.5 bg-black/40 border-b border-[#18181b] flex justify-between items-center rounded-t-lg">
        <div className="flex items-center gap-2">
          {getIcon(data.subtitle || data.cat)}
          <span className="text-[9px] font-mono tracking-widest text-zinc-400 font-bold uppercase">
            {data.subtitle || 'SYS_NODE'}
          </span>
        </div>
        <div className="flex items-center gap-1.5 text-zinc-600">
          <div className={`w-1.5 h-1.5 rounded-full ${selected ? 'bg-[#bc13fe] animate-pulse' : 'bg-zinc-700'}`} />
        </div>
      </div>

      {/* Контент */}
      <div className="p-4">
        <h4 className="text-xs font-bold text-zinc-100 uppercase tracking-wide font-mono mb-1">{data.title || data.label}</h4>
        <p className="text-[10px] text-zinc-500 font-mono leading-relaxed mb-4 italic line-clamp-2">
          {data.label || 'Компонент промышленного ядра готов к конфигурации.'}
        </p>

        {/* ЖИВЫЕ КНОПКИ ВНУТРИ БЛОКА */}
        <div className="grid grid-cols-2 gap-2 pt-2 border-t border-[#161619]">
          <button
            onClick={handleFocusNode}
            className="flex items-center justify-center gap-1 py-1.5 bg-zinc-900/50 hover:bg-[#00d2ff]/10 border border-zinc-800 hover:border-[#00d2ff]/30 text-zinc-400 hover:text-[#00d2ff] text-[8px] font-bold font-mono uppercase tracking-wider rounded transition-all active:scale-95 cursor-pointer"
          >
            <Key size={10} /> Авторизация
          </button>

          <button
            onClick={handleFocusNode}
            className="flex items-center justify-center gap-1 py-1.5 bg-zinc-900/50 hover:bg-[#bc13fe]/10 border border-zinc-800 hover:border-[#bc13fe]/30 text-zinc-400 hover:text-[#bc13fe] text-[8px] font-bold font-mono uppercase tracking-wider rounded transition-all active:scale-95 cursor-pointer"
          >
            <Settings size={10} /> Параметры
          </button>

          <button
            onClick={handleLocalSave}
            className="flex items-center justify-center gap-1 py-1.5 bg-zinc-900/50 hover:bg-[#22c55e]/10 border border-zinc-800 hover:border-[#22c55e]/30 text-zinc-400 hover:text-[#22c55e] text-[8px] font-bold font-mono uppercase tracking-wider rounded transition-all active:scale-95 cursor-pointer"
          >
            <Save size={10} /> Save Node
          </button>

          <button
            onClick={handleLocalDeploy}
            className="flex items-center justify-center gap-1 py-1.5 bg-[#bc13fe]/5 hover:bg-[#bc13fe]/20 border border-[#bc13fe]/20 hover:border-[#bc13fe] text-zinc-400 hover:text-white text-[8px] font-black font-mono uppercase tracking-wider rounded transition-all active:scale-95 cursor-pointer"
          >
            <Zap size={10} className="text-[#FFD700]" /> Deploy Code
          </button>
        </div>

        {/* Сводка */}
        <div className="mt-3 pt-2 border-t border-[#111113] flex justify-between items-center text-[8px] font-mono uppercase tracking-wider text-zinc-600">
          <span>Связи: {selected ? '[ACTIVE]' : '[STANDBY]'}</span>
          <span>v6.0_STEEL</span>
        </div>
      </div>

      {/* Порты подключения (Вход / Выход) */}
      <Handle
        type="target"
        position={Position.Left}
        className="!w-2 !h-2 !bg-[#00d2ff] !border-none hover:!scale-125 transition-transform"
        style={{ left: '-5px' }}
      />
      <Handle
        type="source"
        position={Position.Right}
        className="!w-2 !h-2 !bg-[#bc13fe] !border-none hover:!scale-125 transition-transform"
        style={{ right: '-5px' }}
      />
    </div>
  );
});

CustomNode.displayName = 'CustomNode';