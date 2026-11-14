(()=>{"use strict";
const q=id=>document.getElementById(id);
let selectedBot=null;
const line=(label,good)=>{
 const row=document.createElement("div");row.className="lab-release-check "+(good?"passed":"blocked");
 const icon=document.createElement("b");icon.textContent=good?"✓":"!";
 const text=document.createElement("span");text.textContent=label;
 row.append(icon,text);return row;
};
document.addEventListener("omni:bot-selection",event=>{
 selectedBot=event.detail.bot;
 q("lab-runtime-panel").hidden=!selectedBot;
 q("lab-runtime-report").textContent=selectedBot?
   "Нажми «Проверить сценарий и runtime» для диагностики.":"Выбери своего бота.";
});
q("lab-runtime-check").addEventListener("click",async()=>{
 if(!selectedBot)return;
 const id=selectedBot.id,root=q("lab-runtime-report");
 root.replaceChildren();
 root.append(line("Проверка сохранённого сценария…",true));
 try{
  const res=await fetch("/api/v1/cloud/runtime/preflight/"+id,{
   credentials:"same-origin",cache:"no-store"
  });
  if(!res.ok)throw Error("HTTP "+res.status);
  const data=await res.json();
  if(!selectedBot||selectedBot.id!==id)return;
  root.replaceChildren();
  root.append(line(data.scenario_compatible?
    "Граф совместим с текущим runtime":
    "Граф требует исправления",data.scenario_compatible));
  root.append(line(data.image_digest_configured?
    "Образ runtime указан с SHA-256":
    "Не задан проверенный образ runtime",data.image_digest_configured));
  root.append(line("Webhook защищён секретным заголовком в runtime v1",true));
  root.append(line("Хранилище диалогов пока только в памяти (1 реплика)",false));
  root.append(line("Повторные Telegram updates не имеют durable deduplication",false));
  root.append(line("Реальная публикация и Telegram E2E не подтверждены",false));
  if(data.scenario_sha256){
   const hash=document.createElement("p");hash.className="lab-muted";
   hash.textContent="Отпечаток сценария: "+data.scenario_sha256;root.append(hash);
  }
 }catch(err){root.replaceChildren(line("Не удалось проверить runtime: "+err.message,false));}
});
})();