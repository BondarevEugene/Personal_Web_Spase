/* OmniFactory Graph Studio workspace density preference (layout only).
   Never stores bot tokens, scenario content, cookies or customer metadata. */
(()=>{"use strict";
 const button=document.getElementById("btn-workspace-density");
 const host=document.body;
 const help=document.getElementById("graph-workspace-help");
 if(!button||!host.classList.contains("builder-app"))return;
 function apply(compact){
  host.classList.toggle("graph-workspace-compact",compact);
  button.setAttribute("aria-pressed",String(compact));
  button.textContent=compact?"Рабочий режим":"Обзор возможностей";
  button.title=compact?"Показать описание и этапы конструктора":"Освободить место для схемы";
  if(help)help.textContent=compact
   ?"Рабочее пространство: схема и инспектор занимают больше места. Нажми «Рабочий режим», чтобы вернуть описание."
   :"Обзор возможностей: доступны описание конструктора и последовательность работы. Нажми «Обзор возможностей» для компактного режима.";
 }
 apply(true);
 button.addEventListener("click",()=>apply(!host.classList.contains("graph-workspace-compact")));
})();