/* Graph Studio logical groups — organizational metadata only.
   Graph nodes/edges and exported Python runtime remain untouched. */
(function(root){
 "use strict";
 function clean(groups,nodes){
  var existing=new Set((nodes||[]).map(function(n){return n.id;}));
  var used=new Set(),ids=new Set(),result=[];
  for(var g of Array.isArray(groups)?groups:[]){
   if(!g||typeof g.id!=="string"||!/^group[0-9]{1,6}$/.test(g.id)||
      ids.has(g.id)||typeof g.title!=="string")continue;
   var title=g.title.trim().slice(0,60);
   if(title.length<2)continue;
   var members=[];
   for(var id of Array.isArray(g.node_ids)?g.node_ids:[]){
    if(existing.has(id)&&!used.has(id)){
     used.add(id);members.push(id);
    }
   }
   if(!members.length)continue;
   ids.add(g.id);result.push({id:g.id,title:title,node_ids:members});
   if(result.length>=20)break;
  }
  return result;
 }
 function nextId(groups){
  var used=new Set(groups.map(function(g){return g.id;}));
  for(var i=1;i<=999999;i++){var id="group"+i;if(!used.has(id))return id;}
  throw Error("Лимит идентификаторов групп");
 }
 function create(groups,nodes,title,nodeId){
  if(!nodes.some(function(n){return n.id===nodeId;}))throw Error("Выберите существующий блок");
  if(groups.length>=20)throw Error("Лимит 20 групп");
  title=String(title||"").trim();
  if(title.length<2||title.length>60)throw Error("Название группы: 2–60 символов");
  if(groups.some(function(g){return g.node_ids.includes(nodeId);}))
   throw Error("Блок уже включён в группу");
  return groups.concat([{id:nextId(groups),title:title,node_ids:[nodeId]}]);
 }
 function move(groups,nodes,groupId,nodeId){
  if(!nodes.some(function(n){return n.id===nodeId;}))throw Error("Блок не найден");
  if(!groups.some(function(g){return g.id===groupId;}))throw Error("Группа не найдена");
  return groups.map(function(g){
   return {...g,node_ids:g.id===groupId?
    Array.from(new Set(g.node_ids.concat([nodeId]))):
    g.node_ids.filter(function(id){return id!==nodeId;})};
  }).filter(function(g){return g.node_ids.length;});
 }
 function ungroup(groups,nodeId){
  return groups.map(function(g){
   return {...g,node_ids:g.node_ids.filter(function(id){return id!==nodeId;})};
  }).filter(function(g){return g.node_ids.length;});
 }
 function deleteGroup(groups,id){return groups.filter(function(g){return g.id!==id;});}
 var api={clean:clean,create:create,move:move,ungroup:ungroup,deleteGroup:deleteGroup};
 if(typeof module!=="undefined"&&module.exports)module.exports=api;
 if(root)root.OmniGraphGroups=api;
})(typeof window!=="undefined"?window:null);
