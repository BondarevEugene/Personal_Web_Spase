/* OMNIFACTORY Automation Studio — declarative graph UI; no eval or arbitrary code. */
(()=>{
'use strict';
const $=id=>document.getElementById(id);
const API='/api/v1/automation',SAVE='omnifactory:automation-studio:v1';
const SCENE={width:1950,height:1260};
const kindNames={trigger:'Trigger',set:'Переменная',condition:'IF / ELSE',transform:'Преобразование',
 http:'HTTP / REST',google_docs:'Google Docs',google_sheets:'Google Sheets',
 facebook_page:'Facebook Page',instagram:'Instagram',approval:'Согласование',end:'Завершение'};
const kindIcons={trigger:'◉',set:'≔',condition:'◇',transform:'↔',http:'⇄',
 google_docs:'▤',google_sheets:'▦',facebook_page:'f',instagram:'◎',approval:'⏸',end:'■'};
const defaults={
 trigger:{},set:{variable:'value',value:'{{customer}}'},condition:{variable:'value',operator:'equals',value:'Алексей'},
 transform:{variable:'value',operation:'strip'},http:{method:'GET',url:'https://api.example.com/path',save_as:'response'},
 google_docs:{action:'create',title:'Новый документ',credential:'OMNI_CREDENTIAL_GOOGLE',save_as:'document'},
 google_sheets:{action:'append',spreadsheet_id:'',range:'Sheet1!A1',rows:[['{{customer}}']],credential:'OMNI_CREDENTIAL_GOOGLE'},
 facebook_page:{action:'publish',page_id:'',message:'Привет!',credential:'OMNI_CREDENTIAL_FACEBOOK'},
 instagram:{action:'publish_image',account_id:'',image_url:'https://example.com/image.jpg',caption:'',
  credential:'OMNI_CREDENTIAL_INSTAGRAM'},approval:{},end:{}
};
const demo=()=>({name:'Обработка входящих заявок',start:'start',nodes:[
 {id:'start',kind:'trigger',next:'name',config:{}},
 {id:'name',kind:'set',next:'check',config:{variable:'value',value:'{{customer}}'}},
 {id:'check',kind:'condition',true_target:'vip',false_target:'normal',
  config:{variable:'value',operator:'equals',value:'Алексей'}},
 {id:'vip',kind:'set',next:'endvip',config:{variable:'segment',value:'VIP'}},
 {id:'normal',kind:'set',next:'endnormal',config:{variable:'segment',value:'Standard'}},
 {id:'endvip',kind:'end',config:{}},{id:'endnormal',kind:'end',config:{}}]});
const fresh=()=>({name:'Новая автоматизация',start:'start',nodes:[
 {id:'start',kind:'trigger',next:'finish',config:{}},
 {id:'finish',kind:'end',config:{}}]});
let workflow=demo(),selected='start',cloudId=null,revision=null,counter=1,pending=null;
let positions={};
const el=(tag,cls,txt)=>{const x=document.createElement(tag);if(cls)x.className=cls;if(txt!==undefined)x.textContent=txt;return x;};
const button=(label,callback,cls='auto-small-button')=>{const b=el('button',cls,label);b.type='button';b.addEventListener('click',callback);return b;};
const status=(text,bad=false)=>{const n=$('auto-status');n.textContent=text;n.classList.toggle('error',bad);};
function persist(){try{localStorage.setItem(SAVE,JSON.stringify({workflow,positions,cloudId,revision}));}catch(_){}}
function byId(id){return workflow.nodes.find(x=>x.id===id);}
function point(id,index=0){if(!positions[id])positions[id]={x:55+index%4*340,y:60+Math.floor(index/4)*245};return positions[id];}
function nodeId(){let id;do{id='node'+counter++;}while(byId(id));return id;}
function layoutReset(){positions={};cloudId=null;revision=null;selected=workflow.start;counter=1;pending=null;
 $('auto-name').value=workflow.name;$('auto-workflows').value='';render();inspector();persist();}
function newFlow(factory){
 if(!window.confirm('Создать новый граф? Текущий черновик сохранится в резерве браузера.'))return;
 try{localStorage.setItem(SAVE+':backup',JSON.stringify({workflow,positions,cloudId,revision}));}catch(_){}
 workflow=factory();layoutReset();status('Новая схема готова к настройке.');
}
function edges(){
 const svg=$('auto-svg');if(!svg)return;svg.replaceChildren();
 for(const n of workflow.nodes){
  const source=point(n.id),targets=n.kind==='condition'?
   [{id:n.true_target,i:0},{id:n.false_target,i:1}]:n.next?[{id:n.next,i:0}]:[];
  for(const dest of targets){
   if(!byId(dest.id))continue;
   const target=point(dest.id),x=source.x+262,y=source.y+103+dest.i*35,X=target.x,Y=target.y+53;
   const bend=Math.max(60,Math.abs(X-x)*.45);
   const path=document.createElementNS('http://www.w3.org/2000/svg','path');
   path.setAttribute('d',`M${x},${y} C${x+bend},${y} ${X-bend},${Y} ${X},${Y}`);
   path.setAttribute('class','auto-edge');svg.append(path);
  }
 }
}
function connect(target){
 if(!pending)return;
 const source=byId(pending.id);if(!source||!byId(target))return;
 if(source.kind==='condition'){
  if(pending.index===0)source.true_target=target;else source.false_target=target;
 }else if(source.kind!=='end')source.next=target;
 pending=null;render();inspector();persist();status('Связь создана.');
}
function render(){
 const canvas=$('auto-canvas');canvas.replaceChildren();
 const surface=el('div','auto-surface');surface.style.width=SCENE.width+'px';surface.style.height=SCENE.height+'px';
 const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.id='auto-svg';
 svg.setAttribute('width',SCENE.width);svg.setAttribute('height',SCENE.height);
 svg.setAttribute('viewBox',`0 0 ${SCENE.width} ${SCENE.height}`);surface.append(svg);
 $('auto-node-count').textContent=workflow.nodes.length+' узлов';
 workflow.nodes.forEach((n,i)=>{
  const p=point(n.id,i),card=el('section','auto-node kind-'+n.kind+(selected===n.id?' selected':''));
  card.style.left=p.x+'px';card.style.top=p.y+'px';
  card.dataset.node=n.id;
  const head=el('div','auto-node-head');
  head.append(el('span','',kindIcons[n.kind]+' '+n.id),el('strong','',kindNames[n.kind]));
  head.title='Перетащить блок';card.append(head);
  const input=button('',()=>pending?connect(n.id):status('Выбери выход первого блока.'),'auto-port auto-input');
  input.setAttribute('aria-label','Вход '+n.id);card.append(input);
  const detail=n.kind==='condition'?(n.config.variable||'')+' '+(n.config.operator||'equals')+' '+(n.config.value||''):
   n.kind==='set'?n.config.variable+' = '+String(n.config.value||''):
   n.kind==='http'?n.config.method+' '+(n.config.url||''):
   n.kind==='trigger'?'Начало запуска':
   n.kind==='end'?'Завершить процесс':kindNames[n.kind];
  card.append(el('p','auto-node-description',detail));
  const outs=n.kind==='condition'?[{label:'ДА',index:0},{label:'НЕТ',index:1}]:
   n.kind==='end'?[]:[{label:'ДАЛЕЕ',index:0}];
  for(const outgoing of outs){
   const row=el('div','auto-output-row',outgoing.label);
   const port=button('',()=>{
    pending={id:n.id,index:outgoing.index};
    status('Выход '+n.id+' выбран. Нажми вход целевого блока.');
   },'auto-port auto-output');
   port.style.top=(103+outgoing.index*35)+'px';
   port.setAttribute('aria-label','Выход '+outgoing.label+' '+n.id);
   row.append(port);card.append(row);
  }
  card.addEventListener('click',e=>{if(e.target.closest('.auto-port'))return;selected=n.id;render();inspector();});
  head.addEventListener('pointerdown',e=>{
   if(e.button!==0)return;
   e.preventDefault();head.setPointerCapture(e.pointerId);
   const sx=e.clientX,sy=e.clientY,ox=p.x,oy=p.y;
   const move=ev=>{p.x=Math.max(0,Math.min(SCENE.width-290,ox+ev.clientX-sx));
    p.y=Math.max(0,Math.min(SCENE.height-175,oy+ev.clientY-sy));
    card.style.left=p.x+'px';card.style.top=p.y+'px';edges();};
   const stop=()=>{head.removeEventListener('pointermove',move);
    head.removeEventListener('pointerup',stop);head.removeEventListener('pointercancel',stop);persist();};
   head.addEventListener('pointermove',move);head.addEventListener('pointerup',stop);
   head.addEventListener('pointercancel',stop);
  });
  surface.append(card);
 });
 canvas.append(surface);edges();
}
function addNode(kind){
 if(!defaults[kind]||workflow.nodes.length>=80)return status('Лимит 80 узлов.',true);
 if(kind==='trigger'&&workflow.nodes.some(n=>n.kind==='trigger'))
  return status('Триггер уже существует. Старт можно выбрать в инспекторе.',true);
 const id=nodeId(),last=byId(selected);
 const n={id,kind,config:structuredClone(defaults[kind])};
 if(kind==='condition'){n.true_target=null;n.false_target=null;}
 else if(kind!=='end')n.next=null;
 if(last&&last.kind!=='end'&&last.kind!=='condition'&&last.next&&kind!=='condition'){
  n.next=n.kind==='end'?undefined:last.next;
  last.next=id;
 }
 workflow.nodes.push(n);
 const p=point(selected);positions[id]={x:Math.min(p.x+330,SCENE.width-290),y:Math.min(p.y+75,SCENE.height-175)};
 selected=id;render();inspector();persist();status(kindNames[kind]+' добавлен. Настрой параметры справа.');
}
function removeSelected(){
 if(selected===workflow.start)return status('Сначала назначь другой стартовый блок.',true);
 if(workflow.nodes.length<=1)return;
 const id=selected;workflow.nodes=workflow.nodes.filter(x=>x.id!==id);
 for(const n of workflow.nodes){if(n.next===id)n.next=null;
  if(n.true_target===id)n.true_target=null;if(n.false_target===id)n.false_target=null;}
 delete positions[id];selected=workflow.start;render();inspector();persist();
 status('Блок удалён. Проверь связи.');
}
function control(parent,label,key,type='text',choices=null){
 const n=byId(selected);if(!n)return;
 const wrap=el('label','auto-inspector-field');wrap.append(el('span','',label));
 let ctrl;if(choices){ctrl=el('select');for(const [value,caption] of choices){
  const opt=el('option','',caption);opt.value=value;ctrl.append(opt);}
  ctrl.value=String(n.config[key]??choices[0][0]);
 }else if(type==='textarea'){ctrl=el('textarea');ctrl.rows=4;
  ctrl.value=typeof n.config[key]==='object'?JSON.stringify(n.config[key],null,2):String(n.config[key]||'');
 }else{ctrl=el('input');ctrl.type=type;ctrl.value=String(n.config[key]??'');}
 ctrl.addEventListener('change',()=>{
  try{
   n.config[key]=type==='textarea'&&['rows','body'].includes(key)?JSON.parse(ctrl.value):ctrl.value;
   persist();render();status('Параметр '+label+' обновлён.');
  }catch(err){status('Ожидается корректный JSON: '+err.message,true);}
 });
 wrap.append(ctrl);parent.append(wrap);
}
function inspector(){
 const root=$('auto-inspector-body');root.replaceChildren();
 const n=byId(selected);if(!n)return;
 root.append(el('h3','',kindNames[n.kind]+' / '+n.id));
 root.append(el('p','auto-muted','Изменения параметров сохраняются в черновике браузера.'));
 root.append(button('Назначить стартовым',()=>{workflow.start=n.id;persist();render();inspector();}));
 root.append(button('Удалить узел',removeSelected,'auto-small-button danger'));
 const choices=[['','Нет связи'],...workflow.nodes.map(n=>[n.id,n.id+' · '+kindNames[n.kind]])];
 function target(key,label){
  const wrap=el('label','auto-inspector-field');wrap.append(el('span','',label));
  const select=el('select');choices.forEach(([v,t])=>{
   const opt=el('option','',t);opt.value=v;select.append(opt);});
  select.value=n[key]||'';select.addEventListener('change',()=>{
   n[key]=select.value||null;persist();render();
  });wrap.append(select);root.append(wrap);
 }
 if(n.kind==='set'||n.kind==='condition'||n.kind==='transform')control(root,'Переменная','variable');
 if(n.kind==='set'||n.kind==='condition')control(root,'Значение, поддерживает {{variable}}','value','textarea');
 if(n.kind==='condition')control(root,'Оператор','operator','text',[
  ['equals','Равно'],['not_equals','Не равно'],['contains','Содержит'],
  ['not_empty','Не пусто'],['greater','Больше'],['less','Меньше']]);
 if(n.kind==='transform')control(root,'Операция','operation','text',[
  ['strip','Удалить пробелы'],['uppercase','Верхний регистр'],['lowercase','Нижний регистр']]);
 if(n.kind==='http'){
  control(root,'Метод','method','text',[['GET','GET'],['POST','POST']]);
  control(root,'HTTPS URL','url');control(root,'JSON-тело','body','textarea');
 }
 if(n.kind==='google_docs')control(root,'Заголовок документа','title');
 if(n.kind==='google_sheets'){
  control(root,'ID таблицы','spreadsheet_id');control(root,'Диапазон','range');
  control(root,'Строки в JSON','rows','textarea');
 }
 if(n.kind==='facebook_page'){
  control(root,'ID страницы','page_id');control(root,'Текст публикации','message','textarea');
 }
 if(n.kind==='instagram'){
  control(root,'ID Instagram Professional','account_id');control(root,'Ссылка на изображение','image_url');
  control(root,'Подпись','caption','textarea');
 }
 if(['http','google_docs','google_sheets','facebook_page','instagram'].includes(n.kind)){
  control(root,'Секрет оператора (имя, не токен)','credential');
  control(root,'Сохранить ответ в переменную','save_as');
  root.append(el('p','auto-muted','Не вводи секреты в параметры узла. Указывай только имя переменной окружения вида OMNI_CREDENTIAL_...'));
 }
 if(n.kind==='condition'){target('true_target','Если ДА / TRUE');target('false_target','Если НЕТ / FALSE');}
 else if(n.kind!=='end')target('next','Следующий шаг');
}
async function request(path,options={}){
 const response=await fetch(API+path,{credentials:'same-origin',cache:'no-store',...options});
 if(!response.ok){
  const body=await response.json().catch(()=>({}));
  throw Error(response.status===401?'Войди в аккаунт OmniFactory.':
   response.status===503?'Не применены миграции базы Automation.':
   typeof body.detail==='string'?body.detail:'HTTP '+response.status);
 }
 return response.status===204?null:response.json();
}
async function csrf(){
 const response=await fetch('/api/v1/builder/projects/csrf',{credentials:'same-origin'});
 if(!response.ok)throw Error('Для изменения нужен вход в аккаунт.');
 return (await response.json()).csrf_token;
}
async function listWorkflows(){
 try{
  const body=await request('/workflows'),select=$('auto-workflows');
  select.replaceChildren();const empty=el('option','','— Выбрать —');empty.value='';select.append(empty);
  for(const w of body.workflows){const op=el('option','',w.name+' · r'+w.revision);
   op.value=w.id;select.append(op);}
  select.value=cloudId||'';
  status('Сервер доступен: '+body.workflows.length+' сохранённых workflows.');
 }catch(err){status(err.message,true);}
}
async function saveWorkflow(){
 try{
  workflow.name=$('auto-name').value.trim();
  const token=await csrf();
  const response=await request(cloudId?'/workflows/'+cloudId:'/workflows',{
   method:cloudId?'PUT':'POST',
   headers:{'Content-Type':'application/json','X-Omni-CSRF':token},
   body:JSON.stringify({definition:workflow,revision})
  });
  cloudId=response.id;revision=response.revision;persist();
  await listWorkflows();void refreshSchedule();status('Сценарий сохранён: версия '+revision);
 }catch(err){status('Ошибка сохранения: '+err.message,true);}
}
async function loadWorkflow(){
 const id=$('auto-workflows').value;
 if(!id)return status('Выбери сценарий.',true);
 if(!window.confirm('Открыть выбранный сценарий? Черновик будет сохранён локально.'))return;
 try{
  localStorage.setItem(SAVE+':backup',JSON.stringify({workflow,positions,cloudId,revision}));
  const data=await request('/workflows/'+encodeURIComponent(id));
  workflow=data.definition;cloudId=data.id;revision=data.revision;
  selected=workflow.start;positions={};counter=1;
  $('auto-name').value=workflow.name;render();inspector();persist();
  status('Открыт сценарий '+workflow.name+' · версия '+revision);void loadRuns();void refreshSchedule();
 }catch(err){status('Не удалось открыть: '+err.message,true);}
}
async function analyzeWorkflow(){
 try{
  workflow.name=$('auto-name').value.trim();
  const response=await request('/analyze',{
   method:'POST',headers:{'Content-Type':'application/json'},
   body:JSON.stringify(workflow)
  });
  const root=$('auto-review');root.replaceChildren();
  root.append(el('strong','', 'Проверено '+response.nodes_reachable+' / '+response.nodes_total+' узлов'));
  for(const issue of response.warnings){
   root.append(el('p','auto-warning',issue.node+' · '+issue.message));
  }
  for(const recommendation of response.recommendations)
   root.append(el('p','auto-tip',recommendation));
  root.append(el('small','',response.limitations));
  status('Проверка схемы завершена. Это не проверка подключённых API.');
 }catch(err){status('Не удалось проверить граф: '+err.message,true);}
}
async function runWorkflow(){
 if(!cloudId)return status('Для серверного запуска сначала сохрани сценарий.',true);
 try{
  const inputs=JSON.parse($('auto-input').value||'{}');
  const result=await request('/workflows/'+cloudId+'/runs',{
   method:'POST',headers:{'Content-Type':'application/json','X-Omni-CSRF':await csrf()},
   body:JSON.stringify({input:inputs,live:false})
  });
  const root=$('auto-trace');root.replaceChildren();
  root.append(el('strong','auto-run-state','Статус: '+result.status+' · '+result.mode));
  for(const step of result.trace){const line=el('div','auto-trace-step');
   line.append(el('strong','',step.step?String(step.step).padStart(2,'0'):'—'),
               el('span','',step.node||'Лимит'),
               el('span','',step.kind||'engine'),
               el('em','',step.outcome||'ok'));root.append(line);}
  status('Run ID: '+result.id+' — журнал сохранён.');void loadRuns();
 }catch(err){status('Ошибка тестового запуска: '+err.message,true);}
}
async function loadRuns(){
 if(!cloudId)return;
 try{const rows=(await request('/workflows/'+cloudId+'/runs')).runs;
  const root=$('auto-runs');root.replaceChildren();
  for(const row of rows.slice(0,15))root.append(el('div','auto-history-row',
   row.status+' · '+row.mode+' · r'+row.revision+' · '+new Date(row.created_at).toLocaleString()));
  if(!rows.length)root.textContent='Запусков ещё нет.';
 }catch(err){status(err.message,true);}
}
async function refreshSchedule(){
 if(!cloudId)return;
 try{
  const response=await request('/workflows/'+cloudId+'/schedule');
  const row=response.schedule;
  if(row){
   $('auto-schedule-minutes').value=row.interval_minutes;
   $('auto-schedule-status').textContent=(row.enabled?'Активно':'Отключено')+
    ' · Следующий запуск '+new Date(row.next_run_at).toLocaleString()+
    ' · нужен запущенный scheduler worker';
  }else $('auto-schedule-status').textContent='Расписание не настроено. Выполнение только в dry-run.';
 }catch(err){$('auto-schedule-status').textContent=err.message;}
}
async function configureSchedule(){
 if(!cloudId)return status('Сначала сохрани workflow.',true);
 try{
  const minutes=Number($('auto-schedule-minutes').value);
  if(!Number.isInteger(minutes)||minutes<5||minutes>10080)
   return status('Интервал должен быть от 5 до 10080 минут.',true);
  const result=await request('/workflows/'+cloudId+'/schedule',{
   method:'PUT',headers:{'Content-Type':'application/json','X-Omni-CSRF':await csrf()},
   body:JSON.stringify({interval_minutes:minutes,enabled:true})
  });
  status('Расписание сохранено. Worker должен быть запущен отдельно; режим: '+result.mode);
  void refreshSchedule();
 }catch(err){status('Ошибка расписания: '+err.message,true);}
}
async function removeSchedule(){
 if(!cloudId)return;
 if(!window.confirm('Отключить расписание этого процесса?'))return;
 try{
  await request('/workflows/'+cloudId+'/schedule',{
   method:'DELETE',headers:{'X-Omni-CSRF':await csrf()}});
  status('Расписание отключено.');void refreshSchedule();
 }catch(err){status('Ошибка: '+err.message,true);}
}
async function webhook(){
 if(!cloudId)return status('Сначала сохрани workflow.',true);
 if(!window.confirm('Создать или заменить Webhook-токен? Прежний токен перестанет работать.'))return;
 try{
  const result=await request('/workflows/'+cloudId+'/webhook',{
   method:'POST',headers:{'X-Omni-CSRF':await csrf()}});
  const root=$('auto-webhook-info');root.hidden=false;root.replaceChildren();
  root.append(el('strong','','Webhook токен (показывается только сейчас)'));
  const token=el('code','',result.token);root.append(token);
  root.append(el('code','',result.url_path));
  root.append(el('p','','Передавай токен в X-Omni-Webhook-Token по HTTPS. Сейчас запускается только dry-run.'));
  status('Webhook активирован: токен сохранён на сервере только в виде SHA-256.');
 }catch(err){status(err.message,true);}
}
$('auto-new').addEventListener('click',()=>newFlow(fresh));
$('auto-demo').addEventListener('click',()=>newFlow(demo));
$('auto-save').addEventListener('click',saveWorkflow);
$('auto-load').addEventListener('click',loadWorkflow);
$('auto-analyze').addEventListener('click',analyzeWorkflow);
$('auto-run').addEventListener('click',runWorkflow);
$('auto-refresh-runs').addEventListener('click',loadRuns);
$('auto-webhook').addEventListener('click',webhook);
$('auto-schedule-save').addEventListener('click',configureSchedule);
$('auto-schedule-remove').addEventListener('click',removeSchedule);
$('auto-name').addEventListener('input',e=>{workflow.name=e.target.value;persist();});
document.querySelectorAll('[data-kind]').forEach(btn=>btn.addEventListener('click',()=>addNode(btn.dataset.kind)));
try{
 const saved=JSON.parse(localStorage.getItem(SAVE)||'null');
 if(saved?.workflow?.nodes?.length&&saved.workflow.nodes.length<=80){
  workflow=saved.workflow;cloudId=saved.cloudId||null;revision=saved.revision||null;
  for(const [id,p] of Object.entries(saved.positions||{}))
   if(workflow.nodes.some(n=>n.id===id)&&p&&Number.isFinite(p.x)&&Number.isFinite(p.y))
    positions[id]={x:p.x,y:p.y};
 }
}catch(_){}
selected=workflow.start;$('auto-name').value=workflow.name;render();inspector();
status('Локальный граф готов. Сохрани его в аккаунте для запуска на сервере.');
void listWorkflows();
})();