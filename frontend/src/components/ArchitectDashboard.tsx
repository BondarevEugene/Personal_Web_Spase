import React, { useState, useEffect, useRef, useCallback } from 'react';
import { ReactFlow, Background, Controls, useNodesState, useEdgesState, addEdge } from '@xyflow/react';
import type { Connection } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { CustomNode } from './CustomNode';
import { Layers, Cpu, MessageSquare, Box, Settings, Zap, Terminal as TermIcon, Lock, Unlock, KeyRound, Send, Network, Download, Upload, HardDrive, ShieldAlert, Search, Globe, ChevronRight } from 'lucide-react';

const nodeTypes = { botStep: CustomNode };

export const ArchitectDashboard = () => {
  const [activeTab, setActiveTab] = useState<string>('index');
  const [isAdminAuthenticated, setIsAdminAuthenticated] = useState<boolean>(false);
  const [pinCode, setPinCode] = useState<string>('');
  const [pinError, setPinError] = useState<boolean>(false);

  // Стейт подвкладок внутри самой админки (для имитации кликов по левому внутреннему меню из image_48ad06.png)
  const [adminSubTab, setAdminSubTab] = useState<string>('mainnode');

  // Симулятор ТГ-бота
  const [tgMessages, setTgMessages] = useState<Array<{sender: 'user' | 'bot', text: string}>>([
    { sender: 'bot', text: '⚡ OMNIFACTORY BOT // Канал связи активирован. Готов к приему директив.' }
  ]);
  const [inputMsg, setInputMsg] = useState<string>('');

  // Основные стейты графа (ReactFlow)
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [registry, setRegistry] = useState<any[]>([]);

  const [logs, setLogs] = useState<string[]>([`[${new Date().toLocaleTimeString()}] [SYSTEM] Инженерный узел супервизора OMNIFACTORY MASTER запущен стабильно.`]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const pushLog = (tag: string, text: string) => {
    const time = new Date().toLocaleTimeString();
    setLogs(prev => [`[${time}] [${tag}] ${text}`, ...prev]);
  };

  useEffect(() => {
    setRegistry([
      { id: 'welcome_core', name: 'WELCOME_CORE', type: 'Gateway', cat: 'CHANNELS', desc: 'Стартовая точка авторизации и приветствия.' },
      { id: 'geo_picker', name: 'GEO_PICKER', type: 'Logic', cat: 'UTILITIES', desc: 'Модуль определения геопозиции пользователя.' },
      { id: 'ai_consultant', name: 'ai_consultant.py', type: 'AI_Core', cat: 'AI_ML', desc: 'Интеграция Gemini Flash + RAG контекст.' },
      { id: 'numerology_calc', name: 'numerology_calc.py', type: 'Math_Engine', cat: 'UTILITIES', desc: 'Расчет Квадрата Пифагора.' }
    ]);
  }, []);

  const handleExportConfig = () => {
    const configData = { version: "7.7-Evo", timestamp: new Date().toISOString(), graph: { nodes, edges } };
    const jsonString = `data:text/json;charset=utf-8,${encodeURIComponent(JSON.stringify(configData, null, 2))}`;
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", jsonString);
    downloadAnchor.setAttribute("download", `omnifactory_config_${Date.now()}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
    pushLog('SUCCESS', 'Конфигурация успешно экспортирована.');
  };

  const handleImportConfig = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const parsed = JSON.parse(e.target?.result as string);
        if (parsed && parsed.graph) {
          setNodes(parsed.graph.nodes || []);
          setEdges(parsed.graph.edges || []);
          pushLog('SUCCESS', `Конфигурация [${file.name}] развернута.`);
        }
      } catch (err) {
        pushLog('CRITICAL', 'Ошибка импорта JSON.');
      }
    };
    reader.readAsText(file);
    if (event.target) event.target.value = '';
  };

  const handleSendTgMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMsg.trim()) return;
    const userText = inputMsg;
    setTgMessages(prev => [...prev, { sender: 'user', text: userText }]);
    setInputMsg('');
    setTimeout(() => {
      setTgMessages(prev => [...prev, { sender: 'bot', text: `🤖 Директива принята в рантайм: "${userText}"` }]);
    }, 1000);
  };

  const handleAdminAuth = (e: React.FormEvent) => {
    e.preventDefault();
    if (pinCode === '2305') {
      setIsAdminAuthenticated(true);
      setPinError(false);
      pushLog('SUCCESS', 'Авторизация в контуре администратора пройдена. Доступ к OMNIFACTORY MASTER открыт.');
    } else {
      setPinError(true);
      setPinCode('');
      pushLog('CRITICAL', 'Попытка несанкционированного доступа к панели супервизора!');
      setTimeout(() => setPinError(false), 1000);
    }
  };

  const onConnect = useCallback((params: Connection) => {
    setEdges((eds) => addEdge({ ...params, type: 'smoothstep', animated: true, style: { stroke: '#bc13fe', strokeWidth: 2 } }, eds));
    pushLog('LINK', `Связь: [${params.source}] ➔ [${params.target}]`);
  }, [setEdges]);

  return (
    <div className="w-screen h-screen bg-[#050508] text-white flex overflow-hidden select-none font-mono relative">

      <input type="file" ref={fileInputRef} onChange={handleImportConfig} accept=".json" className="hidden" />

      {/* ГЛОБАЛЬНЫЙ ЛЕВЫЙ САЙДБАР СИСТЕМЫ */}
      <aside className="w-24 bg-[#020204] border-r border-zinc-900 flex flex-col items-center py-6 gap-4 shrink-0 z-30 shadow-[5px_0_25px_rgba(0,0,0,0.8)]">
        <div className="w-14 h-14 relative cursor-pointer group mb-2" onClick={() => setActiveTab('index')}>
          <div className="absolute inset-0 border border-[#bc13fe] rounded-full animate-[spin_5s_linear_infinite] opacity-60" />
          <Layers size={18} className="text-[#bc13fe] absolute inset-0 m-auto" />
        </div>

        <button onClick={() => setActiveTab('index')} className={`w-18 h-14 rounded-xl flex flex-col items-center justify-center gap-1 transition-all border cursor-pointer ${activeTab === 'index' ? 'bg-[#bc13fe]/15 border-[#bc13fe] text-white shadow-[0_0_10px_rgba(188,19,254,0.2)]' : 'border-transparent text-zinc-500 hover:text-zinc-300'}`}>
          <Cpu size={16} />
          <span className="text-[7.5px] font-bold font-sans">MAIN_NODE</span>
        </button>

        <button onClick={() => setActiveTab('builder')} className={`w-18 h-14 rounded-xl flex flex-col items-center justify-center gap-1 transition-all border cursor-pointer ${activeTab === 'builder' ? 'bg-[#bc13fe]/15 border-[#bc13fe] text-white shadow-[0_0_10px_rgba(188,19,254,0.2)]' : 'border-transparent text-zinc-500 hover:text-zinc-300'}`}>
          <Zap size={16} />
          <span className="text-[7.5px] font-bold font-sans">BUILDER</span>
        </button>

        <button onClick={() => setActiveTab('admin')} className={`w-18 h-14 rounded-xl flex flex-col items-center justify-center gap-1 transition-all border cursor-pointer ${activeTab === 'admin' ? 'bg-[#bc13fe]/15 border-[#bc13fe] text-white shadow-[0_0_10px_rgba(188,19,254,0.2)]' : 'border-transparent text-zinc-500 hover:text-zinc-300'}`}>
          {isAdminAuthenticated ? <Unlock size={16} className="text-[#00ff88]" /> : <Lock size={16} className="text-[#ff0055]" />}
          <span className="text-[7.5px] font-bold font-sans">ADMIN_SYS</span>
        </button>
      </aside>

      {/* ГЛАВНЫЙ ИНТЕРФЕЙСНЫЙ КОНТЕЙНЕР */}
      <div className="flex-1 flex flex-col overflow-hidden">

        {/* ХЕДЕР */}
        <header className="h-14 bg-[#09090d] border-b border-zinc-900 flex items-center justify-between px-6 z-20 shrink-0 relative">
          <span className="font-bold text-xs tracking-widest text-[#bc13fe] uppercase">
            WF_CORE // V5.0
          </span>
          <div className="text-[#FFD700] text-xs font-bold tracking-widest font-sans" style={{ textShadow: '0 0 12px rgba(255, 215, 0, 0.4)' }}>
            OMNIFACTORY রের PRO ARCHITECT // DESIGN BY BONDAREV_E
          </div>
        </header>

        {/* ДИНАМИЧЕСКИЕ ПАНЕЛИ */}
        <main className="flex-grow flex overflow-hidden relative bg-[#040407]">

          {/* 1. ЭКРАН INDEX (СЛОЖНЫЕ САЙТЫ И API) */}
          {activeTab === 'index' && (
            <div className="w-full flex-grow flex flex-col justify-between overflow-y-auto custom-scrollbar">
              <div className="p-8 space-y-8">
                <div className="h-44 border border-[#bc13fe]/30 rounded-xl bg-gradient-to-b from-[#14031d] to-[#050508] flex items-center justify-center relative overflow-hidden shadow-xl">
                  <h1 className="text-xl font-black tracking-[0.4em] text-white z-10 text-center">IDEA_TO_BIOROBOT_MORPH</h1>
                </div>
                <div className="space-y-2">
                  <h2 className="text-md font-bold uppercase tracking-wider text-white">Разработка веб-платформ и API любой сложности</h2>
                  <p className="text-xs text-zinc-400 font-sans leading-relaxed">Инженерные решения на базе асинхронных микросервисов FastAPI и интеллектуальных графов обмена.</p>
                </div>
              </div>

              {/* ПОДВАЛ ИНДЕКСА */}
              <div className="grid grid-cols-1 lg:grid-cols-2 h-64 border-t border-zinc-900 bg-black shrink-0">
                <div className="flex flex-col border-r border-zinc-900 h-full">
                  <div className="h-8 bg-[#09090e] border-b border-zinc-800 flex items-center px-4 text-[10px] font-bold text-zinc-400 gap-2"><TermIcon size={12} className="text-[#bc13fe]" /> // SYSTEM CONSOLE OUTPUT</div>
                  <div className="flex-grow p-4 overflow-y-auto font-mono text-xs text-zinc-400 space-y-1 bg-black custom-scrollbar flex flex-col-reverse">
                    {logs.map((log, i) => <div key={i} className="text-zinc-500 leading-relaxed pl-2 border-l border-zinc-800">{log}</div>)}
                  </div>
                </div>
                <div className="flex flex-col h-full bg-[#030305]">
                  <div className="h-8 bg-[#09090e] border-b border-zinc-800 flex items-center px-4 text-[10px] font-bold text-zinc-400">TELEGRAM_BOT_SIMULATOR</div>
                  <div className="flex-grow p-4 overflow-y-auto space-y-2 bg-[#050508] custom-scrollbar flex flex-col">
                    {tgMessages.map((msg, idx) => <div key={idx} className={`max-w-[85%] rounded-lg p-2 text-xs ${msg.sender === 'bot' ? 'bg-[#14141d] text-[#00ff41] self-start' : 'bg-[#bc13fe]/10 text-white self-end'}`}>{msg.text}</div>)}
                  </div>
                  <form onSubmit={handleSendTgMessage} className="p-2 bg-[#0a0a0f] border-t border-zinc-900 flex gap-2">
                    <input type="text" value={inputMsg} onChange={(e) => setInputMsg(e.target.value)} placeholder="Сообщение боту..." className="flex-1 bg-black border border-zinc-800 rounded px-3 py-1.5 text-xs outline-none text-zinc-200" />
                    <button type="submit" className="p-2 bg-[#bc13fe] text-black rounded cursor-pointer"><Send size={12} /></button>
                  </form>
                </div>
              </div>
            </div>
          )}

          {/* 2. ЭКРАН BUILDER */}
          {activeTab === 'builder' && (
            <div className="flex-grow flex overflow-hidden w-full h-full relative">
              <nav className="w-64 bg-[#020205] border-r border-zinc-900 p-4 flex flex-col gap-3 shrink-0">
                <div className="text-[10px] text-zinc-500 font-bold tracking-widest uppercase">// PALETTE_UNITS</div>
                <div className="flex-grow overflow-y-auto space-y-2 custom-scrollbar pr-1">
                  {registry.map((mod, idx) => (
                    <div key={`${mod.id}-${idx}`} draggable onDragStart={(e) => onDragStart(e, mod)} className="p-3 bg-zinc-900/60 border border-zinc-800 hover:border-[#bc13fe]/40 rounded cursor-grab">
                      <div className="text-xs font-bold text-zinc-200 uppercase">{mod.name}</div>
                      <div className="text-[8px] text-[#00f0ff] mt-0.5">{mod.cat}</div>
                    </div>
                  ))}
                </div>
                <div className="pt-4 border-t border-zinc-900 flex flex-col gap-2">
                  <button onClick={handleExportConfig} className="w-full py-2 bg-gradient-to-r from-[#15803d] to-[#166534] text-white text-xs font-bold rounded flex items-center justify-center gap-2 cursor-pointer"><Download size={13} /> DOWNLOAD JSON</button>
                  <button onClick={() => fileInputRef.current?.click()} className="w-full py-2 bg-zinc-900 border border-zinc-700 text-zinc-300 text-xs font-bold rounded flex items-center justify-center gap-2 cursor-pointer"><Upload size={13} /> UPLOAD CONFIG</button>
                </div>
              </nav>
              <div className="flex-grow h-full relative" onDragOver={onDragOver} onDrop={onDrop}>
                <ReactFlow nodes={nodes} edges={edges} onNodesChange={onNodesChange} onEdgesChange={onEdgesChange} onConnect={onConnect} nodeTypes={nodeTypes} fitView>
                  <Background color="#16161e" gap={24} size={1} variant="grid" />
                  <Controls className="!bg-zinc-900 !text-white !border-zinc-800" />
                </ReactFlow>
              </div>
            </div>
          )}

          {/* 3. ЭКРАН АДМИНКИ (ПОЛНАЯ РЕПЛИКА ИЗ IMAGE_48AD06.PNG С РОУТИНГОМ) */}
          {activeTab === 'admin' && (
            <div className="flex-1 w-full h-full relative">
              {!isAdminAuthenticated ? (
                /* НЕОНОВОЕ ОКНО АВТОРИЗАЦИИ В СТИЛЕ КИБЕРПАНК */
                <div className="absolute inset-0 bg-[#050508]/98 flex items-center justify-center p-4 z-50">
                  <div className={`w-full max-w-sm bg-[#0a0a0f] border ${pinError ? 'border-[#ff0055] shadow-[0_0_35px_rgba(255,0,85,0.3)]' : 'border-[#bc13fe]/30'} p-8 rounded-xl text-center space-y-4 relative`}>
                    <div className="absolute top-0 left-0 w-3 h-3 border-t-2 border-l-2 border-[#bc13fe]" />
                    <div className="absolute bottom-0 right-0 w-3 h-3 border-b-2 border-r-2 border-[#bc13fe]" />
                    <KeyRound size={22} className="text-[#bc13fe] mx-auto" />
                    <h2 className="text-xs font-bold text-white tracking-[0.2em] uppercase">ADMINISTRATIVE SUPERVISOR KEY</h2>
                    <form onSubmit={handleAdminAuth} className="space-y-4">
                      <input type="password" maxLength={4} value={pinCode} onChange={(e) => setPinCode(e.target.value.replace(/\D/g, ''))} placeholder="••••" className="w-full text-center tracking-[1.5em] text-lg font-bold bg-black border border-zinc-800 rounded-lg p-3 outline-none text-[#bc13fe]" autoFocus />
                      <button type="submit" className="w-full py-2 bg-[#bc13fe] text-black text-xs font-black uppercase rounded-md tracking-wider cursor-pointer">DECRYPT CONSOLE</button>
                    </form>
                  </div>
                </div>
              ) : (
                /* ОРИГИНАЛЬНЫЙ СУПЕРВИЗОР ИЗ СКРИНШОТА image_48ad06.png */
                <div className="w-full h-full flex overflow-hidden">

                  {/* Левый внутренний сайдбар админки (Контроль инфраструктуры...) */}
                  <div className="w-64 bg-[#0f0f12] border-r border-zinc-800 flex flex-col p-5 shrink-0 select-none">
                    <div className="flex items-center gap-2 mb-6 pl-2">
                      <svg width="20" height="20" viewBox="0 0 100 100" className="shadow-[0_0_8px_#bc13fe]">
                        <circle cx="50" cy="50" r="40" fill="none" stroke="#bc13fe" strokeWidth="8" strokeDasharray="10, 5"/>
                        <text x="35" y="65" fontFamily="Orbitron" fontSize="40" fontWeight="900" fill="#fff">M</text>
                      </svg>
                      <div className="text-[10px] font-bold text-white leading-tight">Managmant<br/><span className="text-[#00f0ff]">Factory</span></div>
                    </div>

                    <div className="border-b border-[#bc13fe]/10 pb-4 mb-4 pl-2">
                      <div className="text-sm font-black text-white tracking-wider">OmniFactory Evo</div>
                      <div className="text-[10px] font-bold text-[#ffff00] tracking-wider mt-1">powered design by BONDAREV_E</div>
                    </div>

                    {/* Разделы меню из image_48ad06.png */}
                    <div className="space-y-4 text-[10px]">
                      <div>
                        <div className="text-zinc-600 font-bold tracking-widest uppercase mb-1.5 pl-2">Контроль Инфраструктуры</div>
                        <div className="space-y-1">
                          <button onClick={() => setAdminSubTab('mainnode')} className={`w-full text-left py-2 px-3 rounded transition-colors flex items-center ${adminSubTab === 'mainnode' ? 'bg-[#1e1b4b] text-[#c084fc] border-l-2 border-[#bc13fe]' : 'text-zinc-400 hover:bg-zinc-900'}`}>🌐 [ Главный Узел ]</button>
                          <button onClick={() => setAdminSubTab('robotization')} className={`w-full text-left py-2 px-3 rounded transition-colors flex items-center ${adminSubTab === 'robotization' ? 'bg-[#1e1b4b] text-[#c084fc] border-l-2 border-[#bc13fe]' : 'text-zinc-400 hover:bg-zinc-900'}`}>🤖 [ Роботизация ]</button>
                        </div>
                      </div>

                      <div>
                        <div className="text-zinc-600 font-bold tracking-widest uppercase mb-1.5 pl-2">0 // Когнитивный Реестр</div>
                        <div className="space-y-1">
                          <button onClick={() => setAdminSubTab('modules')} className={`w-full text-left py-2 px-3 rounded transition-colors flex items-center ${adminSubTab === 'modules' ? 'bg-[#1e1b4b] text-[#c084fc] border-l-2 border-[#bc13fe]' : 'text-zinc-400 hover:bg-zinc-900'}`}>🧬 [ Реестр Модулей ]</button>
                        </div>
                      </div>
                    </div>

                    <button onClick={() => { setIsAdminAuthenticated(false); setPinCode(''); }} className="mt-auto w-full py-2 bg-zinc-900 border border-zinc-800 text-zinc-500 hover:text-[#ff0055] text-[10px] rounded transition-colors font-bold uppercase tracking-wider">
                      Lock Node Console
                    </button>
                  </div>

                  {/* Правая контентная область админки на базе выбранного под-раздела */}
                  <div className="flex-1 p-8 overflow-y-auto custom-scrollbar space-y-6 bg-[#040407]">

                    {adminSubTab === 'mainnode' && (
                      <div className="space-y-6 animate-fadeIn">
                        {/* Шапка из скриншота */}
                        <div className="border-b border-zinc-800 pb-4">
                          <h1 className="text-md font-bold text-white flex items-center gap-2">► Управление нодами и Оркестрация</h1>
                          <p className="text-[11px] text-zinc-500 mt-0.5 font-sans">Оркестрация трафика, управление внешними шлюзами авторизации и роутингом порталов.</p>
                        </div>

                        {/* Квадратная сетка KPI панелей из скриншота */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                          <div className="bg-[#141417] border border-zinc-800 p-5 rounded-xl relative border-l-2 border-[#bc13fe]">
                            <div className="text-[9px] text-zinc-500 font-bold uppercase tracking-wider">GLOBAL PORTAL UPSTREAM</div>
                            <div className="text-base font-bold font-sans text-white mt-1.5">OMNI_EVO_v7.7</div>
                            <div className="text-[10px] text-[#00ff41] mt-1 font-sans">STATUS: OPERATIONAL</div>
                          </div>
                          <div className="bg-[#141417] border border-zinc-800 p-5 rounded-xl relative border-l-2 border-[#bc13fe]">
                            <div className="text-[9px] text-zinc-500 font-bold uppercase tracking-wider">CONNECTED PORTALS</div>
                            <div className="text-base font-bold font-sans text-white mt-1.5">3 ПОРТАЛА</div>
                            <div className="text-[10px] text-[#00f0ff] mt-1 font-sans">WEB / ARCHITECT / BOT</div>
                          </div>
                          <div className="bg-[#141417] border border-zinc-800 p-5 rounded-xl relative border-l-2 border-[#bc13fe]">
                            <div className="text-[9px] text-zinc-500 font-bold uppercase tracking-wider">NETWORK IO STREAM</div>
                            <div className="text-base font-bold font-sans text-white mt-1.5">4.2 MB/s</div>
                            <div className="text-[10px] text-[#00ff41] mt-1 font-sans">PACKETS: 12.4k/s</div>
                          </div>
                        </div>

                        {/* Главная таблица состояния привязанных контуров из скриншота */}
                        <div className="bg-[#141417] border border-zinc-800 rounded-xl p-5 relative">
                          <div className="text-[11px] font-bold text-white uppercase tracking-wider mb-4 flex items-center gap-2">
                            <span className="text-[#bc13fe]">◈</span> Состояние привязанных цифровых контуров и веб-узлов экосистемы
                          </div>
                          <div className="overflow-x-auto">
                            <table className="w-full text-left text-xs font-sans">
                              <thead>
                                <tr className="border-b border-zinc-800 text-zinc-500 uppercase text-[10px]">
                                  <th className="pb-3 font-bold">Имя шлюза / Портала</th>
                                  <th className="pb-3 font-bold">Адрес маршрута</th>
                                  <th className="pb-3 font-bold">Контроль доступов</th>
                                  <th className="pb-3 font-bold">Трафик (In/Out)</th>
                                  <th className="pb-3 font-bold">Пинг</th>
                                  <th className="pb-3 font-bold">Статус</th>
                                  <th className="pb-3 font-bold text-right">Операции</th>
                                </tr>
                              </thead>
                              <tbody className="divide-y divide-zinc-900 text-zinc-300 font-mono text-[11px]">
                                <tr className="hover:bg-zinc-900/30">
                                  <td className="py-3.5 font-sans font-bold text-white">Основной веб-сайт (Frontend Node)</td>
                                  <td><code>/</code></td>
                                  <td className="font-sans text-zinc-400">Публичный контур</td>
                                  <td><code>142MB / 1.1GB</code></td>
                                  <td>1.2ms</td>
                                  <td><span className="inline-block w-2 h-2 rounded-full bg-[#22c55e] mr-1.5 shadow-[0_0_6px_#22c55e]" /> ONLINE</td>
                                  <td className="text-right"><button onClick={() => pushLog('SUCCESS', 'Перезагрузка ноды: frontend')} className="px-2 py-1 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-300 rounded font-sans text-[10px]">Reboot Node</button></td>
                                </tr>
                                <tr className="hover:bg-zinc-900/30">
                                  <td className="py-3.5 font-sans font-bold text-white">Робостроитель (Architect Engine Pro)</td>
                                  <td><code>/architect</code></td>
                                  <td className="font-sans text-zinc-400">Авторизованные инженеры</td>
                                  <td><code>45MB / 122MB</code></td>
                                  <td>0.8ms</td>
                                  <td><span className="inline-block w-2 h-2 rounded-full bg-[#22c55e] mr-1.5 shadow-[0_0_6px_#22c55e]" /> SECURE</td>
                                  <td className="text-right"><button onClick={() => pushLog('SUCCESS', 'Перезагрузка ноды: architect')} className="px-2 py-1 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-300 rounded font-sans text-[10px]">Reboot Node</button></td>
                                </tr>
                                <tr className="hover:bg-zinc-900/30">
                                  <td className="py-3.5 font-sans font-bold text-white">Контур автоматизации Telegram-ботов</td>
                                  <td><code>/api/builder/*</code></td>
                                  <td className="font-sans text-zinc-400">Администраторы модулей</td>
                                  <td><code>894MB / 3.4GB</code></td>
                                  <td>2.1ms</td>
                                  <td><span className="inline-block w-2 h-2 rounded-full bg-[#22c55e] mr-1.5 shadow-[0_0_6px_#22c55e]" /> MONITORING</td>
                                  <td className="text-right"><button onClick={() => pushLog('SUCCESS', 'Перезагрузка ноды: api_builder')} className="px-2 py-1 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-300 rounded font-sans text-[10px]">Reboot Node</button></td>
                                </tr>
                              </tbody>
                            </table>
                          </div>
                        </div>
                      </div>
                    )}

                    {adminSubTab === 'robotization' && (
                      <div className="space-y-4 animate-fadeIn">
                        <h2 className="text-sm font-bold text-[#00f0ff]">// РЕЕСТР WSL2 DOCKER POOLS</h2>
                        <div className="bg-[#141417] p-5 border border-zinc-800 rounded-xl text-xs text-zinc-400 leading-relaxed">
                          Мониторинг запущенных контейнеров компилятора Python/Flet изолирован на уровне хоста. Доступ к демону стабилен.
                        </div>
                      </div>
                    )}

                    {adminSubTab === 'modules' && (
                      <div className="space-y-4 animate-fadeIn">
                        <h2 className="text-sm font-bold text-[#bc13fe]">// КОГНИТИВНЫЙ РЕЕСТР СУЩНОСТЕЙ</h2>
                        <div className="bg-[#141417] p-5 border border-zinc-800 rounded-xl text-xs text-zinc-400 leading-relaxed">
                          База векторов ChromaDB активна. Загружено эмбеддингов личности: <span className="text-[#00ff41] font-bold">1,124,092</span>.
                        </div>
                      </div>
                    )}

                  </div>

                </div>
              )}
            </div>
          )}

        </main>
      </div>

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(3px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fadeIn { animation: fadeIn 0.2s ease-out forwards; }
      `}</style>
    </div>
  );
};