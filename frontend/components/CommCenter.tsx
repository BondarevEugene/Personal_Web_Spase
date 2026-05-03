# ==============================================================================
# PROJECT: PERSONAL_WEB_SPACE
# LOCATION: /frontend/components/CommCenter.tsx
# VERSION: 1.0.0
# LAST MODIFIED: 2026-05-02
# DESCRIPTION: Панель управления коммуникациями и заказами.
# PURPOSE: Визуализация логов общения Агента и статусов сделок.
# DEPENDENCIES: lucide-react, framer-motion
# AUTHORS: Human & AI Collaboration
# STATUS: Draft
# ==============================================================================

import React from 'react';
import { MessageSquare, User, Clock, AlertCircle } from 'lucide-react';

const OrderCard = ({ log }: { log: any }) => (
  <div className="bg-slate-900/40 border-l-2 border-cyan-500 p-4 mb-3 hover:bg-slate-900/60 transition-all cursor-pointer group">
    <div className="flex justify-between items-start mb-2">
      <div className="flex items-center gap-2">
        <User size={14} className="text-cyan-600" />
        <span className="text-xs font-bold text-cyan-100 uppercase tracking-tighter">{log.client_name}</span>
      </div>
      <span className={`text-[9px] px-2 py-0.5 rounded ${log.status === 'New' ? 'bg-cyan-500 text-black' : 'border border-cyan-900 text-cyan-900'}`}>
        {log.status}
      </span>
    </div>
    <p className="text-[11px] text-slate-400 line-clamp-2 mb-3 leading-relaxed">
      {log.summary}
    </p>
    <div className="flex justify-between items-center text-[10px] text-slate-600">
      <div className="flex gap-3">
        <span className="flex items-center gap-1"><Clock size={10}/> {log.timestamp}</span>
        <span className="text-cyan-800"># {log.extracted_entities.item}</span>
         </div>
        <div className="mt-2 flex gap-2">
          {log.extracted_entities.format && (
            <span className="flex items-center gap-1 text-[9px] bg-purple-500/20 text-purple-400 px-2 py-0.5 rounded border border-purple-500/30">
              <Mail size={10} /> {log.extracted_entities.format}
            </span>
          )}
          <span className="text-[9px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded">
            ID: {log.id.slice(0,5)}
          </span>
        </div>
      <AlertCircle size={12} className={log.sentiment === 'Positive' ? 'text-green-500' : 'text-yellow-500'} />
    </div>
  </div>
);

export const CommCenter = () => {
  // В будущем данные потянутся из Firestore
  const mockLogs = [
    {
      id: "1",
      client_name: "Ivan Petrov",
      summary: "Интересуется дубовым столом 2х1м. Просил уточнить условия доставки в область.",
      timestamp: "14:20",
      sentiment: "Positive",
      extracted_entities: { item: "Oak Table" },
      status: "New"
    }
  ];

  return (
    <div className="h-full flex flex-col p-6 bg-black/40 backdrop-blur-md">
      <h2 className="text-sm font-black text-cyan-700 uppercase mb-6 flex items-center gap-2">
        <MessageSquare size={16}/> Neural Order Stream
      </h2>
      <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
        {mockLogs.map(log => <OrderCard key={log.id} log={log} />)}
      </div>
    </div>
  );
};
