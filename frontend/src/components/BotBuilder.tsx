    import React, { useState, useMemo, useEffect } from 'react';
    import * as Icons from 'lucide-react';
    import { motion, AnimatePresence } from 'framer-motion';

    // --- FULL RESOURCE LIBRARY (EXTENDED & RESTORED) ---
    const LIBRARY_RESOURCES = [
      {
        id: 'core',
        label: 'Kernel_v9',
        cat: 'SYSTEM',
        icon: 'Cpu',
        weight: 15,
        desc: 'Центральное ядро управления системой и маршрутизацией запросов.',
        defaultLogic: { text: "СИСТЕМА АКТИВИРОВАНА. ОЖИДАНИЕ КОМАНДЫ ПОЛЬЗОВАТЕЛЯ...", buttons: ["START", "INFO", "HELP"] }
      },
      {
        id: 'ai_gpt',
        label: 'GPT-4_Turbo',
        cat: 'AI_LOGIC',
        icon: 'Brain',
        weight: 45,
        desc: 'Семантическая обработка нейросетью последнего поколения.',
        defaultLogic: { text: "НЕЙРОСЕТЬ ПОДКЛЮЧЕНА. ВВЕДИТЕ ВАШ ЗАПРОС ДЛЯ ОБРАБОТКИ:", buttons: ["CLEAR_CONTEXT", "REGENERATE"] }
      },
      {
        id: 'pay_crypto',
        label: 'Crypto_Pay',
        cat: 'FINANCE',
        icon: 'Coins',
        weight: 30,
        desc: 'Автоматизированный шлюз приема платежей USDT / BTC / TON.',
        defaultLogic: { text: "ВЫБЕРИТЕ УДОБНУЮ ВАЛЮТУ ДЛЯ ОПЛАТЫ УСЛУГ:", buttons: ["USDT_TRC20", "TON_COIN", "BTC_BLOCK"] }
      },
      {
        id: 'db_pg',
        label: 'Postgres_DB',
        cat: 'DATA',
        icon: 'Database',
        weight: 20,
        desc: 'Высокопроизводительное хранилище данных и системных логов.',
        defaultLogic: { text: "БАЗА ДАННЫХ СИНХРОНИЗИРОВАНА. ВСЕ ЛОГИ ЗАПИСАНЫ.", buttons: ["VIEW_LOGS", "BACKUP_DATA", "PURGE"] }
      },
      {
        id: 'sec_guard',
        label: 'Guard_Unit',
        cat: 'SECURITY',
        icon: 'Shield',
        weight: 25,
        desc: 'Система предотвращения флуда и защиты от DDoS атак.',
        defaultLogic: { text: "ФИЛЬТРАЦИЯ ТРАФИКА ВКЛЮЧЕНА. УГРОЗ НЕ ОБНАРУЖЕНО.", buttons: ["STATUS", "SHIELD_ON", "IP_BAN"] }
      },
      {
        id: 'api_web',
        label: 'Webhook_API',
        cat: 'SYSTEM',
        icon: 'Link',
        weight: 15,
        desc: 'Интеграция с внешними API и обработка входящих вебхуков.',
        defaultLogic: { text: "WEBHOOK СЛУШАЕТ ПОРТ 8080. ОЖИДАНИЕ ТРАФИКА...", buttons: ["REBOOT_API", "STATS", "RETRY"] }
      },
      // --- НОВЫЕ МОДУЛИ (РАСШИРЕНИЕ ФУНКЦИОНАЛА) ---
      {
        id: 'media_srv',
        label: 'Media_Storage',
        cat: 'ASSETS',
        icon: 'Image',
        weight: 18,
        desc: 'Облачное хранилище для медиафайлов и генерация временных ссылок.',
        defaultLogic: { text: "МЕДИА-СЕРВЕР АКТИВЕН. ЗАГРУЗИТЕ ИЗОБРАЖЕНИЕ ИЛИ ВИДЕО:", buttons: ["GALLERY", "OPTIMIZE", "CDN_LINK"] }
      },
      {
        id: 'log_analyzer',
        label: 'Log_Hunter',
        cat: 'DEBUG',
        icon: 'Terminal',
        weight: 12,
        desc: 'Продвинутый мониторинг ошибок и аномального поведения пользователей.',
        defaultLogic: { text: "АНАЛИЗАТОР ЗАПУЩЕН. ОШИБОК ЗА 24Ч: 0. ПОДОЗРИТЕЛЬНЫХ СЕССИЙ: 2.", buttons: ["DUMP_ERROR", "CLEAN_CACHE"] }
      },
      {
        id: 'cron_bot',
        label: 'Scheduler_v2',
        cat: 'AUTOMATION',
        icon: 'Clock',
        weight: 10,
        desc: 'Планировщик задач, рассылок и автоматических бэкапов по времени.',
        defaultLogic: { text: "ПЛАНИРОВЩИК АКТИВЕН. СЛЕДУЮЩАЯ РАССЫЛКА ЧЕРЕЗ 04:20:15.", buttons: ["NEW_TASK", "PAUSE_ALL"] }
      },
      {
        id: 'stat_engine',
        label: 'Data_Metrics',
        cat: 'ANALYTICS',
        icon: 'BarChart3',
        weight: 14,
        desc: 'Сбор детальной статистики по каждой команде и конверсии кнопок.',
        defaultLogic: { text: "СТАТИСТИКА ОБНОВЛЕНА. DAU: 1,420. КОНВЕРСИЯ В ОПЛАТУ: 4.2%.", buttons: ["EXPORT_CSV", "LIVE_GRAPH"] }
      },
    ];

    export function BotBuilder() {
      const [tab, setTab] = useState<'BUILD' | 'STYLE' | 'DEPLOY'>('BUILD');
      const [selectedNodes, setSelectedNodes] = useState<string[]>(['core', 'ai_gpt', 'sec_guard', 'stat_engine']);
      const [inspectId, setInspectId] = useState<string | null>('core');

      // States для кастомизации
      const [theme, setTheme] = useState({ primary: '#f97316', radius: '24px', glass: true, noise: true });
      const [botFlowLogic, setBotFlowLogic] = useState<Record<string, any>>(
        LIBRARY_RESOURCES.reduce((acc, m) => ({ ...acc, [m.id]: m.defaultLogic }), {})
      );

      const inspected = useMemo(() => LIBRARY_RESOURCES.find(m => m.id === inspectId), [inspectId]);

      // Движок расчета параметров
      const complexity = useMemo(() => {
        const totalWeight = selectedNodes.reduce((acc, id) => acc + (LIBRARY_RESOURCES.find(m => m.id === id)?.weight || 0), 0);
        return {
            val: Math.min(totalWeight, 100),
            label: totalWeight > 90 ? 'INDUSTRIAL_MAX' : totalWeight > 60 ? 'ADVANCED_UNIT' : 'STABLE_CORE',
            eta: Math.round(totalWeight * 1.8),
            ram: (totalWeight * 14.2).toFixed(1),
            uptime: "99.99%"
        };
      }, [selectedNodes]);

      const GetIcon = ({ name, size = 20, className = "" }: { name: string, size?: number, className?: string }) => {
        const IconComponent = (Icons as any)[name] || Icons.HelpCircle;
        return <IconComponent size={size} className={className} />;
      };

      return (
        <div className="h-screen w-full bg-[#030304] text-zinc-300 flex flex-col font-mono overflow-hidden selection:bg-orange-500/30">

          {/* --- HEADER (INDUSTRIAL DESIGN) --- */}
          <nav className="h-20 border-b border-orange-500/20 bg-[#0a0a0c] flex items-center justify-between px-10 shrink-0 z-[100] relative">
            <div className="flex items-center gap-8">
              <div className="flex items-center gap-4 bg-orange-500 px-6 py-3 rounded-2xl shadow-[0_0_50px_rgba(249,115,22,0.4)] transform -skew-x-12 group cursor-pointer hover:scale-105 transition-transform">
                <Icons.Zap size={26} className="text-black group-hover:animate-pulse" fill="currentColor" />
                <span className="text-black font-black text-3xl tracking-tighter uppercase italic skew-x-12">Factory_OS</span>
              </div>
              <div className="flex flex-col border-l border-white/10 pl-8">
                <span className="text-[10px] font-black text-zinc-600 tracking-[0.6em] uppercase leading-none mb-1">Architecture v5.5 PRO</span>
                <span className="text-xs font-black text-green-500 flex items-center gap-2">
                   <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse shadow-[0_0_10px_#22c55e]" />
                   SYS_STATUS: OPTIMAL
                </span>
              </div>
            </div>

            <div className="absolute left-1/2 -translate-x-1/2 flex bg-black/80 rounded-[2rem] p-1.5 border border-white/5 shadow-2xl backdrop-blur-xl">
              {['BUILD', 'STYLE', 'DEPLOY'].map(t => (
                <button key={t} onClick={() => setTab(t as any)}
                  className={`px-14 py-3.5 rounded-[1.5rem] text-[11px] font-black tracking-[0.4em] transition-all duration-500 relative overflow-hidden group ${tab === t ? 'bg-zinc-800 text-white shadow-2xl border border-white/10' : 'text-zinc-600 hover:text-zinc-300'}`}
                >
                  {tab === t && <motion.div layoutId="tab-bg" className="absolute inset-0 bg-gradient-to-r from-orange-500/10 to-transparent" />}
                  <span className="relative z-10">{t}</span>
                </button>
              ))}
            </div>

            <div className="flex items-center gap-6 bg-zinc-900/40 px-8 py-2.5 rounded-[2rem] border border-white/5">
               <div className="text-right leading-none">
                  <span className="text-[9px] font-black text-zinc-600 uppercase block mb-1 tracking-widest italic">Node_Cluster</span>
                  <span className={`text-xl font-black italic tracking-tighter ${complexity.val > 70 ? 'text-orange-500' : 'text-white'}`}>{complexity.label}</span>
               </div>
               <div className="h-10 w-px bg-white/5" />
               <Icons.Gauge size={32} className={complexity.val > 70 ? 'text-orange-500' : 'text-zinc-500'} />
            </div>
          </nav>

          <div className="flex-1 flex overflow-hidden">
            <AnimatePresence mode="wait">

              {/* --- TAB 1: BUILD --- */}
              {tab === 'BUILD' && (
                <motion.div key="b" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex-1 flex w-full">

                  {/* LEFT: REPOSITORY */}
                  <aside className="w-[20%] border-r border-white/5 bg-[#08080a] flex flex-col shrink-0">
                    <div className="p-8 border-b border-white/5 bg-black/20 relative overflow-hidden">
                       <div className="absolute top-0 right-0 p-2 opacity-10"><Icons.Box size={80}/></div>
                       <h3 className="text-xs font-black text-zinc-500 uppercase tracking-[0.5em] mb-6 flex items-center gap-3 relative z-10">
                         <Icons.Layers size={16} className="text-orange-500"/> Node_Pool
                       </h3>
                       <div className="relative z-10">
                          <Icons.Search size={18} className="absolute left-4 top-4 text-zinc-700" />
                          <input placeholder="SEARCH_SYSTEM..." className="w-full bg-black/50 border border-white/10 rounded-2xl pl-12 pr-4 py-4 text-xs font-bold text-white outline-none focus:border-orange-500/50 transition-all placeholder:text-zinc-800" />
                       </div>
                    </div>

                    <div className="flex-1 overflow-y-auto p-6 space-y-4 custom-scrollbar">
                      {LIBRARY_RESOURCES.map(m => {
                        const isSelected = selectedNodes.includes(m.id);
                        return (
                          <motion.div key={m.id}
                            whileHover={{ x: 5 }}
                            onClick={() => !isSelected ? setSelectedNodes([...selectedNodes, m.id]) : setSelectedNodes(selectedNodes.filter(id => id !== m.id))}
                            className={`p-6 rounded-[2.5rem] border-2 transition-all cursor-pointer group relative overflow-hidden ${isSelected ? 'border-orange-500 bg-orange-500/5 shadow-[0_0_30px_rgba(249,115,22,0.1)]' : 'border-white/5 bg-white/[0.02] hover:border-white/10'}`}
                          >
                            <div className="flex items-center gap-5 relative z-10">
                              <div className={`p-4 rounded-2xl transform transition-transform group-hover:rotate-12 ${isSelected ? 'bg-orange-500 text-black shadow-lg' : 'bg-zinc-800 text-zinc-500 group-hover:text-white'}`}>
                                <GetIcon name={m.icon} size={24} />
                              </div>
                              <div className="min-w-0">
                                <div className="text-sm font-black text-white uppercase tracking-tight truncate">{m.label}</div>
                                <div className="text-[10px] text-zinc-600 font-black uppercase mt-1 italic tracking-[0.2em]">{m.cat}</div>
                              </div>
                            </div>
                            {isSelected && <div className="absolute right-4 top-1/2 -translate-y-1/2"><Icons.X size={16} className="text-orange-500 hover:text-white" /></div>}
                          </motion.div>
                        );
                      })}
                    </div>
                  </aside>

                  {/* CENTER: CANVAS */}
                  <main className="w-[50%] relative bg-[#050506] border-r border-white/5 flex flex-col overflow-hidden">
                    <div className="absolute inset-0 bg-[radial-gradient(#1a1a1a_2px,transparent_2px)] [background-size:48px_48px] opacity-30 pointer-events-none" />

                    <div className="flex-1 overflow-x-auto flex items-center p-16 gap-14 custom-scrollbar">
                      {selectedNodes.map((id, idx) => {
                        const m = LIBRARY_RESOURCES.find(item => item.id === id)!;
                        const isActive = inspectId === id;
                        return (
                          <motion.div layout key={id} onClick={() => setInspectId(id)}
                            initial={{ scale: 0.8, opacity: 0, x: 50 }} animate={{ scale: 1, opacity: 1, x: 0 }}
                            className={`w-80 h-[560px] shrink-0 rounded-[4.5rem] border-2 p-12 flex flex-col relative transition-all cursor-pointer transform ${isActive ? 'border-orange-500 bg-[#0c0c0e] shadow-[0_0_100px_rgba(249,115,22,0.2)] scale-105 z-20' : 'border-white/5 bg-[#0c0c0e]/60 opacity-40 grayscale hover:grayscale-0 hover:opacity-70'}`}
                          >
                            <div className="text-[10px] font-black text-zinc-700 mb-12 tracking-[0.5em] uppercase flex justify-between border-b border-white/5 pb-4">
                                <span>UID: {id.toUpperCase()}</span>
                                {isActive && <div className="w-2 h-2 bg-orange-500 rounded-full animate-ping" />}
                            </div>
                            <div className="flex-1 space-y-10">
                               <div className="flex items-center gap-6">
                                 <div className={`p-6 rounded-[2.5rem] shadow-2xl ${isActive ? 'bg-orange-500 text-black' : 'bg-zinc-800 text-zinc-500'}`}>
                                    <GetIcon name={m.icon} size={36} />
                                 </div>
                                 <h3 className="text-3xl font-black text-white italic uppercase tracking-tighter leading-none">{m.label}</h3>
                               </div>
                               <p className="text-[14px] text-zinc-400 leading-relaxed font-bold uppercase italic tracking-tighter border-l-2 border-orange-500/30 pl-6">
                                 "{botFlowLogic[id]?.text}"
                               </p>
                            </div>
                            <div className="flex flex-wrap gap-2.5 mt-auto pt-10 border-t border-white/5">
                               {botFlowLogic[id]?.buttons.map((b:string, i:number) => (
                                 <div key={i} className="px-5 py-2.5 bg-black rounded-2xl text-[9px] border border-white/10 font-black uppercase text-zinc-600">{b}</div>
                               ))}
                            </div>
                          </motion.div>
                        );
                      })}
                    </div>
                  </main>

                  {/* RIGHT: INSPECTOR */}
                  <aside className="w-[30%] border-l border-white/5 bg-[#08080a] p-14 overflow-y-auto shrink-0 relative">
                    {inspected ? (
                      <motion.div initial={{ opacity: 0, x: 40 }} animate={{ opacity: 1, x: 0 }} className="space-y-14 relative z-10">
                        <div className="space-y-4">
                          <div className="text-orange-500 font-black text-[10px] tracking-[0.6em] uppercase italic flex items-center gap-3">
                            <Icons.Terminal size={14}/> Node_Configuration_Mode
                          </div>
                          <h2 className="text-7xl font-black text-white uppercase italic leading-[0.8] tracking-tighter">{inspected.label}</h2>
                          <p className="text-xs text-zinc-600 font-bold uppercase mt-6 leading-relaxed tracking-widest">{inspected.desc}</p>
                        </div>

                        <div className="space-y-8">
                          <label className="text-xs font-black text-zinc-500 uppercase tracking-[0.4em] flex items-center gap-3">
                            <Icons.ChevronRight size={14} className="text-orange-500"/> Content_Payload
                          </label>
                          <textarea
                            value={botFlowLogic[inspected.id].text}
                            onChange={(e) => setBotFlowLogic({...botFlowLogic, [inspected.id]: {...botFlowLogic[inspected.id], text: e.target.value.toUpperCase()}})}
                            className="w-full h-64 bg-black border border-white/10 rounded-[3rem] p-10 text-[15px] font-bold text-zinc-300 focus:border-orange-500 outline-none transition-all shadow-[inset_0_0_40px_rgba(0,0,0,0.5)] leading-relaxed resize-none"
                          />
                        </div>

                        <div className="space-y-8">
                          <label className="text-xs font-black text-zinc-500 uppercase tracking-[0.4em] flex justify-between">
                            <span>Action_Matrix</span>
                            <span className="text-orange-500">{botFlowLogic[inspected.id].buttons.length}_SLOTS</span>
                          </label>
                          <div className="grid grid-cols-1 gap-4">
                             {botFlowLogic[inspected.id].buttons.map((btn: string, i: number) => (
                               <motion.div layout key={i} className="flex items-center justify-between bg-white/5 p-7 rounded-[2rem] border border-white/5 group hover:border-orange-500 transition-all hover:bg-orange-500/5">
                                  <span className="text-xs font-black uppercase text-zinc-400 group-hover:text-white tracking-[0.2em] italic">{btn}</span>
                                  <Icons.X size={18} className="text-zinc-800 hover:text-red-500 cursor-pointer transition-colors"
                                    onClick={() => {
                                      const newBtns = botFlowLogic[inspected.id].buttons.filter((_:any, idx:any) => idx !== i);
                                      setBotFlowLogic({...botFlowLogic, [inspected.id]: {...botFlowLogic[inspected.id], buttons: newBtns}});
                                    }}
                                  />
                               </motion.div>
                             ))}
                             <button onClick={() => {
                                const b = prompt("DEFINE_ACTION_NAME:");
                                if(b) setBotFlowLogic({...botFlowLogic, [inspected.id]: {...botFlowLogic[inspected.id], buttons: [...botFlowLogic[inspected.id].buttons, b.toUpperCase()]}});
                             }} className="w-full py-8 rounded-[2.5rem] border-2 border-dashed border-white/10 text-[11px] font-black uppercase text-zinc-700 hover:text-orange-500 hover:border-orange-500 transition-all">
                                + Inject_New_Action_Slot
                             </button>
                          </div>
                        </div>
                      </motion.div>
                    ) : (
                      <div className="h-full flex flex-col items-center justify-center opacity-20">
                        <Icons.Cpu size={80} className="text-zinc-500 animate-spin-slow" />
                      </div>
                    )}
                  </aside>
                </motion.div>
              )}

              {/* --- TAB 2: STYLE --- */}
              {tab === 'STYLE' && (
                <motion.div key="s" initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} className="flex-1 flex items-center justify-center gap-40 p-20">
                   <div className="w-[450px] space-y-20">
                      <h2 className="text-[140px] font-black italic uppercase tracking-tighter leading-[0.7] text-white">Visual<br/>Matrix</h2>

                      <div className="space-y-16">
                         <div className="space-y-8">
                            <label className="text-xs font-black uppercase text-zinc-600 tracking-[0.4em]">Global_Accent</label>
                            <div className="flex gap-5">
                               {['#f97316', '#3b82f6', '#22c55e', '#ef4444', '#a855f7'].map(c => (
                                 <button key={c} onClick={() => setTheme({...theme, primary: c})}
                                   className={`w-14 h-14 rounded-2xl transition-all ${theme.primary === c ? 'scale-125 ring-4 ring-white shadow-2xl z-10' : 'opacity-20 hover:opacity-100'}`}
                                   style={{backgroundColor: c}}
                                 />
                               ))}
                            </div>
                         </div>

                         <div className="space-y-10">
                            <div className="flex justify-between text-xs font-black uppercase text-zinc-500 tracking-widest">
                               <span>Interface_Curvature</span>
                               <span className="text-white bg-zinc-900 px-3 py-1 rounded-md">{theme.radius}</span>
                            </div>
                            <input type="range" min="0" max="64" step="4" value={parseInt(theme.radius)}
                              onChange={(e) => setTheme({...theme, radius: `${e.target.value}px`})}
                              className="w-full h-2 bg-zinc-900 rounded-lg appearance-none cursor-pointer accent-orange-500"
                            />
                         </div>
                      </div>
                   </div>

                   {/* TG SIMULATOR */}
                   <div className="w-[440px] h-[880px] bg-black rounded-[6rem] border-[20px] border-zinc-900 shadow-[0_0_200px_rgba(249,115,22,0.15)] relative overflow-hidden flex flex-col">
                      <div className="h-14 w-full bg-zinc-900 flex justify-center items-end pb-4 border-b border-white/5"><div className="w-36 h-7 bg-black rounded-full" /></div>
                      <div className="flex-1 p-10 flex flex-col justify-end">
                         <div className="space-y-8">
                            <motion.div initial={{ y: 50, opacity: 0 }} animate={{ y: 0, opacity: 1 }}
                              className="bg-zinc-900/95 p-10 border border-white/10 shadow-2xl"
                              style={{ borderRadius: theme.radius, borderBottomLeftRadius: '4px' }}
                            >
                               <p className="text-[14px] font-black text-white italic uppercase tracking-tight">
                                 {inspected ? botFlowLogic[inspected.id].text : "SYSTEM_READY_FOR_PREVIEW"}
                               </p>
                            </motion.div>

                            <div className="grid grid-cols-1 gap-4">
                               {(inspected ? botFlowLogic[inspected.id].buttons : ["ACTION_01", "ACTION_02"]).map((b: string, i: number) => (
                                 <button key={i} className="py-6 text-xs font-black uppercase tracking-[0.3em] text-black"
                                  style={{ backgroundColor: theme.primary, borderRadius: theme.radius }}
                                 >
                                   {b}
                                 </button>
                               ))}
                            </div>
                         </div>
                      </div>
                      <div className="h-28 bg-zinc-900/90 border-t border-white/5 flex items-center px-10 gap-6">
                         <div className="w-14 h-14 rounded-full bg-zinc-800 flex items-center justify-center text-zinc-600"><Icons.Smile size={28}/></div>
                         <div className="flex-1 h-14 bg-black rounded-full border border-white/5 px-8 flex items-center text-[11px] text-zinc-700 font-black italic tracking-[0.4em]">ENTER_COMMAND...</div>
                      </div>
                   </div>
                </motion.div>
              )}

              {/* --- TAB 3: DEPLOY --- */}
              {tab === 'DEPLOY' && (
                 <motion.div key="d" initial={{ opacity: 0, y: 100 }} animate={{ opacity: 1, y: 0 }} className="flex-1 flex flex-col items-center justify-center p-20">
                    <div className="max-w-7xl w-full bg-[#0a0a0c] border border-orange-500/20 rounded-[6rem] p-24 space-y-20 shadow-[0_0_250px_rgba(0,0,0,1)] relative overflow-hidden">
                       <div className="absolute top-0 right-0 p-20 opacity-[0.03] rotate-12"><Icons.Rocket size={400}/></div>

                       <div className="flex items-center gap-16 relative z-10">
                          <div className="w-40 h-40 bg-orange-500 rounded-[4rem] flex items-center justify-center shadow-[0_0_100px_rgba(249,115,22,0.4)] animate-pulse">
                             <Icons.Rocket size={80} className="text-black" />
                          </div>
                          <h2 className="text-[140px] font-black italic uppercase tracking-tighter leading-none text-white">E_XECUTE</h2>
                       </div>

                       <div className="grid grid-cols-2 gap-20 relative z-10">
                          <div className="space-y-8">
                            <span className="text-[11px] font-black text-zinc-600 uppercase tracking-[0.6em]">System_Manifest.json</span>
                            <div className="bg-black/90 rounded-[4rem] p-16 border border-white/5 font-mono text-[12px] text-green-500/80 leading-relaxed h-[450px] overflow-y-auto custom-scrollbar shadow-inner">
                               <pre>{JSON.stringify({
                                 factory_auth: "BONDAREV_ENGINEERING_PRO",
                                 build_id: `WF-PRO-99`,
                                 complexity: complexity.label,
                                 nodes: selectedNodes,
                                 ram_alloc: `${complexity.ram}MB`,
                                 ui_matrix: theme,
                                 logic_map: botFlowLogic
                               }, null, 3)}</pre>
                            </div>
                          </div>

                          <div className="flex flex-col gap-12 pt-10">
                             <span className="text-[11px] font-black text-zinc-600 uppercase tracking-[0.6em]">Project_Structure_Preview</span>
                             <div className="flex-1 grid grid-rows-2 gap-8">
                                <div className="bg-white/[0.03] rounded-[4rem] border border-white/5 p-12 flex items-center gap-12 hover:bg-orange-500/10 transition-all cursor-pointer group">
                                   <Icons.FolderTree size={60} className="text-zinc-800 group-hover:text-orange-500" />
                                   <div>
                                      <h4 className="text-4xl font-black text-white uppercase italic tracking-tighter">APP_BUNDLE.ZIP</h4>
                                      <p className="text-[11px] text-zinc-600 font-black uppercase mt-3 italic">Ready for production v3.11</p>
                                   </div>
                                </div>
                                <div className="bg-white/[0.03] rounded-[4rem] border border-white/5 p-12 flex items-center gap-12 hover:bg-orange-500/10 transition-all cursor-pointer group">
                                   <Icons.Box size={60} className="text-zinc-800 group-hover:text-orange-500" />
                                   <div>
                                      <h4 className="text-4xl font-black text-white uppercase italic tracking-tighter">DOCKER_COMPOSE</h4>
                                      <p className="text-[11px] text-zinc-600 font-black uppercase mt-3 italic">Linux_Alpine / Python_Env</p>
                                   </div>
                                </div>
                             </div>
                          </div>
                       </div>

                       <button className="w-full py-16 bg-white hover:bg-orange-500 text-black text-5xl font-black uppercase tracking-[1em] rounded-[3.5rem] transition-all transform active:scale-[0.98] italic">
                          LAUNCH_DEPLOY
                       </button>
                    </div>
                 </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* --- FOOTER (THE MANIFESTO) --- */}
          <footer className="h-32 bg-[#050506] border-t border-orange-500/30 flex items-center justify-between px-20 relative overflow-hidden shrink-0">
             <div className="flex flex-col border-l-4 border-orange-500 pl-10">
                <h4 className="text-4xl font-black text-white italic tracking-tighter leading-none uppercase">Webfactory_OS</h4>
                <span className="text-[10px] font-black text-zinc-700 uppercase tracking-[0.5em] mt-2 italic">Bondarev_Engineering_Unit // Stable_5.5</span>
             </div>

             <div className="max-w-2xl text-right space-y-4">
                <p className="text-3xl font-black text-zinc-500 italic uppercase tracking-tighter opacity-80">
                  "We can build your name. We do it because we can!"
                </p>
                <div className="flex items-center justify-end gap-12 text-[10px] font-black text-zinc-800 uppercase tracking-[0.5em] italic">
                   <span className="text-green-600 flex items-center gap-2"><div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"/> CLUSTER_STABLE</span>
                   <span>CPU: {complexity.val}%</span>
                   <span>RAM: {complexity.ram}MB</span>
                   <span>ETA: {complexity.eta}s</span>
                </div>
             </div>
          </footer>
        </div>
      );
    }

    export default BotBuilder;