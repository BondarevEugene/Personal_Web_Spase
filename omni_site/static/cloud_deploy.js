/* Managed Cloud foundation — no billable operations, no credentials in browser. */
(()=>{
"use strict";
const $=id=>document.getElementById(id), BASE="/api/v1/cloud";
let lastPlan=null;
function spec(){
 return {name:$('cloud-name').value.trim(),runtime:$('cloud-runtime').value,
  mode:$('cloud-mode').value,provider:$('cloud-provider').value,
  transport:$('cloud-transport').value,version:$('cloud-version').value.trim(),
  max_monthly_usd:Number($('cloud-budget').value),
  secret_refs:[],workflow_id:null};
}
function status(message,error=false){
 $('cloud-status').textContent=message;
 $('cloud-status').style.color=error?'#ffc1c1':'#b1eedf';
}
async function api(url,options={}){
 const response=await fetch(url,{credentials:'same-origin',cache:'no-store',...options});
 if(!response.ok){
  const body=await response.json().catch(()=>({}));
  const detail=Array.isArray(body.detail)?body.detail.map(x=>x.msg).join(', '):body.detail;
  throw Error(typeof detail==='string'?detail:'HTTP '+response.status);
 }
 return response.json();
}
function showPlan(plan){
 lastPlan=plan;
 const lines=[
  'СТАТУС: '+plan.state.toUpperCase(),
  'Режим: '+plan.spec.mode,
  'Провайдер: '+plan.spec.provider,
  'Runtime: '+plan.spec.runtime+' / '+plan.spec.version,
  'Контрольная сумма: '+plan.manifest_sha256,
  'Предел бюджета: $'+plan.spec.max_monthly_usd+'/мес. (НЕ прогноз)',
  '',
  'ШАГИ:',
  ...plan.steps.map((s,i)=>String(i+1).padStart(2,'0')+'. '+s),
  '',
  'ОГРАНИЧЕНИЯ:',
  ...plan.warnings.map(w=>'• '+w)
 ];
 $('cloud-result').textContent=lines.join('\n');
}
async function preview(){
 try{
  const data=await api(BASE+'/preview',{method:'POST',
    headers:{'Content-Type':'application/json'},body:JSON.stringify({spec:spec()})});
  showPlan(data);status('План проверен. Никаких ресурсов не создано.');
 }catch(err){lastPlan=null;status('Ошибка проверки: '+err.message,true);}
}
async function csrf(){
 const r=await api('/api/v1/builder/projects/csrf');
 return r.csrf_token;
}
async function save(){
 try{
  const data=await api(BASE+'/preview',{method:'POST',
   headers:{'Content-Type':'application/json'},body:JSON.stringify({spec:spec()})});
  showPlan(data);
  if(!window.confirm('Сохранить план без создания ресурсов Railway?'))return;
  const token=await csrf();
  // A unique key per deliberate creation; duplicate-clicks within the page
  // share the same key until the configuration is changed.
  const key='plan-'+data.manifest_sha256.slice(0,50);
  const saved=await api(BASE+'/plans',{method:'POST',
   headers:{'Content-Type':'application/json','X-Omni-CSRF':token,
    'Idempotency-Key':key},body:JSON.stringify({spec:data.spec})});
  status('Сохранён план '+saved.id+'. Статус: '+saved.status);
  void list();
 }catch(err){status('Ошибка сохранения: '+err.message,true);}
}
async function list(){
 try{
  const data=await api(BASE+'/plans');
  const root=$('cloud-plans');root.replaceChildren();
  if(!data.plans.length){root.textContent='Сохранённых планов нет.';return;}
  for(const plan of data.plans){
   const row=document.createElement('p');
   row.textContent=plan.name+' · '+plan.provider+' · '+plan.mode+' · '+plan.status;
   root.append(row);
  }
 }catch(err){$('cloud-plans').textContent='Авторизуйся для просмотра сохранённых планов.';}
}
function transportLock(){
 const automation=$('cloud-runtime').value==='automation';
 if(automation)$('cloud-transport').value='webhook';
 $('cloud-transport').querySelector('option[value="worker"]').disabled=automation;
 lastPlan=null;
}
$('cloud-runtime').addEventListener('change',transportLock);
for(const id of ['cloud-name','cloud-runtime','cloud-mode','cloud-provider',
                 'cloud-transport','cloud-version','cloud-budget']){
 $(id).addEventListener('change',()=>{lastPlan=null;status('Конфигурация изменена. Проверь план ещё раз.');});
}
$('cloud-preview').addEventListener('click',preview);
$('cloud-save').addEventListener('click',save);
transportLock();void list();
})();