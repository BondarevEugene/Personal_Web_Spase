/* OmniFactory Graph Studio v2 — native browser canvas, no framework. */
(()=>{
'use strict';
const $=id=>document.getElementById(id), API='/api/v1/builder/simple';
const STORE='omnifactory:graph-studio:v2';
const integrationDetails={
 google_docs:'Google Docs: создание, чтение и изменение документов. Для подключения потребуется OAuth Google и серверный исполнитель.',
 google_sheets:'Google Sheets: чтение строк, добавление и обновление. Нужны OAuth и безопасное хранилище токенов.',
 facebook:'Facebook Pages: публикации и обработка комментариев через Meta Graph API. Требуются разрешения приложения и авторизация.',
 instagram:'Instagram Business: публикация медиа и комментарии через Instagram API. Требуется профессиональный аккаунт и авторизация Meta.',
 http:'HTTP / Webhook: исходящие REST-запросы и входящие события. До запуска необходимы SSRF-защита, ограничения адресов и хранение секретов.',
 python:'Python Handler: произвольная логика, но только в отдельной sandbox/worker-среде с ограничениями ресурсов.'
};
const sample=()=>({name:'Мой Telegram-бот',start:'welcome',nodes:[
{id:'welcome',kind:'message',text:'Добро пожаловать!',next:'question'},
{id:'question',kind:'choice',text:'Чем помочь?',options:[{label:'О нас',target:'about'},{label:'Завершить',target:'finish'}]},
{id:'about',kind:'message',text:'Мы создаём цифровые решения.',next:'finish'},
{id:'finish',kind:'end',text:'До встречи!'}]});
const names={message:'Сообщение',choice:'Кнопки / диалог',photo:'Фото',document:'Документ',end:'Финиш'};
let data=sample(),selected=data.start,positions={},zoom=1,link=null,counter=1;
let canvasExpanded=false;
function setExpanded(value){
 canvasExpanded=Boolean(value);
 document.body.classList.toggle('graph-fullscreen',canvasExpanded);
 const toggle=$('btn-expand-canvas');
 if(toggle){toggle.textContent=canvasExpanded?'Свернуть поле':'Развернуть поле';toggle.setAttribute('aria-pressed',String(canvasExpanded));}
}
function newNodeId(){
 let id;
 do{id='node'+counter++;}while(data.nodes.some(n=>n.id===id));
 return id;
}
function duplicateNode(id){
 const original=data.nodes.find(n=>n.id===id);
 if(!original||data.nodes.length>=80)return status('Не удалось скопировать: превышен лимит узлов.',true);
 const clone=JSON.parse(JSON.stringify(original));
 clone.id=newNodeId();
 // Duplicating should not silently create a shared branch or change start.
 if(clone.kind==='choice')clone.options=(clone.options||[]).map(o=>({...o}));
 data.nodes.push(clone);
 const p=position(id);
 positions[clone.id]={x:Math.min(world.width-300,p.x+65),y:Math.min(world.height-190,p.y+170)};
 selected=clone.id;change();inspector();status('Создана копия узла '+id+'.');
}
function removeNode(id){
 if(data.nodes.length<=1)return status('Нельзя удалить единственный узел.',true);
 data.nodes=data.nodes.filter(n=>n.id!==id);
 delete positions[id];
 for(const n of data.nodes){
  if(n.next===id)n.next=null;
  if(n.options)n.options=n.options.filter(o=>o.target!==id);
 }
 if(data.start===id)data.start=data.nodes[0].id;
 selected=data.start;link=null;change();inspector();status('Узел удалён. Проверь незамкнутые переходы.');
}
function contextMenu(e,id){
 e.preventDefault();e.stopPropagation();
 const m=$('graph-context-menu');
 if(!m)return;
 m.replaceChildren();selected=id;render();inspector();
 const n=data.nodes.find(x=>x.id===id);
 const actions=[
  ['Настроить узел',()=>{$('editor-inspector').scrollIntoView({block:'nearest',behavior:'smooth'});}],
  ['Дублировать узел',()=>duplicateNode(id)],
  ['Сделать стартовым',()=>{data.start=id;change();inspector();}],
  ['Удалить узел',()=>removeNode(id)]
 ];
 for(const [label,fn] of actions)m.append(btn(label,()=>{m.hidden=true;fn();},'context-action'+(label.startsWith('Удалить')?' danger':'')));
 m.hidden=false;
 m.style.left=Math.min(e.clientX,innerWidth-230)+'px';
 m.style.top=Math.min(e.clientY,innerHeight-195)+'px';
 m.setAttribute('aria-label','Действия с узлом '+n.id);
}

const world={width:2200,height:1400};
function decorateCard(card,n) {
 card.classList.add('node-kind-'+n.kind);
 card.dataset.kind=n.kind;
 const icon=el('span','graph-kind-icon',
  {message:'✉',choice:'◇',photo:'▧',document:'▤',end:'■'}[n.kind]||'●');
 card.prepend(icon);
}
const el=(tag,cls,txt)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(txt!==undefined)e.textContent=txt;return e;};
const btn=(txt,cb,cls='inspector-btn')=>{const e=el('button',cls,txt);e.type='button';e.addEventListener('click',cb);return e;};
const status=(msg,bad=false)=>{const n=$('project-status');n.textContent=msg;n.classList.toggle('error',bad);};
const save=()=>{try{localStorage.setItem(STORE,JSON.stringify({data,positions}));}catch(e){status('Локальное сохранение недоступно',true);}};
function position(id,index=0){if(!positions[id])positions[id]={x:80+(index%5)*335,y:90+Math.floor(index/5)*235};return positions[id];}
function payload(){return {name:data.name,start:data.start,nodes:data.nodes.map(({id,kind,text='',next=null,media=null,options=[]})=>({id,kind,text,next,media,options}))};}
function edges(){
 const svg=$('flow-edges');if(!svg)return;svg.replaceChildren();
 for(const n of data.nodes){const p=position(n.id),targets=n.kind==='choice'?(n.options||[]).map((o,i)=>({id:o.target,i})):n.next?[{id:n.next,i:0}]:[];
  for(const t of targets){if(!data.nodes.some(x=>x.id===t.id))continue;
   const q=position(t.id),x=p.x+278,y=p.y+114+t.i*43,X=q.x,Y=q.y+65,b=Math.max(70,Math.abs(X-x)*.48);
   const path=document.createElementNS('http://www.w3.org/2000/svg','path');
   path.setAttribute('d',`M${x} ${y} C${x+b} ${y} ${X-b} ${Y} ${X} ${Y}`);
   path.setAttribute('class','builder-wire');svg.append(path);
  }
 }
}
function connect(target){
 if(!link)return;
 const n=data.nodes.find(x=>x.id===link.id);if(!n)return;
 if(n.kind==='choice'){if(!n.options?.[link.i])return;n.options[link.i].target=target;}
 else if(n.kind!=='end')n.next=target;
 status('Соединено: '+n.id+' → '+target);link=null;render();save();
}
function render(){
 const root=$('flow-canvas');root.replaceChildren();
 const worldEl=el('div','flow-workspace');worldEl.id='flow-workspace';
 worldEl.style.width=world.width+'px';worldEl.style.height=world.height+'px';worldEl.style.zoom=zoom;
 const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.id='flow-edges';
 svg.setAttribute('viewBox',`0 0 ${world.width} ${world.height}`);
 svg.setAttribute('width',world.width);svg.setAttribute('height',world.height);worldEl.append(svg);
 $('node-count').textContent=data.nodes.length+' узлов';
 data.nodes.forEach((n,i)=>{
  const p=position(n.id,i),card=el('section','builder-node graph-node'+(selected===n.id?' selected':''));
  card.dataset.nodeId=n.id;decorateCard(card,n);card.style.left=p.x+'px';card.style.top=p.y+'px';
  card.addEventListener('contextmenu',e=>contextMenu(e,n.id));
  const head=el('div','builder-node-head graph-node-head');head.append(el('span','',n.id===data.start?'● START':n.id),el('strong','',names[n.kind]));
  head.title='Переместить узел';card.append(head);
  const input=btn('',()=>link?connect(n.id):status('Сначала выбери выход узла'),'graph-port node-input');
  input.setAttribute('aria-label','Вход '+n.id);card.append(input);
  card.append(el('div','builder-node-text',n.text||n.media||'(настрой содержимое)'));
  const opts=n.kind==='choice'?(n.options||[]):n.kind==='end'?[]:[{label:'Далее',target:n.next||'—'}];
  opts.forEach((o,j)=>{
   const row=el('div','graph-option');row.append(el('span','',o.label+' → '+(o.target||'—')));
   const output=btn('',()=>{link={id:n.id,i:j};status('Выход выбран. Нажми вход другого блока.');},'graph-port node-output');
   output.setAttribute('aria-label','Выход '+n.id+' '+o.label);output.style.top=(114+j*43)+'px';
   row.append(output);card.append(row);
  });
  card.addEventListener('click',event=>{if(event.target.closest('.graph-port'))return;selected=n.id;render();inspector();});
  head.addEventListener('pointerdown',event=>{
   if(event.button!==0)return;event.preventDefault();head.setPointerCapture(event.pointerId);
   const sx=event.clientX,sy=event.clientY,ox=p.x,oy=p.y;
   const move=e=>{p.x=Math.max(0,Math.min(world.width-300,ox+(e.clientX-sx)/zoom));
    p.y=Math.max(0,Math.min(world.height-200,oy+(e.clientY-sy)/zoom));
    card.style.left=p.x+'px';card.style.top=p.y+'px';edges();};
   const end=()=>{head.removeEventListener('pointermove',move);head.removeEventListener('pointerup',end);head.removeEventListener('pointercancel',end);save();};
   head.addEventListener('pointermove',move);head.addEventListener('pointerup',end);head.addEventListener('pointercancel',end);
  });
  worldEl.append(card);
 });
 root.append(worldEl);edges();
}
function change(){render();save();}
function field(parent,title,value,changeFn,textarea=false){
 const label=el('label','inspector-field'),input=el(textarea?'textarea':'input');
 label.append(el('span','',title));input.value=value??'';input.addEventListener('input',()=>changeFn(input.value));
 input.addEventListener('blur',()=>render());label.append(input);parent.append(label);
}
function selector(parent,title,value,options,handler){
 const label=el('label','inspector-field'),sel=el('select');label.append(el('span','',title));
 options.forEach(([v,t])=>{const op=el('option','',t);op.value=v;op.selected=v===value;sel.append(op);});
 sel.addEventListener('change',()=>handler(sel.value));label.append(sel);parent.append(label);
}
function inspector(){
 const root=$('editor-inspector');root.replaceChildren();const n=data.nodes.find(x=>x.id===selected);if(!n)return;
 root.append(el('h3','',names[n.kind]+' · '+n.id));
 root.append(btn('Сделать стартовым',()=>{data.start=n.id;change();inspector();}));
 root.append(btn('Дублировать',()=>duplicateNode(n.id)));
 root.append(btn('Удалить',()=>removeNode(n.id),'inspector-btn danger'));
 const details=el('div','inspector-meta');
 details.append(el('span','', 'ID: '+n.id),el('span','', 'ТИП: '+n.kind),el('span','',n.id===data.start?'● СТАРТОВЫЙ БЛОК':'Промежуточный блок'));
 root.append(details);
 field(root,n.kind==='photo'||n.kind==='document'?'Подпись':'Текст',n.text||'',v=>{n.text=v;save();},true);
 if(n.kind==='photo'||n.kind==='document')field(root,'HTTPS URL / Telegram file_id',n.media||'',v=>{n.media=v;save();});
 const targets=data.nodes.map(x=>[x.id,x.id+' · '+names[x.kind]]);
 if(n.kind==='choice'){
  (n.options||[]).forEach((o,i)=>{
   const card=el('div','option-edit');
   field(card,'Подпись кнопки',o.label,v=>{o.label=v;save();});
   selector(card,'Целевой узел',o.target,targets,v=>{o.target=v;change();});
   card.append(btn('Удалить кнопку',()=>{n.options.splice(i,1);change();inspector();},'inspector-btn danger'));
   root.append(card);
  });
  root.append(btn('+ Кнопка',()=>{
   n.options=n.options||[];if(n.options.length>=8)return status('Максимум 8 кнопок',true);
   n.options.push({label:'Кнопка',target:data.start});change();inspector();
  }));
 }else if(n.kind!=='end')selector(root,'Следующий узел',n.next||'',[['','Нет связи'],...targets],v=>{n.next=v||null;change();});
}
function add(kind,pos){
 if(!names[kind]||data.nodes.length>=80)return status('Лимит блоков достигнут',true);
 const id=newNodeId();
 const n={id,kind,text:kind==='message'?'Новое сообщение':kind==='choice'?'Выберите вариант':'',next:null,media:null,options:kind==='choice'?[{label:'Продолжить',target:data.start}]:[]};
 data.nodes.push(n);if(pos)positions[id]=pos;selected=id;change();inspector();status('Узел добавлен. Перетаскивай за заголовок, соединяй порты.');
}
async function post(path){
 const r=await fetch(API+path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload())});
 if(!r.ok){const d=await r.json().catch(()=>({}));throw Error(Array.isArray(d.detail)?d.detail.map(x=>x.msg).join('; '):d.detail||'HTTP '+r.status);}
 return r;
}
function download(blob,name){const a=el('a'),url=URL.createObjectURL(blob);a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),2000);}
function preview(){
 const root=$('preview-messages');root.replaceChildren();const map=new Map(data.nodes.map(n=>[n.id,n]));
 let steps=0;
 const trace=$('preview-trace');
 if(trace){trace.replaceChildren();trace.append(el('strong','', 'Трассировка выполнения (браузерная симуляция)'));}
 const log=n=>{
  steps++;
  if(trace)trace.append(el('div','preview-trace-line',steps+' · '+n.id+' / '+n.kind));
 };
 const bubble=t=>root.append(el('div','preview-bubble',t));
 function step(id){let loops=0;while(id&&loops++<40){const n=map.get(id);if(!n)return bubble('Блок не найден: '+id);
  log(n);
  if(n.kind==='choice'){bubble(n.text);n.options.forEach(o=>root.append(btn(o.label,()=>{root.querySelectorAll('.preview-button').forEach(x=>x.remove());step(o.target);},'preview-button')));return;}
  if(n.kind==='message'||n.kind==='end')bubble(n.text||'Конец');
  if(n.kind==='photo'||n.kind==='document')bubble('['+names[n.kind]+'] '+(n.media||''));
  if(n.kind==='end')return;id=n.next;
 }if(loops>=40)bubble('Обнаружен цикл.');}step(data.start);
}
document.addEventListener('pointerdown',e=>{
 const menu=$('graph-context-menu');
 if(menu&&!menu.hidden&&!menu.contains(e.target))menu.hidden=true;
});
document.addEventListener('keydown',e=>{
 if(e.key==='Escape'){$('graph-context-menu').hidden=true;if(canvasExpanded)setExpanded(false);}
 const typing=['INPUT','TEXTAREA','SELECT'].includes(document.activeElement?.tagName);
 if(!typing&&e.key==='Delete'&&selected)removeNode(selected);
});
$('btn-expand-canvas').addEventListener('click',()=>setExpanded(!canvasExpanded));
$('btn-test-canvas').addEventListener('click',()=>{
 preview();$('builder-preview').scrollIntoView({behavior:'smooth',block:'start'});
});
$('btn-export-info').addEventListener('click',()=>{
 const n=$('export-explainer');
 n.hidden=!n.hidden;
 if(!n.hidden)n.scrollIntoView({behavior:'smooth',block:'center'});
});
document.querySelectorAll('[data-integration]').forEach(b=>b.addEventListener('click',()=>{
 const code=b.dataset.integration,info=$('integration-information');
 info.replaceChildren();
 info.append(el('strong','',b.querySelector('strong')?.textContent||code));
 info.append(el('p','',integrationDetails[code]||'Пока недоступно.'));
 info.append(el('span','integration-tag','ПЛАНИРУЕТСЯ · ПОКА НЕ ИСПОЛНЯЕТСЯ'));
 info.hidden=false;
 status('Модуль '+code+' есть в каталоге, но пока недоступен в экспортируемом сценарии.');
}));
document.querySelectorAll('[data-add]').forEach(b=>{b.addEventListener('click',()=>add(b.dataset.add));
 b.addEventListener('dragstart',e=>{e.dataTransfer.setData('text/plain','kind:'+b.dataset.add);});});
$('flow-canvas').addEventListener('dragover',e=>e.preventDefault());
$('flow-canvas').addEventListener('drop',e=>{e.preventDefault();const value=e.dataTransfer.getData('text/plain');
 if(!value.startsWith('kind:'))return;const rect=$('flow-workspace').getBoundingClientRect();
 add(value.slice(5),{x:Math.max(0,(e.clientX-rect.left)/zoom),y:Math.max(0,(e.clientY-rect.top)/zoom)});});
$('scenario-name').addEventListener('input',e=>{data.name=e.target.value;save();});
$('btn-save').addEventListener('click',()=>{save();status('Черновик сохранён в этом браузере.');});
$('btn-validate').addEventListener('click',async()=>{try{const result=await(await post('/validate')).json();status('Проверено '+result.nodes+' узлов. '+result.warnings.join('; '));}catch(e){status(e.message,true);}});
$('btn-export').addEventListener('click',async()=>{try{await post('/validate');const r=await post('/export');download(await r.blob(),'omnifactory_bot.zip');status('Экспорт Python готов.');}catch(e){status(e.message,true);}});
$('btn-download-json').addEventListener('click',()=>download(new Blob([JSON.stringify(payload(),null,2)],{type:'application/json'}),'scenario.json'));
$('btn-import').addEventListener('click',()=>$('import-file').click());
$('import-file').addEventListener('change',async e=>{
 const file=e.target.files?.[0];if(!file)return;
 try{if(file.size>120000)throw Error('Файл превышает 120 КБ');
  const obj=JSON.parse(await file.text());
  const r=await fetch(API+'/validate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(obj)});
  if(!r.ok)throw Error('Схема не прошла серверную проверку');
  data=obj;positions={};selected=data.start;counter=1;change();inspector();$('scenario-name').value=data.name;status('Сценарий импортирован.');
 }catch(err){status('Ошибка импорта: '+err.message,true);}e.target.value='';
});
$('btn-preview').addEventListener('click',preview);
const controls=el('div','graph-controls');
const level=el('span','graph-zoom-label','100%');
function setZoom(v){zoom=Math.max(.5,Math.min(1.5,v));$('flow-workspace').style.zoom=zoom;level.textContent=Math.round(zoom*100)+'%';}
controls.append(btn('−',()=>setZoom(zoom-.15),'graph-zoom'),level,btn('+',()=>setZoom(zoom+.15),'graph-zoom'),btn('100%',()=>setZoom(1),'graph-zoom'));
$('flow-canvas').parentElement.querySelector('.builder-pane-head').append(controls);
try{const stored=JSON.parse(localStorage.getItem(STORE)||'null');if(stored?.data?.nodes?.length){data=stored.data;positions=stored.positions||{};}}catch(e){}
selected=data.start;$('scenario-name').value=data.name;render();inspector();status('Graph Studio готов: перемещай узлы и соединяй входы с выходами.');
})();