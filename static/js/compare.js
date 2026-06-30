(function(){
  var KEY='lpb_compare';
  function get(){try{return JSON.parse(localStorage.getItem(KEY))||[];}catch(e){return [];}}
  function setA(a){localStorage.setItem(KEY,JSON.stringify(a));paint();bar();}
  window.toggleCmp=function(slug,ev){
    if(ev){ev.preventDefault();ev.stopPropagation();}
    var a=get(), i=a.indexOf(slug);
    if(i>-1)a.splice(i,1);
    else if(a.length>=4){alert('Сравнить можно до 4 товаров одновременно');return;}
    else a.push(slug);
    setA(a);
  };
  function paint(){
    var a=get();
    document.querySelectorAll('[data-cmp-slug]').forEach(function(el){
      var on=a.indexOf(el.getAttribute('data-cmp-slug'))>-1;
      el.classList.toggle('on',on);
      var card=el.closest('.card'); if(card)card.classList.toggle('cmp-selected',on);
    });
  }
  function bar(){
    var a=get(), b=document.getElementById('cmpbar'); if(!b)return;
    var n=document.getElementById('cmpn'); if(n)n.textContent=a.length;
    b.classList.toggle('show',a.length>0);
    var go=document.getElementById('cmpgo'); if(go)go.href='/catalog/compare/?items='+a.join(',');
  }
  window.clearCmp=function(){setA([]);};
  document.addEventListener('DOMContentLoaded',function(){paint();bar();});
})();
