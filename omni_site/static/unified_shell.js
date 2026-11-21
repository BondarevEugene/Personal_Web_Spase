/* Enhancement only: no requests, storage, analytics or navigation interception. */
(function(){
  "use strict";
  document.addEventListener("DOMContentLoaded", function(){
    var rail=document.querySelector(".omni-section-rail");
    if(rail){
      var links=Array.prototype.slice.call(rail.querySelectorAll('a[href^="#"]'));
      var sections=links.map(function(a){return document.getElementById(a.getAttribute("href").slice(1));});
      if("IntersectionObserver" in window){
        var observer=new IntersectionObserver(function(entries){
          entries.forEach(function(entry){
            if(!entry.isIntersecting)return;
            links.forEach(function(link,i){
              if(sections[i]===entry.target){link.setAttribute("aria-current","location");}
              else{link.removeAttribute("aria-current");}
            });
          });
        },{rootMargin:"-15% 0px -65% 0px",threshold:0});
        sections.forEach(function(section){if(section)observer.observe(section);});
      }
      links.forEach(function(link){
        if(link.getAttribute("href")===window.location.hash)link.setAttribute("aria-current","location");
      });
    }
    var next=document.getElementById("omni-idea-next");
    var text=document.getElementById("omni-idea-text");
    if(next&&text){
      var ideas=[
        "Бот, который собирает заявки с сайта и создаёт задачи для команды.",
        "Ассистент, который напоминает клиенту о согласовании этапа проекта.",
        "Сценарий, который собирает обратную связь после завершённого заказа.",
        "Автоматизация, которая готовит сводку обращений для менеджера.",
        "Конструктор, который превращает повторяющиеся вопросы в сценарий поддержки."
      ];
      var n=0;
      next.addEventListener("click",function(){
        n=(n+1)%ideas.length;
        text.textContent=ideas[n];
      });
    }
  });
})();
