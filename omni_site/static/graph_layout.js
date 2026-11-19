/* OMNIFACTORY Graph Studio — deterministic, bounded graph auto-layout.
   Pure algorithm: never mutates nodes, edges or saved positions.
   CommonJS export permits direct execution in tests without a browser. */
(function(root){
  "use strict";
  function arrange(scenario){
    if(!scenario||!Array.isArray(scenario.nodes)||!scenario.nodes.length||
       scenario.nodes.length>80)throw Error("Сценарий должен содержать от 1 до 80 узлов");
    var nodes=scenario.nodes, byId=new Map(),index=new Map();
    nodes.forEach(function(n,i){
      if(!n||typeof n.id!=="string"||byId.has(n.id))
        throw Error("Некорректные или повторяющиеся идентификаторы блоков");
      byId.set(n.id,n);index.set(n.id,i);
    });
    if(!byId.has(scenario.start))throw Error("Не найден стартовый блок");
    function destinations(node){
      var result=node.kind==="choice"?(node.options||[]).map(function(o){return o.target;})
        :node.kind==="condition"?[node.true_target,node.false_target]:[node.next];
      return result.filter(function(id){return byId.has(id);});
    }
    var depth=new Map(),order=[],queue=[scenario.start],head=0;
    depth.set(scenario.start,0);
    while(head<queue.length){
      var id=queue[head++],node=byId.get(id);
      order.push(id);
      destinations(node).forEach(function(target){
        if(!depth.has(target)){depth.set(target,depth.get(id)+1);queue.push(target);}
      });
    }
    // Include isolated nodes in their original authoring order.
    nodes.forEach(function(node){
      if(!depth.has(node.id)){depth.set(node.id,-1);order.push(node.id);}
    });
    var layers=new Map();
    order.forEach(function(id){
      var d=depth.get(id);
      if(!layers.has(d))layers.set(d,[]);
      layers.get(d).push(id);
    });
    var reachableLayers=Array.from(layers.keys()).filter(function(d){return d>=0;});
    var canLayer=reachableLayers.length<=6 &&
      reachableLayers.every(function(d){return layers.get(d).length<=13;}) &&
      (!layers.has(-1)||layers.get(-1).length<=13);
    var positions={};
    var originX=80,originY=88,gapX=344,gapY=250;
    if(canLayer){
      reachableLayers.forEach(function(d){
        layers.get(d).forEach(function(id,row){
          positions[id]={x:originX+d*gapX,y:originY+row*gapY};
        });
      });
      if(layers.has(-1)){
        // Disconnected nodes sit in a separate bottom band.
        var maxY=Math.max.apply(null,Object.keys(positions).map(function(id){return positions[id].y;}));
        layers.get(-1).forEach(function(id,row){
          positions[id]={x:originX,y:maxY+gapY*(row+1)};
        });
      }
    }else{
      // Dense or deep graphs wrap in rows, not outside the editable world.
      order.forEach(function(id,i){
        positions[id]={x:originX+(i%6)*gapX,y:originY+Math.floor(i/6)*gapY};
      });
    }
    var height=Math.max(1400,...Object.keys(positions).map(function(id){
      return positions[id].y+260;
    }));
    if(height>8000)throw Error("Недостаточно места для автоматической компоновки");
    return {positions:positions,width:2200,height:height,
            nodes:order.length,mode:canLayer?"layers":"wrapped",
            disconnected:layers.has(-1)?layers.get(-1).length:0};
  }
  var api={arrange:arrange};
  if(typeof module!=="undefined"&&module.exports)module.exports=api;
  if(root)root.OmniGraphLayout=api;
})(typeof window!=="undefined"?window:null);
