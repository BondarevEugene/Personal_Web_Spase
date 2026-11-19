/* In-memory undo/redo for a single Graph Studio document.
   Never persists customer data or mixes project histories. */
(function(root){
  "use strict";
  function snapshot(value){return JSON.parse(JSON.stringify(value));}
  function create(initial,limit){
    var max=Math.max(2,Math.min(100,limit||60));
    var stack=[snapshot(initial)],index=0,lastGroup=null,lastAt=0;
    function record(value,group){
      var next=snapshot(value);
      if(JSON.stringify(stack[index])===JSON.stringify(next))return false;
      if(index<stack.length-1)stack=stack.slice(0,index+1);
      var now=Date.now();
      // Group fast consecutive edits in the SAME inspector field.
      // Never coalesce structural edits (nodes, links, layout).
      if(group&&lastGroup===group&&now-lastAt<700&&index>0){
        stack[index]=next;
      }else{
        stack.push(next);index++;
        if(stack.length>max){stack.shift();index--;}
      }
      lastGroup=group||null;lastAt=now;
      return true;
    }
    function undo(){
      if(index<=0)return null;
      index--;lastGroup=null;
      return snapshot(stack[index]);
    }
    function redo(){
      if(index>=stack.length-1)return null;
      index++;lastGroup=null;
      return snapshot(stack[index]);
    }
    function reset(value){
      stack=[snapshot(value)];index=0;lastGroup=null;lastAt=0;
    }
    return {
      record:record,undo:undo,redo:redo,reset:reset,
      canUndo:function(){return index>0;},
      canRedo:function(){return index<stack.length-1;},
      length:function(){return stack.length;},
    };
  }
  var api={create:create};
  if(typeof module!=="undefined"&&module.exports)module.exports=api;
  if(root)root.OmniGraphHistory=api;
})(typeof window!=="undefined"?window:null);
