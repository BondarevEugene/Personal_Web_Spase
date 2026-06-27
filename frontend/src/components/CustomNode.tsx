import React, { memo } from 'react';
import { Handle, Position } from '@xyflow/react';
import { Layers, Cpu, Radio, Shield, Settings } from 'lucide-react';

const getIcon = (cat: string) => {
  const c = cat ? cat.toUpperCase() : '';
  if (c.includes('CHANNEL')) return <Radio size={14} className="text-[#bc13fe]" />;
  if (c.includes('CORE')) return <Cpu size={14} className="text-[#00d2ff]" />;
  if (c.includes('ADMIN') || c.includes('SECURITY')) return <Shield size={14} className="text-[#ff007f]" />;
  return <Layers size={14} className="text-[#a1a1aa]" />;
};

export const CustomNode = memo(({ data, selected }: any) => {
  const fieldsCount = data.config_fields ? Object.keys(data.config_fields).length : 0;

  return (
    <div className={`w-72 rounded-md bg-[#09090e]/95 backdrop-blur-md transition-all duration-200 ${
      selected
        ? 'border-2 border-[#bc13fe] shadow-[0_0_25px_rgba(188,19,254,0.4)] scale-[1.01]'
        : 'border border-[#27272a] hover:border-[#bc13fe]/40 shadow-xl'
    }`}>

      {/* Шапка модуля */}
      <div className="px-3 py-2 bg-black/40 border-b border-[#27272a] flex items-center justify-between rounded-t-md">
        <div className="flex items-center gap-2">
          <span className={`w-1.5 h-1.5 rounded-full ${selected ? 'bg-[#bc13fe] animate-pulse' : 'bg-[#22c55e]'}`} />
          <span className="text-[9px] font-mono uppercase tracking-[0.15em] text-zinc-400 font-bold">
            {data.cat || 'SYSTEM_NODE'}
          </span>
        </div>
        <div className="flex items-center gap-1.5 text-zinc-600">
          {getIcon(data.cat)}
        </div>
      </div>

      {/* Контент */}
      <div className="p-4">
        <h4 className="text-xs font-bold text-zinc-200 uppercase tracking-wide font-mono mb-1">{data.label}</h4>
        <p className="text-[10px] text-zinc-500 font-mono leading-relaxed line-clamp-2 italic">
          {data.desc || 'Нет описания конфигурации.'}
        </p>

        {/* Сводка конфигурации */}
        <div className="mt-3 pt-2 border-t border-[#18181b] flex justify-between items-center text-[8px] font-mono uppercase tracking-wider">
          <span className="text-zinc-600">Параметры: {fieldsCount}</span>
          <span className={selected ? 'text-[#bc13fe]' : 'text-zinc-600'}>
            {selected ? '[АКТИВЕН]' : '[ОЖИДАНИЕ]'}
          </span>
        </div>
      </div>

      {/* Промышленные порты подключения */}
      <Handle
        type="target"
        position={Position.Left}
        className="!w-2.5 !h-2.5 !bg-[#030305] !border !border-[#27272a] hover:!border-[#bc13fe] !rounded-none -ml-1.5 transition-colors"
      />
      <Handle
        type="source"
        position={Position.Right}
        className="!w-2.5 !h-2.5 !bg-[#030305] !border !border-[#bc13fe] hover:!bg-[#bc13fe] !rounded-none -mr-1.5 transition-colors"
      />
    </div>
  );
});