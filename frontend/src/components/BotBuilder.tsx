import React, { useState, useMemo, useEffect, useCallback, useRef } from 'react';
import * as Icons from 'lucide-react';
import { motion, AnimatePresence, LayoutGroup } from 'framer-motion';

// --- ПОЛНАЯ ТИПИЗАЦИЯ СИСТЕМЫ ---
export type ComplexityLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'ULTRA' | 'CRITICAL';
export type Category = 'SYSTEM' | 'AI_LOGIC' | 'FINANCE' | 'DATA' | 'SECURITY' | 'ASSETS' | 'DEBUG' | 'AUTOMATION';

export interface INodeLogic {
  text: string;
  buttons: string[];
  action_type?: string;
  metadata?: Record<string, any>;
  callback_data?: string;
  parse_mode?: 'HTML' | 'MarkdownV2';
}

export interface INode {
  id: string;
  label: string;
  cat: Category;
  icon: string;
  weight: number;
  complexity_level: ComplexityLevel;
  desc: string;
  security_layer: string;
  version: string;
  uptime_requirement: number;
  defaultLogic: INodeLogic;
}

export interface ITheme {
  primaryColor: string;
  secondaryColor: string;
  backgroundColor: string;
  borderRadius: string;
  glassEffect: boolean;
  noiseOverlay: boolean;
  fontFamily: string;
  borderWeight: string;
  glowIntensity: string;
  accentGlow: boolean;
}

// --- ПОЛНАЯ БИБЛИОТЕКА РЕСУРСОВ ---
const LIBRARY_RESOURCES: INode[] = [
  {
    id: 'core',
    label: 'Kernel_v9',
    cat: 'SYSTEM',
    icon: 'Cpu',
    weight: 15,
    complexity_level: 'LOW',
    security_layer: 'L1_KERNEL',
    version: '9.4.2-stable',
    uptime_requirement: 99.99,
    desc: 'Центральное ядро управления системой. Обеспечивает маршрутизацию между всеми модулями и управление жизненным циклом сессий.',
    defaultLogic: {
      text: "СИСТЕМА АКТИВИРОВАНА. ВАШ ПЕРСОНАЛЬНЫЙ АССИСТЕНТ ГОТОВ К РАБОТЕ. ВЫБЕРИТЕ ДЕЙСТВИЕ:",
      buttons: ["🚀 ЗАПУСК", "📊 СТАТИСТИКА", "⚙️ НАСТРОЙКИ"],
      parse_mode: 'HTML'
    }
  },
  {
    id: 'ai_gpt',
    label: 'GPT-4_Turbo',
    cat: 'AI_LOGIC',
    icon: 'Brain',
    weight: 45,
    complexity_level: 'ULTRA',
    security_layer: 'L5_NEURAL',
    version: '2024.px',
    uptime_requirement: 98.5,
    desc: 'Нейросетевой модуль для глубокого анализа естественного языка, генерации контента и логических выводов в реальном времени.',
    defaultLogic: {
      text: "НЕЙРОСЕТЬ GPT-4 ОЖИДАЕТ ВАШ ЗАПРОС. КОНТЕКСТ ОБНУЛЕН. ЧТО ВАС ИНТЕРЕСУЕТ?",
      buttons: ["📝 СОЗДАТЬ ТЕКСТ", "🔍 АНАЛИЗ ДАННЫХ", "🧹 ОЧИСТИТЬ ПАМЯТЬ"]
    }
  },
  {
    id: 'pay_crypto',
    label: 'Crypto_Pay',
    cat: 'FINANCE',
    icon: 'Coins',
    weight: 35,
    complexity_level: 'HIGH',
    security_layer: 'L7_FINANCIAL',
    version: '3.1.0-enc',
    uptime_requirement: 100,
    desc: 'Криптовалютный шлюз с поддержкой мульти-чейн транзакций. Автоматическая генерация кошельков и проверка подтверждений в блокчейне.',
    defaultLogic: {
      text: "ПЛАТЕЖНЫЙ МОДУЛЬ ИНИЦИАЛИЗИРОВАН. ВЫБЕРИТЕ СПОСОБ ПОПОЛНЕНИЯ БАЛАНСА:",
      buttons: ["💎 TON", "💵 USDT (TRC20)", "₿ BITCOIN"]
    }
  },
  {
    id: 'db_pg',
    label: 'Postgres_DB',
    cat: 'DATA',
    icon: 'Database',
    weight: 20,
    complexity_level: 'MEDIUM',
    security_layer: 'L3_DATA',
    version: '15.4-dist',
    uptime_requirement: 99.9,
    desc: 'Кластер базы данных для надежного хранения пользовательских данных, истории операций и системных настроек.',
    defaultLogic: {
      text: "БАЗА ДАННЫХ В СЕТИ. ВСЕ ТАБЛИЦЫ ОПТИМИЗИРОВАНЫ. ТЕКУЩАЯ НАГРУЗКА: НИЗКАЯ.",
      buttons: ["📁 ПРОСМОТР БД", "💾 СДЕЛАТЬ БЭКАП", "🛠 ОПТИМИЗАЦИЯ"]
    }
  },
  {
    id: 'sec_guard',
    label: 'Guard_Unit',
    cat: 'SECURITY',
    icon: 'Shield',
    weight: 25,
    complexity_level: 'CRITICAL',
    security_layer: 'L9_DEFENSE',
    version: 'v2-shield',
    uptime_requirement: 100,
    desc: 'Активная защита от спама, брутфорса и аномальных паттернов поведения. Интеллектуальный бан-модуль.',
    defaultLogic: {
      text: "МОДУЛЬ БЕЗОПАСНОСТИ GUARD_UNIT АКТИВЕН. ПЕРИМЕТР ПОД КОНТРОЛЕМ. АНОМАЛИЙ НЕ ВЫЯВЛЕНО.",
      buttons: ["🛡 СТАТУС ЗАЩИТЫ", "🚫 СПИСОК БАНОВ", "⚡ ЭКСТРЕННЫЙ СТОП"]
    }
  },
  {
    id: 'api_web',
    label: 'Webhook_API',
    cat: 'SYSTEM',
    icon: 'Link',
    weight: 18,
    complexity_level: 'MEDIUM',
    security_layer: 'L2_NETWORK',
    version: '1.0.4',
    uptime_requirement: 99.5,
    desc: 'Слушатель входящих Webhook-запросов для интеграции с внешними CRM, платежками и сторонними сервисами.',
    defaultLogic: {
      text: "API СЕРВЕР ЗАПУЩЕН. ОЖИДАНИЕ ВХОДЯЩИХ СОЕДИНЕНИЙ НА ПОРТУ 443.",
      buttons: ["🌐 ТЕСТ СВЯЗИ", "📜 ЛОГИ ТРАФИКА", "🔄 ПЕРЕЗАПУСК"]
    }
  },
  {
    id: 'media_srv',
    label: 'Media_Storage',
    cat: 'ASSETS',
    icon: 'Image',
    weight: 22,
    complexity_level: 'MEDIUM',
    security_layer: 'L4_STORAGE',
    version: 'cdn-opt-2',
    uptime_requirement: 99.0,
    desc: 'Хранилище медиа-контента с автоматическим ресайзом изображений и поддержкой облачного CDN.',
    defaultLogic: {
      text: "МЕДИА-СЕРВЕР ГОТОВ. ВСЕ ФАЙЛЫ ДОСТУПНЫ. ВЫБЕРИТЕ ДЕЙСТВИЕ С ГАЛЕРЕЕЙ:",
      buttons: ["🖼 ГАЛЕРЕЯ", "⬆️ ЗАГРУЗИТЬ", "🧹 ОЧИСТИТЬ КЭШ"]
    }
  },
  {
    id: 'log_analyzer',
    label: 'Log_Hunter',
    cat: 'DEBUG',
    icon: 'Terminal',
    weight: 12,
    complexity_level: 'LOW',
    security_layer: 'L1_KERNEL',
    version: 'debug-v3',
    uptime_requirement: 95.0,
    desc: 'Служба мониторинга состояния. Фиксирует каждое действие пользователя для последующего анализа и дебага.',
    defaultLogic: {
      text: "ЛОГ-АНАЛИЗАТОР В РЕЖИМЕ REAL-TIME. ВСЕ СОБЫТИЯ ЗАПИСЫВАЮТСЯ.",
      buttons: ["📄 ПОКАЗАТЬ ЛОГИ", "🐞 НАЙТИ ОШИБКИ", "🗑 СБРОС ЛОГОВ"]
    }
  },
  {
    id: 'auto_cron',
    label: 'Cron_Scheduler',
    cat: 'AUTOMATION',
    icon: 'Clock',
    weight: 14,
    complexity_level: 'MEDIUM',
    security_layer: 'L2_SCHEDULER',
    version: 'cron-9',
    uptime_requirement: 99.9,
    desc: 'Планировщик задач. Рассылки, очистка базы и автоматические отчеты по расписанию.',
    defaultLogic: {
      text: "ПЛАНИРОВЩИК ЗАДАЧ ЗАПУЩЕН. СЛЕДУЮЩЕЕ СОБЫТИЕ ЧЕРЕЗ: 14 МИНУТ.",
      buttons: ["📅 РАСПИСАНИЕ", "➕ НОВАЯ ЗАДАЧА", "⏸ СТОП ВСЕ"]
    }
  }
];

// --- ВСПОМОГАТЕЛЬНЫЕ КОМПОНЕНТЫ ---
const GetLucideIcon = ({ name, size = 24, className = "" }: { name: string, size?: number, className?: string }) => {
  const IconComponent = (Icons as any)[name] || Icons.HelpCircle;
  return <IconComponent size={size} className={className} />;
};

const CustomTerminal = ({ lines }: { lines: string[] }) => {
  const endRef = useRef<HTMLDivElement>(null);
  useEffect(() => endRef.current?.scrollIntoView({ behavior: 'smooth' }), [lines]);

  return (
    <div className="bg-black/90 border border-white/10 rounded-[2rem] p-8 font-mono text-[12px] text-green-500/80 h-full overflow-y-auto custom-scrollbar">
      {lines.map((line, idx) => (
        <div key={idx} className="mb-2 flex gap-4 uppercase italic">
          <span className="text-orange-500/50">[{new Date().toLocaleTimeString()}] SYS:</span>
          <span className="text-zinc-200">{line}</span>
        </div>
      ))}
      <div ref={endRef} />
    </div>
  );
};

// --- ОСНОВНОЙ КОМПОНЕНТ ПРИЛОЖЕНИЯ ---
export function BotBuilder() {
  // 1. СОСТОЯНИЯ (STATES)
  const [activeTab, setActiveTab] = useState<'BUILD' | 'STYLE' | 'INTEGRATE' | 'DEPLOY'>('BUILD');
  const [selectedNodes, setSelectedNodes] = useState<string[]>(['core', 'ai_gpt', 'sec_guard', 'log_analyzer']);
  const [inspectId, setInspectId] = useState<string | null>('core');
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncProgress, setSyncProgress] = useState(0);
  const [isDeploying, setIsDeploying] = useState(false);
  const [deployStep, setDeployStep] = useState('');
  const [terminalOutput, setTerminalOutput] = useState<string[]>(["SYSTEM_READY", "AWAITING_INPUT..."]);

  const [botFlowLogic, setBotFlowLogic] = useState<Record<string, INodeLogic>>(() => {
    return LIBRARY_RESOURCES.reduce((acc, m) => ({
      ...acc,
      [m.id]: JSON.parse(JSON.stringify(m.defaultLogic))
    }), {});
  });

  const [theme, setTheme] = useState<ITheme>({
    primaryColor: '#f97316',
    secondaryColor: '#1a1a1a',
    backgroundColor: '#030304',
    borderRadius: '28px',
    glassEffect: true,
    noiseOverlay: true,
    fontFamily: 'JetBrains Mono',
    borderWeight: '2px',
    glowIntensity: '0.2',
    accentGlow: true
  });

  const scrollRef = useRef<HTMLDivElement>(null);

  // 2. ВЫЧИСЛЯЕМЫЕ ДАННЫЕ (MEMO)
  const infraStats = useMemo(() => {
    const totalWeight = selectedNodes.reduce((acc, id) => {
      const node = LIBRARY_RESOURCES.find(n => n.id === id);
      return acc + (node?.weight || 0);
    }, 0);

    const ramValue = (totalWeight * 14.8) + (selectedNodes.length * 5);
    const cpuValue = Math.min(totalWeight * 0.95, 100);

    let label = 'STABLE_CORE';
    if (totalWeight > 50) label = 'ADVANCED_UNIT';
    if (totalWeight > 85) label = 'INDUSTRIAL_MAX';
    if (totalWeight > 110) label = 'CLUSTER_OVERLOAD';

    return {
      complexityLabel: label,
      ram: ramValue.toFixed(1),
      cpu: cpuValue.toFixed(0),
      eta: Math.round(totalWeight * 2.2),
      nodes: selectedNodes.length,
      loadFactor: totalWeight
    };
  }, [selectedNodes]);

  const activeNodeData = useMemo(() =>
    LIBRARY_RESOURCES.find(m => m.id === inspectId),
  [inspectId]);

  // 3. ОБРАБОТЧИКИ (HANDLERS)
  const handleNodeToggle = useCallback((id: string) => {
    setSelectedNodes(prev =>
      prev.includes(id)
        ? prev.filter(nodeId => nodeId !== id)
        : [...prev, id]
    );
  }, []);

  const updateLogicText = (text: string) => {
    if (!inspectId) return;
    setBotFlowLogic(prev => ({
      ...prev,
      [inspectId]: { ...prev[inspectId], text: text.toUpperCase() }
    }));
  };

  const addActionButton = () => {
    if (!inspectId) return;
    const btnName = prompt("ВВЕДИТЕ НАЗВАНИЕ КНОПКИ (UPPERCASE):");
    if (btnName) {
      setBotFlowLogic(prev => ({
        ...prev,
        [inspectId]: {
          ...prev[inspectId],
          buttons: [...prev[inspectId].buttons, btnName.toUpperCase()]
        }
      }));
      setTerminalOutput(p => [...p, `ADDED_BUTTON: ${btnName.toUpperCase()}`]);
    }
  };

  const removeActionButton = (index: number) => {
    if (!inspectId) return;
    setBotFlowLogic(prev => {
      const currentButtons = [...prev[inspectId].buttons];
      const removed = currentButtons.splice(index, 1);
      setTerminalOutput(p => [...p, `REMOVED_BUTTON: ${removed[0]}`]);
      return {
        ...prev,
        [inspectId]: { ...prev[inspectId], buttons: currentButtons }
      };
    });
  };

  const handleDeploy = () => {
    setIsDeploying(true);
    const steps = [
      'COLLECTING_MANIFEST...',
      'ENCRYPTING_DATA_PACKETS...',
      'CONNECTING_TO_CLUSTER_71...',
      'UPLOADING_DOCKER_IMAGE...',
      'VERIFYING_CHECKSUMS...',
      'DEPLOY_SUCCESSFUL!'
    ];

    steps.forEach((step, index) => {
      setTimeout(() => {
        setDeployStep(step);
        setTerminalOutput(prev => [...prev, `DEPLOY_LOG: ${step}`]);
        if (index === steps.length - 1) setIsDeploying(false);
      }, (index + 1) * 800);
    });
  };

  const triggerLiveSync = () => {
    setIsSyncing(true);
    setSyncProgress(0);
    setTerminalOutput(prev => [...prev, "INITIATING_SYNC_PROTOCOL...", "PACKING_LOGIC_MANIFEST..."]);

    const interval = setInterval(() => {
      setSyncProgress(p => {
        if (p >= 100) {
          clearInterval(interval);
          setTerminalOutput(prev => [...prev, "SYNC_COMPLETE_100%", "REMOTE_CLUSTER_UPDATED."]);
          setTimeout(() => setIsSyncing(false), 800);
          return 100;
        }
        return p + 4;
      });
    }, 80);
  };

  // --- RENDER ---
  return (
    <div
      className="h-screen w-full bg-[#030304] text-zinc-300 flex flex-col font-mono overflow-hidden selection:bg-orange-500/40 selection:text-white"
      style={{ fontFamily: theme.fontFamily }}
    >

      {/* --- HEADER (МАСШТАБ УМЕНЬШЕН В 4 РАЗА) --- */}
      <nav className="h-24 border-b border-orange-500/20 bg-[#0a0a0c] flex items-center justify-between px-8 shrink-0 z-[100] relative shadow-2xl">
        <div className="flex items-center gap-6">
          <motion.div
            whileHover={{ scale: 1.05 }}
            className="flex items-center gap-4 bg-orange-500 px-6 py-3 rounded-2xl shadow-[0_0_40px_rgba(249,115,22,0.3)] transform -skew-x-12 cursor-pointer group"
          >
            <Icons.Zap size={24} className="text-black group-hover:animate-pulse" fill="currentColor" />
            <span className="text-black font-black text-base tracking-tighter uppercase italic skew-x-12">Factory_OS</span>
          </motion.div>

          <div className="flex flex-col border-l-2 border-white/10 pl-6">
            <span className="text-sm font-black text-zinc-600 tracking-[0.2em] uppercase leading-none mb-1 italic">Advanced_Architecture_v5.5</span>
            <div className="flex items-center gap-3">
               <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse shadow-[0_0_10px_#22c55e]" />
               <span className="text-[11px] font-black text-zinc-400 uppercase tracking-widest flex gap-2">
                 SYSTEM_STATUS: <span className="text-green-500">OPTIMAL_REACHED</span>
               </span>
            </div>
          </div>
        </div>

        {/* Tab Switcher (Компактный) */}
        <div className="absolute left-1/2 -translate-x-1/2 flex bg-black/40 rounded-full p-1.5 border border-white/5 backdrop-blur-3xl">
          {['BUILD', 'STYLE', 'INTEGRATE', 'DEPLOY'].map((t) => (
            <button
              key={t}
              onClick={() => setActiveTab(t as any)}
              className={`px-8 py-2 rounded-full text-[13px] font-black tracking-[0.1em] transition-all duration-500 relative overflow-hidden group ${activeTab === t ? 'text-white' : 'text-zinc-600 hover:text-zinc-300'}`}
            >
              {activeTab === t && (
                <motion.div layoutId="nav-pill-active" className="absolute inset-0 bg-gradient-to-b from-zinc-800 to-zinc-900 shadow-xl" />
              )}
              <span className="relative z-10">{t}</span>
            </button>
          ))}
        </div>

        <div className="flex items-center gap-6 bg-zinc-900/40 px-6 py-2.5 rounded-2xl border border-white/5 shadow-2xl">
           <div className="text-right">
              <span className="text-[9px] font-black text-zinc-700 uppercase block tracking-widest italic leading-none">Resource_Load</span>
              <span className={`text-sm font-black italic tracking-tighter uppercase ${infraStats.loadFactor > 90 ? 'text-red-500' : 'text-orange-500'}`}>
                {infraStats.complexityLabel}
              </span>
           </div>
           <Icons.Activity size={24} className={infraStats.loadFactor > 90 ? 'text-red-500 animate-bounce' : 'text-orange-500'} />
        </div>
      </nav>

      {/* --- CONTENT AREA --- */}
      <div className="flex-1 flex overflow-hidden relative">
        <AnimatePresence mode="wait">

          {/* BUILD TAB */}
          {activeTab === 'BUILD' && (
            <motion.div
              key="build_tab"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="flex-1 flex w-full"
            >
              {/* Sidebar Modules */}
              <aside className="w-[20%] border-r border-white/5 bg-[#08080a] flex flex-col shrink-0 shadow-2xl">
                <div className="p-8 border-b border-white/5 bg-black/40">
                   <h3 className="text-[14px] font-black text-zinc-500 uppercase tracking-[0.2em] mb-4 flex items-center gap-3">
                     <Icons.Layers size={18} className="text-orange-500" /> Modules
                   </h3>
                </div>
                <div className="flex-1 overflow-y-auto p-6 space-y-4 custom-scrollbar">
                  {LIBRARY_RESOURCES.map((node) => {
                    const isSelected = selectedNodes.includes(node.id);
                    return (
                      <motion.div
                        key={node.id}
                        onClick={() => handleNodeToggle(node.id)}
                        whileHover={{ scale: 1.02 }}
                        className={`p-4 rounded-3xl border transition-all cursor-pointer group relative overflow-hidden ${isSelected ? 'border-orange-500 bg-orange-500/5 shadow-lg' : 'border-white/5 bg-white/[0.02]'}`}
                      >
                        <div className="flex items-center gap-4">
                          <div className={`p-3 rounded-xl ${isSelected ? 'bg-orange-500 text-black' : 'bg-zinc-800 text-zinc-500'}`}>
                            <GetLucideIcon name={node.icon} size={20} />
                          </div>
                          <div className="min-w-0">
                            <div className="text-[14px] font-black text-white uppercase leading-none">{node.label}</div>
                            <div className="text-[9px] text-zinc-600 font-black uppercase mt-1 italic">{node.cat}</div>
                          </div>
                        </div>
                      </motion.div>
                    );
                  })}
                </div>
              </aside>

              {/* Canvas */}
              <main className="flex-1 relative bg-[#050506] border-r border-white/5 flex flex-col overflow-hidden">
                <div className="absolute inset-0 bg-[radial-gradient(#1e1e1e_1px,transparent_1px)] [background-size:40px_40px] opacity-40 pointer-events-none" />
                <div className="flex-1 overflow-x-auto flex items-center px-16 gap-10 custom-scrollbar" ref={scrollRef}>
                  <LayoutGroup>
                    {selectedNodes.map((id) => {
                      const m = LIBRARY_RESOURCES.find(item => item.id === id)!;
                      const isInspected = inspectId === id;
                      return (
                        <motion.div
                          layout
                          key={id}
                          onClick={() => setInspectId(id)}
                          className={`w-[260px] h-[400px] shrink-0 rounded-[3rem] border p-8 flex flex-col relative transition-all duration-700 cursor-pointer group ${isInspected ? 'border-orange-500 bg-[#0c0c0e] shadow-2xl scale-105 z-20' : 'border-white/5 bg-[#0c0c0e]/40 opacity-30 grayscale'}`}
                        >
                          <div className="text-[9px] font-black text-zinc-700 mb-6 tracking-[0.4em] uppercase flex justify-between italic">
                              <span>UID: {id.toUpperCase()}</span>
                              <span>V.{m.version}</span>
                          </div>
                          <div className="flex-1 space-y-6">
                             <div className="flex items-center gap-4">
                                <div className={`p-4 rounded-2xl ${isInspected ? 'bg-orange-500 text-black' : 'bg-zinc-800 text-zinc-500'}`}>
                                   <GetLucideIcon name={m.icon} size={24} />
                                </div>
                                <div className="space-y-1">
                                   <h3 className="text-xl font-black text-white italic uppercase tracking-tighter leading-none">{m.label}</h3>
                                   <span className="text-[8px] font-black text-orange-500/60 uppercase">{m.security_layer}</span>
                                </div>
                             </div>
                             <p className="text-[12px] text-zinc-300 leading-tight font-black uppercase italic tracking-tighter">
                                "{botFlowLogic[id]?.text}"
                             </p>
                          </div>
                          <div className="flex flex-wrap gap-2 mt-auto pt-6 border-t border-white/5">
                             {botFlowLogic[id]?.buttons.map((b: string, i: number) => (
                               <div key={i} className="px-3 py-1.5 bg-black rounded-lg text-[8px] border border-white/10 font-black uppercase text-zinc-500 tracking-widest italic">
                                  {b}
                               </div>
                             ))}
                          </div>
                        </motion.div>
                      );
                    })}
                  </LayoutGroup>
                </div>
              </main>

              {/* Inspector */}
              <aside className="w-[22%] border-l border-white/5 bg-[#08080a] p-10 overflow-y-auto shrink-0 shadow-2xl">
                {activeNodeData ? (
                  <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-10">
                    <div className="space-y-4">
                      <div className="flex items-center gap-3 text-orange-500 font-black text-[11px] tracking-[0.4em] uppercase italic">
                        <Icons.Settings2 size={16}/> Inspector_v5
                      </div>
                      <h2 className="text-3xl font-black text-white uppercase italic leading-none tracking-tighter">
                        {activeNodeData.label}
                      </h2>
                      <p className="text-[13px] text-zinc-500 font-bold uppercase mt-2 leading-relaxed italic border-l-2 border-orange-500/40 pl-4">
                        {activeNodeData.desc}
                      </p>
                    </div>

                    <div className="space-y-4 bg-black/40 p-6 rounded-3xl border border-white/5 shadow-inner">
                      <label className="text-[10px] font-black text-zinc-500 uppercase tracking-[0.4em] flex items-center gap-3 px-2">
                        <Icons.Type size={16} className="text-orange-500" /> Response_Payload
                      </label>
                      <textarea
                        value={botFlowLogic[activeNodeData.id].text}
                        onChange={(e) => updateLogicText(e.target.value)}
                        className="w-full h-32 bg-black/80 border border-white/10 rounded-2xl p-6 text-[14px] font-black text-zinc-200 focus:border-orange-500 outline-none transition-all resize-none uppercase"
                      />
                    </div>

                    <div className="space-y-4">
                         {botFlowLogic[activeNodeData.id].buttons.map((btn: string, i: number) => (
                           <div key={i} className="flex items-center justify-between bg-white/[0.03] p-4 rounded-2xl border border-white/5">
                              <span className="text-[11px] font-black uppercase text-zinc-400 tracking-[0.2em] italic">{btn}</span>
                              <button onClick={() => removeActionButton(i)} className="p-2 hover:bg-red-500/20 rounded-xl text-zinc-800 hover:text-red-500">
                                <Icons.Trash2 size={16} />
                              </button>
                           </div>
                         ))}
                         <button onClick={addActionButton} className="w-full py-6 rounded-full border border-dashed border-white/10 text-[11px] font-black uppercase text-zinc-700 hover:text-orange-500 hover:border-orange-500 transition-all tracking-[0.2em]">
                            + INJECT_ACTION
                         </button>
                    </div>
                  </motion.div>
                ) : null}
              </aside>
            </motion.div>
          )}

          {/* STYLE TAB */}
          {activeTab === 'STYLE' && (
            <motion.div key="style_tab" className="flex-1 flex items-center justify-center gap-32 p-16 overflow-y-auto">
               <div className="w-[400px] space-y-12">
                  <div className="space-y-4">
                     <span className="text-orange-500 font-black text-2xl tracking-[0.2em] uppercase italic">Visual_System_DNA</span>
                     <h2 className="text-7xl font-black italic uppercase tracking-tighter leading-none text-white">Interface<br/>Matrix</h2>
                  </div>

                  <div className="space-y-10">
                      <div className="space-y-6 bg-white/[0.02] p-8 rounded-3xl border border-white/5">
                            <div className="flex justify-between items-end">
                               <span className="text-3xl font-black text-white italic tracking-tighter uppercase">Radius</span>
                               <span className="text-xl font-black text-orange-500">{theme.borderRadius}</span>
                            </div>
                            <input
                              type="range" min="0" max="80" step="4"
                              value={parseInt(theme.borderRadius)}
                              onChange={(e) => setTheme({...theme, borderRadius: `${e.target.value}px`})}
                              className="w-full h-3 bg-zinc-900 rounded-full appearance-none accent-orange-500"
                            />
                      </div>

                      <div className="space-y-6 bg-white/[0.02] p-8 rounded-3xl border border-white/5">
                            <div className="flex justify-between items-end">
                               <span className="text-3xl font-black text-white italic tracking-tighter uppercase">Tone</span>
                               <input
                                 type="color"
                                 value={theme.primaryColor}
                                 onChange={(e) => setTheme({...theme, primaryColor: e.target.value})}
                                 className="w-16 h-16 bg-transparent border-none cursor-pointer"
                               />
                            </div>
                      </div>
                  </div>
               </div>

               {/* Telegram Simulator */}
               <div className="w-[340px] h-[640px] bg-black rounded-[4rem] border-[14px] border-[#121214] shadow-2xl relative overflow-hidden flex flex-col group shrink-0">
                  <div className="h-10 w-full bg-[#121214] flex justify-center items-end pb-2">
                    <div className="w-24 h-4 bg-black rounded-full" />
                  </div>
                  <div className="bg-[#121214]/80 p-5 flex items-center gap-4 border-b border-white/5">
                     <div className="w-10 h-10 rounded-full bg-orange-500 flex items-center justify-center text-black font-black text-[10px] italic">OS</div>
                     <div>
                        <div className="text-white font-black uppercase text-[10px] tracking-widest flex items-center gap-2">FACTORY_BOT <Icons.CheckCircle2 size={10} className="text-blue-500" fill="currentColor" /></div>
                        <div className="text-green-500 text-[8px] font-bold uppercase">online</div>
                     </div>
                  </div>
                  <div className="flex-1 p-6 flex flex-col justify-end space-y-6">
                     <motion.div
                        className="bg-[#1a1a1e]/98 p-6 border border-white/10 relative overflow-hidden"
                        style={{ borderRadius: theme.borderRadius, borderBottomLeftRadius: '4px' }}
                     >
                        <p className="text-[14px] font-black text-white italic uppercase leading-snug">
                          {activeNodeData ? botFlowLogic[activeNodeData.id].text : "SYSTEM_READY"}
                        </p>
                     </motion.div>
                     <div className="grid grid-cols-1 gap-3">
                        {(activeNodeData ? botFlowLogic[activeNodeData.id].buttons : ["ACTION_PRIMARY"]).map((b: string, i: number) => (
                          <button
                            key={i}
                            className="py-4 text-[12px] font-black uppercase tracking-widest text-black shadow-xl"
                            style={{ backgroundColor: theme.primaryColor, borderRadius: theme.borderRadius }}
                          >
                            {b}
                          </button>
                        ))}
                     </div>
                  </div>
               </div>
            </motion.div>
          )}

          {/* INTEGRATE TAB */}
          {activeTab === 'INTEGRATE' && (
             <motion.div key="int_tab" className="flex-1 flex flex-col items-center justify-center p-16">
                <div className="max-w-4xl w-full bg-[#0a0a0c] border border-orange-500/20 rounded-[4rem] p-16 space-y-12 shadow-3xl">
                    <div className="flex items-center gap-8">
                        <motion.div animate={isSyncing ? { rotate: 360 } : {}} className="w-20 h-20 rounded-3xl bg-orange-500/20 flex items-center justify-center text-orange-500">
                            <Icons.RefreshCw size={40} />
                        </motion.div>
                        <h2 className="text-6xl font-black text-white uppercase italic tracking-tighter leading-none">Live_Sync</h2>
                    </div>

                    <div className="grid grid-cols-2 gap-10 h-[350px]">
                        <div className="space-y-8">
                           <div className="bg-black p-8 rounded-3xl border border-white/10">
                              <span className="text-[12px] font-black text-zinc-600 uppercase tracking-widest mb-2 block italic">Target_Endpoint</span>
                              <input readOnly value="FACTORY_CLUSTER_ALPHA_99" className="w-full bg-transparent text-2xl font-black text-orange-500 italic border-none outline-none" />
                           </div>
                        </div>
                        <CustomTerminal lines={terminalOutput} />
                    </div>

                    <button
                      onClick={triggerLiveSync}
                      disabled={isSyncing}
                      className="w-full py-10 rounded-full bg-white text-black text-4xl font-black uppercase italic hover:bg-orange-500 hover:text-white transition-all shadow-2xl active:scale-95"
                    >
                        {isSyncing ? `PUSHING_${syncProgress}%` : 'PUSH_LIVE_UPGRADE'}
                    </button>
                </div>
             </motion.div>
          )}

          {/* DEPLOY TAB */}
          {activeTab === 'DEPLOY' && (
             <motion.div key="dep_tab" className="flex-1 flex flex-col items-center justify-center p-16">
                <div className="max-w-5xl w-full bg-[#0a0a0c] border border-orange-500/20 rounded-[5rem] p-20 space-y-16 shadow-3xl">
                   <div className="flex items-center gap-10">
                      <div className="w-24 h-24 bg-orange-500 rounded-3xl flex items-center justify-center">
                         <Icons.Zap size={48} className="text-black" />
                      </div>
                      <h2 className="text-8xl font-black italic uppercase tracking-tighter leading-none text-white">E_XECUTE</h2>
                   </div>

                   <div className="grid grid-cols-2 gap-12">
                      <div className="bg-black/95 rounded-3xl p-10 border border-white/10 font-mono text-[14px] text-green-500/90 h-[400px] overflow-y-auto custom-scrollbar">
                         <pre className="whitespace-pre-wrap">
                            {JSON.stringify({
                              manifest_id: "WF-X82",
                              status: "READY",
                              cluster: selectedNodes,
                              stats: infraStats,
                              timestamp: new Date().toISOString()
                            }, null, 4)}
                         </pre>
                      </div>
                      <div className="flex flex-col gap-8">
                         <motion.div whileHover={{ x: 10 }} className="bg-white/[0.04] rounded-3xl border border-white/10 p-10 flex items-center gap-8 hover:bg-orange-500/10 cursor-pointer">
                            <Icons.Container size={48} className="text-orange-500" />
                            <div className="space-y-1">
                               <h4 className="text-4xl font-black text-white uppercase italic tracking-tighter leading-none">DOCKER</h4>
                               <span className="text-[12px] font-black text-zinc-600 uppercase">Containerized Image</span>
                            </div>
                         </motion.div>
                      </div>
                   </div>

                   <button
                     onClick={handleDeploy}
                     disabled={isDeploying}
                     className={`w-full py-12 bg-white text-black text-6xl font-black uppercase tracking-widest rounded-full italic shadow-3xl transition-all duration-700 ${isDeploying ? 'bg-zinc-800 text-orange-500 cursor-wait' : 'hover:bg-orange-500 hover:text-white active:scale-95'}`}
                   >
                      {isDeploying ? deployStep : 'INIT_DEPLOY'}
                   </button>
                </div>
             </motion.div>
          )}

        </AnimatePresence>
      </div>

      {/* --- INDUSTRIAL FOOTER (МАСШТАБ УМЕНЬШЕН В 4 РАЗА) --- */}
      <footer className="h-32 bg-[#050506] border-t border-orange-500/40 flex items-center justify-between px-12 shrink-0 overflow-hidden relative shadow-2xl">
         <div className="flex flex-col border-l-8 border-orange-500 pl-8">
            <h4 className="text-4xl font-black text-white italic tracking-tighter leading-[0.7] uppercase">Webfactory_OS</h4>
            <span className="text-base font-black text-zinc-700 uppercase tracking-[0.2em] mt-4 italic">Bondarev_Engineering_Unit // v5.5.0</span>
         </div>
         <div className="text-right space-y-4 pr-8">
            <p className="text-2xl font-black text-zinc-500 italic uppercase tracking-tighter opacity-60 leading-none">"We build your name."</p>
            <div className="flex items-center justify-end gap-10 text-[13px] font-black text-zinc-800 uppercase tracking-widest italic">
               <span className="text-green-600 flex items-center gap-3"><div className="w-2.5 h-2.5 bg-green-500 rounded-full animate-pulse shadow-[0_0_15px_#22c55e]"/>STABLE</span>
               <span className="flex items-center gap-3"><Icons.Cpu size={16}/> CPU: {infraStats.cpu}%</span>
               <span className="flex items-center gap-3"><Icons.Database size={16}/> RAM: {infraStats.ram}MB</span>
            </div>
         </div>
      </footer>

      {/* --- GLOBAL STYLES --- */}
      <style>{`
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #222; border-radius: 10px; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #f97316; }

        input[type="range"]::-webkit-slider-thumb {
          -webkit-appearance: none;
          width: 24px;
          height: 24px;
          background: #f97316;
          border-radius: 50%;
          cursor: pointer;
          border: 3px solid #fff;
          box-shadow: 0 0 15px rgba(249,115,22,0.5);
          margin-top: -10px;
        }
      `}</style>
    </div>
  );
}

export default BotBuilder;