/* OmniFactory Simple Telegram Builder — dependency-free editor. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const API = '/api/v1/builder/simple';
  const STORE = 'omnifactory:telegram-builder:v1';
  const LABEL = {message:'Сообщение', choice:'Кнопки', photo:'Фото', document:'Документ', end:'Завершение'};
  const sample = () => ({
    name:'Мой Telegram-бот', start:'welcome',
    nodes:[
      {id:'welcome',kind:'message',text:'Добро пожаловать! 👋',next:'question',media:null,options:[]},
      {id:'question',kind:'choice',text:'Чем могу помочь?',next:null,media:null,options:[
        {label:'О проекте',target:'about'}, {label:'Завершить',target:'finish'}]},
      {id:'about',kind:'message',text:'Это мой первый Telegram-бот.',next:'finish',media:null,options:[]},
      {id:'finish',kind:'end',text:'До встречи!',next:null,media:null,options:[]}
    ]
  });
  let project = sample();
  let active = project.start;
  let newId = 1;
  let dragging = null;

  function element(tag, text, className) {
    const n = document.createElement(tag);
    if (text !== null && text !== undefined) n.textContent = String(text);
    if (className) n.className = className;
    return n;
  }
  function button(text, className, action) {
    const b = element('button', text, className);
    b.type = 'button';
    b.addEventListener('click', action);
    return b;
  }
  function status(message, isError=false) {
    $('project-status').textContent = message;
    $('project-status').classList.toggle('error', isError);
  }
  function payload() {
    return {name:project.name, start:project.start,
      nodes:project.nodes.map(n => ({id:n.id,kind:n.kind,text:n.text||'',
        next:n.next||null,media:n.media||null,options:(n.options||[]).map(o=>({...o}))}))};
  }
  function persist() {
    try { localStorage.setItem(STORE, JSON.stringify(payload())); }
    catch (_err) { status('Локальное сохранение недоступно. Скачай сценарий в JSON.', true); }
  }
  function validShape(obj) {
    const kinds = Object.keys(LABEL);
    if (!obj || typeof obj.name!=='string'||!Array.isArray(obj.nodes)||obj.nodes.length<1||obj.nodes.length>80||
        typeof obj.start!=='string') return false;
    const ids = new Set();
    for (const n of obj.nodes) {
      if(!n || typeof n.id!=='string'||!(/^[A-Za-z][A-Za-z0-9_-]{0,39}$/).test(n.id)||
        ids.has(n.id)||!kinds.includes(n.kind)||typeof n.text!=='string'||
        (n.next!==null&&n.next!==undefined&&typeof n.next!=='string')||
        (n.media!==null&&n.media!==undefined&&typeof n.media!=='string')||
        !Array.isArray(n.options)||n.options.length>8) return false;
      ids.add(n.id);
    }
    return ids.has(obj.start);
  }
  const selected = () => project.nodes.find(n=>n.id===active);
  function update(newValue, renderInspector=false) {
    project = newValue;
    if(!project.nodes.some(n=>n.id===active))active=project.start;
    $('scenario-name').value=project.name;
    draw();
    if(renderInspector) inspect();
    persist();
  }
  function draw() {
    const root=$('flow-canvas');
    root.replaceChildren();
    $('node-count').textContent=project.nodes.length+' блоков';
    for(const n of project.nodes) {
      const card=element('button',null,'builder-node'+(n.id===active?' selected':''));
      card.type='button';
      card.draggable=true;
      card.dataset.nodeId=n.id;
      card.setAttribute('aria-label',(n.id===project.start?'Стартовый блок. ':'')+LABEL[n.kind]+': '+n.id);
      const header=element('div',null,'builder-node-head');
      header.append(element('span',n.id===project.start?'● СТАРТ':'БЛОК / '+n.id),element('strong',LABEL[n.kind]));
      card.append(header,element('div',n.kind==='end'?'Конец сценария':(n.text||n.media||'(текст не задан)'),'builder-node-text'));
      if(n.kind==='choice') {
        const target=element('div',(n.options||[]).map(o=>o.label+' → '+o.target).join('\n'),'builder-node-edge');
        card.append(target);
      } else if(n.next && n.kind!=='end') card.append(element('div','Переход → '+n.next,'builder-node-edge'));
      card.addEventListener('click',()=>{active=n.id;draw();inspect();});
      card.addEventListener('dragstart',e=>{
        dragging=n.id;e.dataTransfer.setData('text/plain','node:'+n.id);e.dataTransfer.effectAllowed='move';
      });
      card.addEventListener('dragover',e=>e.preventDefault());
      card.addEventListener('drop',e=>{
        e.preventDefault();e.stopPropagation();
        const val=e.dataTransfer.getData('text/plain');
        if(val.startsWith('kind:'))addNode(val.slice(5),n.id);
        else if(val.startsWith('node:'))reorder(val.slice(5),n.id);
      });
      root.append(card);
    }
  }
  function reorder(sourceId,beforeId) {
    if(sourceId===beforeId)return;
    const i=project.nodes.findIndex(n=>n.id===sourceId), j=project.nodes.findIndex(n=>n.id===beforeId);
    if(i<0||j<0)return;
    const node=project.nodes.splice(i,1)[0];
    project.nodes.splice(project.nodes.findIndex(n=>n.id===beforeId),0,node);
    update(project);
  }
  function addNode(kind,beforeId=null) {
    if(!LABEL[kind])return;
    if(project.nodes.length>=80){status('Максимум 80 блоков',true);return;}
    let id;
    do{id='block'+newId++;}while(project.nodes.some(n=>n.id===id));
    const finish=project.nodes.find(n=>n.kind==='end');
    const node={id,kind,text:kind==='message'?'Новое сообщение':kind==='choice'?'Выберите вариант':'',
      next:null,media:null,options:kind==='choice'?[{label:'Продолжить',target:finish?.id||project.start}]:[]};
    const idx=project.nodes.findIndex(n=>n.id===beforeId);
    project.nodes.splice(idx<0?project.nodes.length:idx,0,node);
    active=id;update(project,true);status('Блок '+id+' добавлен. Настрой его параметры справа.');
  }

  function field(parent,label,value,onChange,multiline=false) {
    const wrap=element('label',null,'inspector-field');
    wrap.append(element('span',label));
    const inp=element(multiline?'textarea':'input');
    if(!multiline) inp.type='text';
    inp.value=value??'';
    inp.addEventListener('input',()=>onChange(inp.value));
    wrap.append(inp);parent.append(wrap);
    return inp;
  }
  function selectField(parent,label,value,options,onChange) {
    const wrap=element('label',null,'inspector-field');
    wrap.append(element('span',label));
    const sel=element('select');
    for(const [val,txt] of options) {
      const opt=element('option',txt);opt.value=val;
      if(val===value)opt.selected=true;
      sel.append(opt);
    }
    sel.addEventListener('change',()=>onChange(sel.value));
    wrap.append(sel);parent.append(wrap);
  }
  function targetOptions(except=null) {
    return [['','— Завершить цепочку —'],...project.nodes.filter(n=>n.id!==except).map(n=>[n.id,n.id+' · '+LABEL[n.kind]])];
  }
  function inspect() {
    const root=$('editor-inspector');root.replaceChildren();
    const n=selected();
    if(!n){root.append(element('p','Выбери блок для настройки.'));return;}
    root.append(element('h3',LABEL[n.kind]+' · '+n.id));
    const actions=element('div',null,'inspector-actions');
    actions.append(button(n.id===project.start?'● Стартовый блок':'Сделать стартовым','inspector-btn',()=>{
      project.start=n.id;update(project,true);
    }));
    actions.append(button('Удалить блок','inspector-btn danger',()=>{
      if(project.nodes.length===1){status('Нельзя удалить последний блок.',true);return;}
      project.nodes=project.nodes.filter(x=>x.id!==n.id);
      for(const other of project.nodes){
        if(other.next===n.id)other.next=null;
        other.options=(other.options||[]).filter(o=>o.target!==n.id);
      }
      if(project.start===n.id)project.start=project.nodes[0].id;
      active=project.start;update(project,true);status('Блок удалён; проверь переходы.');
    }));
    root.append(actions);
    if(n.kind==='message'||n.kind==='choice'||n.kind==='end'){
      field(root,n.kind==='choice'?'Вопрос':'Текст',n.text,v=>{
        n.text=v;draw();persist();
      },true);
    }else{
      field(root,'Подпись (необязательно)',n.text,v=>{n.text=v;draw();persist();},true);
      field(root,'HTTPS URL или Telegram file_id',n.media||'',v=>{n.media=v;draw();persist();});
    }
    if(n.kind==='choice'){
      root.append(element('p','Каждая кнопка ведёт в указанный блок.','builder-tip'));
      (n.options||[]).forEach((opt,i)=>{
        const box=element('div',null,'option-edit');
        field(box,'Кнопка '+(i+1),opt.label,v=>{opt.label=v;draw();persist();});
        selectField(box,'Переход к блоку',opt.target,project.nodes.map(x=>[x.id,x.id+' · '+LABEL[x.kind]]),v=>{opt.target=v;draw();persist();});
        box.append(button('Удалить кнопку','inspector-btn danger',()=>{
          n.options.splice(i,1);update(project,true);
        }));
        root.append(box);
      });
      root.append(button('+ Добавить кнопку','inspector-btn',()=>{
        if(n.options.length>=8){status('Максимум 8 кнопок в блоке',true);return;}
        n.options.push({label:'Новая кнопка',target:project.nodes.find(x=>x.kind==='end')?.id||project.start});
        update(project,true);
      }));
    }else if(n.kind!=='end'){
      selectField(root,'После этого блока',n.next||'',targetOptions(n.id),v=>{
        n.next=v||null;draw();persist();
      });
    }
  }
  async function post(path,body) {
    const response=await fetch(API+path,{method:'POST',
      headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    if(!response.ok){
      let detail='HTTP '+response.status;
      try{
        const body=await response.json();
        if(typeof body.detail==='string')detail=body.detail;
        else if(Array.isArray(body.detail))detail=body.detail.map(e=>e.msg).join('; ');
      }catch(_err){}
      throw Error(detail);
    }
    return response;
  }
  function saveBlob(blob,name) {
    const url=URL.createObjectURL(blob);
    const a=element('a');a.href=url;a.download=name;document.body.append(a);a.click();a.remove();
    setTimeout(()=>URL.revokeObjectURL(url),3000);
  }
  async function validate(silent=false) {
    const r=await post('/validate',payload());const d=await r.json();
    if(!silent)status('Проверено: '+d.nodes+' блоков, достижимо '+d.reachable+
      (d.warnings?.length?'. Предупреждения: '+d.warnings.join('; '):'. Ошибок нет.'));
    return d;
  }
  function preview(){
    const root=$('preview-messages');root.replaceChildren();
    const nodes=new Map(project.nodes.map(n=>[n.id,n]));
    function bubble(txt){root.append(element('div',txt,'preview-bubble'));root.scrollTop=root.scrollHeight;}
    function follow(id){
      let steps=0;
      while(id && steps++<40){
        const n=nodes.get(id);
        if(!n){bubble('Ошибка: блок '+id+' не найден.');return;}
        if(n.kind==='choice'){
          bubble(n.text);
          for(const option of n.options){
            const b=button(option.label+' ↗','preview-button',()=>{
              for(const existing of [...root.querySelectorAll('.preview-button')])existing.remove();
              follow(option.target);
            });
            root.append(b);
          }
          return;
        }
        if(n.kind==='message')bubble(n.text);
        if(n.kind==='photo'||n.kind==='document')bubble((n.kind==='photo'?'[Фото] ':'[Документ] ')+(n.media||'нет адреса')+'\n'+(n.text||''));
        if(n.kind==='end'){if(n.text)bubble(n.text);return;}
        id=n.next;
      }
      if(steps>=40)bubble('Автоматический цикл превышает 40 переходов. Проверь связи.');
    }
    follow(project.start);
  }

  for(const b of document.querySelectorAll('[data-add]')){
    const kind=b.dataset.add;
    b.addEventListener('click',()=>addNode(kind));
    b.addEventListener('dragstart',e=>e.dataTransfer.setData('text/plain','kind:'+kind));
  }
  $('flow-canvas').addEventListener('dragover',e=>e.preventDefault());
  $('flow-canvas').addEventListener('drop',e=>{
    if(e.target.closest('.builder-node'))return;
    e.preventDefault();
    const val=e.dataTransfer.getData('text/plain');
    if(val.startsWith('kind:'))addNode(val.slice(5));
    else if(val.startsWith('node:'))reorder(val.slice(5),project.nodes.at(-1)?.id);
  });
  $('scenario-name').addEventListener('input',e=>{project.name=e.target.value;persist();});
  $('btn-save').addEventListener('click',()=>{persist();status('Черновик сохранён в этом браузере.');});
  $('btn-validate').addEventListener('click',async()=>{
    status('Проверяем схему на сервере…');
    try{await validate();}
    catch(e){status('Ошибка проверки: '+e.message,true);}
  });
  $('btn-export').addEventListener('click',async()=>{
    const btn=$('btn-export');btn.disabled=true;status('Проверка и генерация Python-бота…');
    try{
      await validate(true);
      const res=await post('/export',payload());
      saveBlob(await res.blob(),'omnifactory_telegram_bot.zip');
      status('Экспорт готов. Распакуй ZIP и следуй README.md; токен на сервер не передаётся.');
    }catch(e){status('Экспорт не выполнен: '+e.message,true);}
    finally{btn.disabled=false;}
  });
  $('btn-download-json').addEventListener('click',()=>{
    saveBlob(new Blob([JSON.stringify(payload(),null,2)],{type:'application/json'}),'omnifactory_scenario.json');
    status('JSON скачан.');
  });
  $('btn-import').addEventListener('click',()=>$('import-file').click());
  $('import-file').addEventListener('change',async e=>{
    const f=e.target.files?.[0];if(!f)return;
    if(f.size>120000){status('JSON слишком большой (максимум 120 КБ).',true);e.target.value='';return;}
    try{
      const obj=JSON.parse(await f.text());
      if(!validShape(obj))throw Error('неверная структура сценария');
      await post('/validate',obj);
      project={name:obj.name,start:obj.start,nodes:obj.nodes.map(n=>({
        id:n.id,kind:n.kind,text:n.text||'',next:n.next||null,media:n.media||null,
        options:(n.options||[]).map(o=>({label:o.label,target:o.target}))
      }))};
      active=project.start;update(project,true);status('Сценарий импортирован.');
    }catch(err){status('Ошибка импорта: '+err.message,true);}
    e.target.value='';
  });
  $('btn-preview').addEventListener('click',preview);

  try{
    const raw=localStorage.getItem(STORE);
    if(raw){
      const obj=JSON.parse(raw);
      if(validShape(obj))project=obj;
    }
  }catch(_err){}
  active=project.start;
  draw();inspect();
  $('scenario-name').value=project.name;
  status('Конструктор готов. Выбери блок или добавь новый. Экспорт проверяет схему на сервере.');
})();