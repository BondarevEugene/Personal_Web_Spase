(()=>{"use strict";
const q=id=>document.getElementById(id),base="/api/v1/cloud/releases";
let bot=null,preflight=null;
const element=(tag,txt,cls)=>{const e=document.createElement(tag);e.textContent=txt;if(cls)e.className=cls;return e;};
async function call(path,options={}){
 const r=await fetch(base+path,{cache:"no-store",credentials:"same-origin",...options});
 if(!r.ok){const body=await r.json().catch(()=>({}));throw Error(typeof body.detail==="string"?body.detail:"HTTP "+r.status);}
 return r.json();
}
async function csrf(){
 const r=await fetch("/api/v1/builder/projects/csrf",{credentials:"same-origin"});
 if(!r.ok)throw Error("Нужна авторизация");return (await r.json()).csrf_token;
}
function message(text){q("lab-release-results").replaceChildren(element("p",text,"lab-muted"));}
async function history(){
 const root=q("lab-release-history");root.replaceChildren();
 if(!bot)return;
 try{
  const items=(await call("/reviews")).reviews.filter(x=>x.bot_project_id===bot.id);
  if(!items.length){root.append(element("p","Запросов пока нет.","lab-muted"));return;}
  for(const item of items){
   const row=element("div","","lab-job");
   row.append(element("strong",item.status),element("small",new Date(item.created_at).toLocaleString("ru-RU")));
   const inspect=element("button","Актуальность","lab-small");inspect.type="button";
   inspect.addEventListener("click",async()=>{
    try{const detail=await call("/reviews/"+item.id);
      message(detail.still_valid?"Согласование ещё актуально. Платный деплой отключён.":"Согласование устарело или отозвано.");
    }catch(e){message("Ошибка: "+e.message);}
   });row.append(inspect);
   if(item.status==="review_requested"){
    const cancel=element("button","Отозвать","lab-small");cancel.type="button";
    cancel.addEventListener("click",async()=>{
     if(!confirm("Отозвать запрос на проверку релиза?"))return;
     try{await call("/reviews/"+item.id+"/cancel",{method:"POST",headers:{"X-Omni-CSRF":await csrf()}});await history();}
     catch(e){message("Ошибка: "+e.message);}
    });row.append(cancel);
   }
   root.append(row);
  }
 }catch(e){root.append(element("p","История недоступна: "+e.message,"lab-muted"));}
}
document.addEventListener("omni:bot-selection",event=>{
 bot=event.detail.bot;preflight=null;
 q("lab-release-panel").hidden=!bot;
 const select=q("lab-release-plan");select.replaceChildren();
 const blank=element("option","Выбери план размещения");blank.value="";select.append(blank);
 for(const plan of event.detail.plans){const option=element("option",plan.name+" · "+plan.mode);option.value=plan.id;select.append(option);}
 q("lab-release-request").disabled=true;
 message(bot?"Выбери план и проверь готовность к релизу.":"Выбери собственного бота.");
 void history();
});
q("lab-release-plan").addEventListener("change",()=>{
 preflight=null;q("lab-release-request").disabled=true;message("Проверь выбранный план заново.");
});
q("lab-release-check").addEventListener("click",async()=>{
 const plan=q("lab-release-plan").value;if(!bot||!plan){message("Выбери своего бота и план.");return;}
 const botId=bot.id;preflight=null;q("lab-release-request").disabled=true;
 try{
  const result=await call("/preflight/"+botId+"/"+plan);
  if(!bot||bot.id!==botId||q("lab-release-plan").value!==plan)return;
  preflight=result;
  const root=q("lab-release-results");root.replaceChildren();
  root.append(element("strong",result.ready_for_review?"Можно запросить рассмотрение":"Сначала исправь блокирующие условия","lab-release-summary"));
  for(const check of result.checks){
   const row=element("div","","lab-release-check "+(check.ok?"passed":"blocked"));
   row.append(element("b",check.ok?"✓":"!"),element("span",check.message));root.append(row);
  }
  root.append(element("p","Бюджет до $"+result.budget_cap_usd+" — это НЕ прогноз расходов и НЕ лимит Railway. Платный запуск запрещён.","lab-release-caution"));
  q("lab-release-request").disabled=!result.ready_for_review;
 }catch(e){message("Ошибка проверки: "+e.message);}
});
q("lab-release-request").addEventListener("click",async()=>{
 const plan=q("lab-release-plan").value;
 if(!bot||!plan||!preflight?.ready_for_review)return;
 if(!confirm("Запросить рассмотрение релиза без запуска Railway и без расходов?"))return;
 const botId=bot.id;
 try{
  const idempotency="release-"+botId+"-"+plan+"-"+preflight.plan_sha256.slice(0,12);
  await call("/reviews",{method:"POST",headers:{"Content-Type":"application/json",
   "X-Omni-CSRF":await csrf(),"Idempotency-Key":idempotency},
   body:JSON.stringify({bot_project_id:botId,cloud_plan_id:plan,confirmation:"REQUEST RELEASE REVIEW"})});
  preflight=null;q("lab-release-request").disabled=true;
  message("Запрос сохранён. Реальная публикация остаётся заблокированной.");
  if(bot&&bot.id===botId)await history();
 }catch(e){message("Ошибка запроса: "+e.message);}
});
})();