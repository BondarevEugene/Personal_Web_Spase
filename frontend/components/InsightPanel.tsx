# ==============================================================================
# PROJECT: PERSONAL_WEB_SPACE
# LOCATION: /frontend/components/InsightPanel.tsx
# VERSION: 1.0.0
# LAST MODIFIED: 2026-05-02
# DESCRIPTION: Модуль визуализации бизнес-аналитики и активности нейросети.
# PURPOSE: Преобразование собранных лидов в статистические графики и отчеты.
# DEPENDENCIES: recharts, lucide-react, framer-motion
# AUTHORS: Human & AI Collaboration
# STATUS: Development
# ==============================================================================

import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { TrendingUp, Users, Target } from 'lucide-react';
import { motion } from 'framer-motion';
import { BarChart, Bar, XAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Activity, Users, Zap, TrendingUp } from 'lucide-react';

const mockAnalytics = [
  { category: 'Woodwork', count: 24, color: '#06b6d4' },
  { category: 'Design', count: 18, color: '#3b82f6' },
  { category: 'Delivery', count: 12, color: '#8b5cf6' },
  { category: 'Warranty', count: 9, color: '#ec4899' },
];

const data = [
  { name: 'Web Dev', leads: 12, color: '#22d3ee' },
  { name: 'E-commerce', leads: 19, color: '#818cf8' },
  { name: 'Consulting', leads: 7, color: '#c084fc' },
  { name: 'Design', leads: 15, color: '#2dd4bf' },
];

export const InsightPanel = () => {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="p-8 h-full bg-slate-950 text-cyan-500 font-mono"
    >
      <div className="grid grid-cols-4 gap-6 mb-8">
        {[
          { label: 'Neural Leads', val: '128', icon: <Users size={16}/> },
          { label: 'AI Confidence', val: '94.2%', icon: <Zap size={16}/> },
          { label: 'Growth', val: '+12%', icon: <TrendingUp size={16}/> },
          { label: 'System Load', val: '0.4ms', icon: <Activity size={16}/> },
        ].map((stat, i) => (
          <div key={i} className="border border-cyan-500/20 bg-cyan-500/5 p-4 flex flex-col">
            <span className="text-cyan-700 text-[10px] uppercase mb-1 flex items-center gap-2">
              {stat.icon} {stat.label}
            </span>
            <span className="text-2xl font-black text-white">{stat.val}</span>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6">
        <div className="border border-cyan-500/10 bg-black/40 p-6 relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-cyan-500 to-transparent opacity-50"></div>
          <h3 className="text-xs font-bold uppercase mb-8 tracking-[0.2em]">Lead Distribution Analysis</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={mockAnalytics}>
                <XAxis dataKey="category" stroke="#164e63" fontSize={10} tickLine={false} axisLine={false} />
                <Tooltip
                  cursor={{fill: '#083344'}}
                  contentStyle={{ backgroundColor: '#000', border: '1px solid #06b6d4', fontSize: '10px' }}
                />
                <Bar dataKey="count" radius={[2, 2, 0, 0]}>
                  {mockAnalytics.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} fillOpacity={0.4} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </motion.div>
  );
};


export const InsightPanel = () => {
  return (
    <div className="p-6 grid grid-cols-12 gap-6 bg-black/20 h-full overflow-y-auto">
      {/* Stats Cards */}
      <div className="col-span-12 grid grid-cols-3 gap-4">
        {[
          { label: 'Total Leads', val: '53', icon: <Users />, color: 'text-cyan-500' },
          { label: 'Conv. Rate', val: '24%', icon: <Target />, color: 'text-purple-500' },
          { label: 'AI Efficiency', val: '98%', icon: <TrendingUp />, color: 'text-green-500' },
        ].map((stat, i) => (
          <div key={i} className="bg-slate-900/50 border border-cyan-500/10 p-4 rounded-lg">
            <div className={`mb-2 ${stat.color}`}>{stat.icon}</div>
            <div className="text-2xl font-black text-white">{stat.val}</div>
            <div className="text-[10px] uppercase tracking-tighter text-slate-500">{stat.label}</div>
          </div>
        ))}
      </div>

      {/* Chart Section */}
      <div className="col-span-8 bg-slate-900/30 border border-white/5 p-6 rounded-xl">
        <h3 className="text-xs font-bold uppercase mb-6 text-cyan-700">Market Interest Distribution</h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data}>
              <XAxis dataKey="name" stroke="#334155" fontSize={10} />
              <Tooltip
                contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', fontSize: '10px' }}
                itemStyle={{ color: '#22d3ee' }}
              />
              <Bar dataKey="leads" radius={[4, 4, 0, 0]}>
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} fillOpacity={0.6} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Activity Feed */}
      <div className="col-span-4 bg-black/40 border border-cyan-500/5 p-4 rounded-xl">
        <h3 className="text-xs font-bold uppercase mb-4 text-slate-500">Live Agent Activity</h3>
        <div className="space-y-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="text-[10px] border-l border-cyan-500/30 pl-3 py-1">
              <div className="text-cyan-400">Task: Lead Extraction</div>
              <div className="text-slate-600 italic">Processing message from node_882...</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};