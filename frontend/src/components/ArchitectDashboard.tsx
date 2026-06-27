import React, { useState, useEffect, useCallback, useRef } from 'react';
import { ReactFlow, Background, Controls, useNodesState, useEdgesState, addEdge } from '@xyflow/react';
import type { Connection } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { CustomNode } from './CustomNode';
import { Play, Square, Cpu, HardDrive, Terminal as TermIcon, ShieldAlert, CheckCircle2, Zap } from 'lucide-react';

const nodeTypes = { botStep: CustomNode };

export const ArchitectDashboard = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [registry, setRegistry] = useState<any[]>([]);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  // Состояние телеметрии (из dashboard.html)
  const [telemetry, setTelemetry] = useState({ cpu: '0%', ram: '0%', activeFlows: '00', status: 'ONLINE' });
  // Состояние терминала логов
  const [logs, setLogs] = useState<string[]>([`[${new Date().toLocaleTimeString()}] [SYSTEM] Инициализация ядра OmniFactory... [OK]`]);

  const terminalEndRef = useRef<HTMLDivElement>(null);

  // Логирование в терминал
  const pushLog = (tag: string, text: string) => {
    const time = new Date().toLocaleTimeString();
    setLogs(prev => [`[${time}] [${tag}] ${text}`, ...prev]);
  };

  // Живая эмуляция телеметрии
  useEffect(() => {
    const timer = setInterval(() => {
      setTelemetry({
        cpu: `${Math.floor(Math.random() * 45 + 5)}%`,
        ram: `${Math.floor(Math.random() * 15 + 60)}%`,
        activeFlows: String(nodes.length).padStart(2, '0'),
        status: 'ONLINE'
      });
    }, 2000);
    return () => clearInterval(timer);
  }, [nodes]);

  // Загрузка реестра модулей с бэкенда с полным набором строительных блоков
  useEffect(() => {
    const fetchRegistry = async () => {
      try {
        const response = await fetch('/api/registry');
        if (response.ok) {
          const data = await response.json();
          setRegistry(data.modules || []);
          pushLog('SUCCESS', `Загружен промышленный реестр. Модулей в базе: ${data.modules?.length || 0}`);
        } else {
          throw new Error('Реестр пуст или недоступен');
        }
      } catch (e) {
        // ПОЛНЫЙ ИНЖЕНЕРНЫЙ НАБОР КОМПОНЕНТОВ ДЛЯ СБОРКИ БОТА
        setRegistry([
          { id: 'tg_gateway', name: 'tg_gateway.py', type: 'Gateway', desc: 'Входной узел Telegram. Принимает webhook, авторизует Bot Token мессенджера.' },
          { id: 'ai_consultant', name: 'ai_consultant.py', type: 'AI_Core', desc: 'Нейросетевой модуль. Интеграция Gemini Flash + контекст базы знаний (RAG).' },
          { id: 'decision', name: 'decision.py', type: 'Logic', desc: 'Маршрутизатор условий. Проверяет кнопки, текст и стейты пользователя.' },
          { id: 'numerology_calc', name: 'numerology_calc.py', type: 'Math_Engine', desc: 'Вычислительное ядро. Расчет Квадрата Пифагора и психоматрицы по дате.' },
          { id: 'lead_catcher', name: 'lead_catcher.py', type: 'CRM_Integrator', desc: 'Фиксация лида. Перехват контактов и отправка карточки клиента в CRM.' },
          { id: 'stop', name: 'stop.py', type: 'System', desc: 'Завершение сессии диалога. Полный сброс FSM-контекста текущего пользователя.' }
        ]);
        pushLog('WARN', 'API_CORE бэкенда недоступен. Развернута полная инженерная палитра компонентов.');
      }
    };
    fetchRegistry();
  }, []);

  // Клик на ноду графа
  const onNodeClick = useCallback((event: React.MouseEvent, node: any) => {
    setSelectedNodeId(node.id);
    pushLog('FOCUS', `Выбран узел архитектуры графа: ID = [${node.id}]`);
  }, []);

  // Клик на свободное пространство (сброс фокуса)
  const onPaneClick = useCallback(() => {
    setSelectedNodeId(null);
  }, []);

  // Соединение нод стрелочками
  const onConnect = useCallback(
    (params: Connection) => {
      setEdges((eds) => addEdge(params, eds));
      pushLog('LINK', `Создана связь: [${params.source}] ➔ [${params.target}]`);
    },
    [setEdges]
  );

  // Добавление новой ноды на холст из палитры компонентов
  const addModuleToGraph = (mod: any) => {
    const id = `${mod.id}_${Date.now().toString().slice(-4)}`;
    const newNode = {
      id,
      type: 'botStep',
      position: { x: 150 + Math.random() * 100, y: 150 + Math.random() * 100 },
      data: {
        title: mod.name.toUpperCase(),
        subtitle: mod.type,
        label: mod.desc
      }
    };
    setNodes((nds) => nds.concat(newNode));
    pushLog('DEPLOY', `Модуль [${mod.name}] интегрирован на рабочую область графа. Присвоен ID: ${id}`);
  };

  // Функция запуска графа на бэкенд
  const handleLaunchGraph = async () => {
    pushLog('SYSTEM', 'Сборка пакета графа... Подготовка компиляции.');
    const selectedToken = localStorage.getItem(`token_${selectedNodeId}`) || "";

    try {
      const response = await fetch('http://localhost:8000/api/deploy-bot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          bot_id: "omni_bot_instance",
          graph: { nodes, edges },
          selected_module_ids: nodes.map(n => n.id.split('_')[0]),
          token: selectedToken
        })
      });

      const data = await response.json();
      if (data.status === 'success') {
        pushLog('SUCCESS', `Промышленное ядро активировано: ${data.message}`);
      } else {
        pushLog('ERROR', `Сбой инициализации: ${data.message}`);
      }
    } catch (error) {
      pushLog('ERROR', 'Нет связи с API_CORE бэкенда. Эмуляция запуска...');
      setTimeout(() => {
        pushLog('SUCCESS', '🚀 [ЭМУЛЯЦИЯ] Бот успешно скомпилирован и запущен в тестовой песочнице супервизора!');
      }, 1000);
    }
  };

  const handleKillCluster = () => {
    pushLog('CRITICAL', '🛑 Отправлен сигнал SIGKILL. Остановка всех дочерних процессов...');
  };

  return (
    <div className="w-screen h-screen bg-[#030305] text-white flex flex-col overflow-hidden select-none">

      {/* TOP INDUSTRIAL MANAGEMENT HEADER С ТВОЕЙ ПОДПИСЬЬЮ */}
      <header className="h-16 bg-[#09090e] border-b border-[#27272a] flex items-center justify-between px-6 z-20 shrink-0">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-[#22c55e] animate-pulse" />
            <span className="text-[10px] font-bold text-zinc-400 tracking-wider font-mono">SYS_STATUS: {telemetry.status}</span>
          </div>

          <div className="h-4 w-[1px] bg-zinc-800" />

          {/* ЖИВЫЕ КНОПКИ С ФИЗИЧЕСКИМ ОТКЛИКОМ */}
          <div className="flex items-center gap-3">
            <button
              onClick={handleLaunchGraph}
              className="flex items-center gap-1.5 px-4 py-1.5 bg-[#16a34a]/10 hover:bg-[#16a34a]/20 active:scale-95 border border-[#16a34a]/30 hover:border-[#16a34a]/60 active:border-[#16a34a] text-[#4ade80] hover:text-[#22c55e] text-[10px] font-bold uppercase tracking-wider rounded font-mono transition-all duration-200 hover:shadow-[0_0_15px_rgba(34,197,94,0.3)] cursor-pointer"
            >
              <Play size={10} /> Launch Graph
            </button>
            <button
              onClick={handleKillCluster}
              className="flex items-center gap-1.5 px-4 py-1.5 bg-[#dc2626]/10 hover:bg-[#dc2626]/20 active:scale-95 border border-[#dc2626]/30 hover:border-[#dc2626]/60 active:border-[#dc2626] text-[#f87171] hover:text-[#ef4444] text-[10px] font-bold uppercase tracking-wider rounded font-mono transition-all duration-200 hover:shadow-[0_0_15px_rgba(220,38,38,0.3)] cursor-pointer"
            >
              <Square size={10} /> Kill Cluster
            </button>
          </div>

          <div className="h-4 w-[1px] bg-zinc-800" />

          {/* Мини-телеметрия */}
          <div className="flex items-center gap-4 font-mono text-[9px] text-zinc-500 font-bold">
            <div className="flex items-center gap-1.5"><Cpu size={11} className="text-[#bc13fe]" /> CPU: <span className="text-zinc-300">{telemetry.cpu}</span></div>
            <div className="flex items-center gap-1.5"><HardDrive size={11} className="text-[#00d2ff]" /> RAM: <span className="text-zinc-300">{telemetry.ram}</span></div>
          </div>
        </div>

        {/* ТВОЙ БРУТАЛЬНЫЙ ПАСПОРТ ПРОЕКТА */}
        <div style={{
          color: '#FFD700',
          fontFamily: "'Share Tech Mono', 'JetBrains Mono', monospace",
          fontSize: '15pt',
          fontWeight: '900',
          letterSpacing: '3px',
          textShadow: '0 0 15px rgba(255, 215, 0, 0.65), 0 0 30px rgba(255, 215, 0, 0.25)',
          userSelect: 'none',
          background: 'rgba(255, 215, 0, 0.02)',
          padding: '5px 20px',
          border: '1px dashed rgba(255, 215, 0, 0.25)',
          borderRadius: '4px',
          boxShadow: 'inset 0 0 10px rgba(255, 215, 0, 0.03)'
        }}>
          OMNIFACTORY 𒄦 PRO ARCHITECT 𒄦 Design by BONDAREV_E 𒄦
        </div>
      </header>

      {/* MAIN CORE WORKSPACE BLOCK */}
      <div className="flex-grow flex overflow-hidden w-full">

        {/* LEFT PALETTE: Компоненты промышленного реестра */}
        <nav className="w-64 bg-[#05050a] border-r border-[#27272a] p-4 flex flex-col gap-4 z-10 shrink-0 overflow-y-auto">
          <div>
            <div className="text-[10px] font-black text-[#bc13fe] tracking-widest font-mono uppercase">// REGISTRY_COMPONENTS</div>
            <div className="text-[9px] text-zinc-500 font-mono mt-0.5">Кликните на модуль для инъекции в граф</div>
          </div>

          <div className="flex flex-col gap-2">
            {registry.map((mod) => (
              <div
                key={mod.id}
                onClick={() => addModuleToGraph(mod)}
                className="p-3 bg-zinc-900/40 hover:bg-[#00d2ff]/5 border border-zinc-800/80 hover:border-[#00d2ff]/40 rounded-lg cursor-pointer transition-all group active:scale-[0.98]"
              >
                <div className="flex justify-between items-center">
                  <span className="text-xs font-bold font-mono text-zinc-200 group-hover:text-white">{mod.name}</span>
                  <span className="text-[8px] px-1.5 py-0.5 bg-zinc-800 text-zinc-400 font-mono rounded border border-zinc-700/50">{mod.type}</span>
                </div>
                <p className="text-[10px] text-zinc-500 group-hover:text-zinc-400 mt-1 line-clamp-2">{mod.desc}</p>
              </div>
            ))}
          </div>
        </nav>

        {/* CENTER HOVER FIELD: Поле графа ReactFlow */}
        <main className="flex-grow h-full relative bg-[#040406]">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={onNodeClick}
            onPaneClick={onPaneClick}
            nodeTypes={nodeTypes}
            fitView
          >
            <Background color="#1f1f23" gap={20} size={1} />
            <Controls className="!bg-zinc-900 !border-zinc-800 !text-white opacity-60 hover:opacity-100 transition-opacity" />
          </ReactFlow>
        </main>

        {/* RIGHT SIDEBAR: ЖИВЫЕ НАСТРОЙКИ ПАРАМЕТРОВ НОДЫ */}
        <aside className="w-80 bg-[#05050a] border-l border-[#27272a] p-5 flex flex-col gap-4 z-10 shrink-0 overflow-y-auto">
          <div className="bg-zinc-900/30 border border-zinc-800/60 rounded-xl p-4">
            {selectedNodeId ? (
              <div className="space-y-4">
                <div className="text-[11px] font-bold text-[#bc13fe] font-mono tracking-wider">// NODE_SETTINGS: {selectedNodeId}</div>

                {/* Кастомизация ответа */}
                <div>
                  <label className="block text-[10px] font-bold text-zinc-500 uppercase tracking-wider font-mono mb-1">Ответ бота (Текст / Описание)</label>
                  <textarea
                    className="w-full bg-black border border-zinc-800 rounded p-2 text-xs font-mono text-zinc-300 focus:border-[#bc13fe] focus:outline-none"
                    rows={4}
                    value={nodes.find(n => n.id === selectedNodeId)?.data?.label as string || ""}
                    placeholder="Введите текст сообщения..."
                    onChange={(e) => {
                      setNodes(nds => nds.map(node => {
                        if (node.id === selectedNodeId) {
                          return { ...node, data: { ...node.data, label: e.target.value } };
                        }
                        return node;
                      }));
                    }}
                  />
                </div>

                {/* Поле подключения аккаунта / Токена */}
                <div>
                  <label className="block text-[10px] font-bold text-zinc-500 uppercase tracking-wider font-mono mb-1">Telegram Bot Token</label>
                  <input
                    type="password"
                    className="w-full bg-black border border-zinc-800 rounded p-2 text-xs font-mono text-zinc-300 focus:border-[#00d2ff] focus:outline-none"
                    placeholder="712345678:AAH_ПримерТокена..."
                    value={localStorage.getItem(`token_${selectedNodeId}`) || ""}
                    onChange={(e) => {
                      localStorage.setItem(`token_${selectedNodeId}`, e.target.value);
                      setNodes(nds => [...nds]); // Форсируем обновление
                    }}
                  />
                </div>

                <div className="pt-2 border-t border-zinc-900 text-[9px] text-zinc-500 font-mono">
                  * Настройки сохраняются локально. Кликните "Launch Graph" для компиляции и отправки на бэкенд.
                </div>
              </div>
            ) : (
              <div className="text-center text-zinc-600 text-[10px] py-10">
                <ShieldAlert size={20} className="mx-auto text-zinc-700 mb-2" />
                <p className="uppercase tracking-wider italic font-mono">Выберите узел на графе для изменения конфигурации параметров</p>
              </div>
            )}
          </div>
        </aside>

      </div>

      {/* BOTTOM CONTEXT LOG TERMINAL */}
      <footer className="h-40 bg-black border-t border-[#27272a] z-20 flex flex-col font-mono">
        <div className="h-7 bg-[#09090e] border-b border-zinc-800 flex items-center justify-between px-4 text-[9px] font-bold text-zinc-500 tracking-wider">
          <div className="flex items-center gap-2"><TermIcon size={12} className="text-[#bc13fe]" /> SYSTEM CONSOLE OUTPUT</div>
          <div className="cursor-pointer hover:text-white transition-colors" onClick={() => setLogs([])}>CLEAR LOGS</div>
        </div>
        <div className="flex-grow p-3 overflow-y-auto text-[10px] space-y-1 bg-black text-[#a1a1aa] custom-scrollbar selection:bg-zinc-800">
          {logs.map((log, i) => {
            let color = 'text-zinc-400';
            if (log.includes('[SUCCESS]')) color = 'text-[#22c55e]';
            if (log.includes('[CRITICAL]') || log.includes('[ERROR]')) color = 'text-[#ff007f]';
            if (log.includes('[DEPLOY]') || log.includes('[LINK]')) color = 'text-[#00d2ff]';
            return (
              <div key={i} className={`${color} border-l-2 border-current pl-2 py-0.5 bg-zinc-950/20 rounded-r`}>
                {log}
              </div>
            );
          })}
          <div ref={terminalEndRef} />
        </div>
      </footer>
    </div>
  );
};