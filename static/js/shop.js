/* ЛЕСПРОФБАЗА — корзина (AJAX+анимация), избранное, сравнение. Один файл на все страницы. */
(function(){
  var CKEY='lpb_compare', FKEY='lpb_fav';
  function gj(k){try{return JSON.parse(localStorage.getItem(k))||[];}catch(e){return [];}}
  function sj(k,a){localStorage.setItem(k,JSON.stringify(a));}
  function enc(a){return a.map(encodeURIComponent).join(',');}

  /* ---------- стили (внедряем, чтобы работало на всех страницах) ---------- */
  var css='.flydot{position:fixed;width:18px;height:18px;border-radius:50%;background:#B97E3F;box-shadow:0 4px 12px rgba(0,0,0,.3);z-index:9999;pointer-events:none;transition:transform .65s cubic-bezier(.5,-.3,.4,1),opacity .65s ease}'
   +'.cart.bump{animation:lpbbump .35s ease}@keyframes lpbbump{0%{transform:scale(1)}40%{transform:scale(1.22)}100%{transform:scale(1)}}'
   +'.lpb-toast{position:fixed;left:50%;bottom:26px;transform:translateX(-50%) translateY(20px);background:#1B1A17;color:#EFE6D5;padding:12px 22px;border-radius:999px;font-family:Manrope,sans-serif;font-size:14px;font-weight:600;z-index:9999;opacity:0;transition:opacity .3s,transform .3s;box-shadow:0 10px 30px rgba(0,0,0,.25)}.lpb-toast.show{opacity:1;transform:translateX(-50%) translateY(0)}'
   +'.fav.on,[data-fav-slug].on{color:#B97E3F!important}.btn-ic.on{background:#274A36;color:#fff;border-color:#274A36}'
   +'.favlink{position:relative}.favn{position:absolute;top:-5px;right:-5px;background:#B97E3F;color:#fff;font-size:11px;min-width:17px;height:17px;border-radius:999px;display:grid;place-items:center;font-weight:700;padding:0 4px}';
  var st=document.createElement('style');st.textContent=css;document.head.appendChild(st);

  /* ---------- СРАВНЕНИЕ ---------- */
  window.toggleCmp=function(slug,ev){if(ev){ev.preventDefault();ev.stopPropagation();}
    var a=gj(CKEY),i=a.indexOf(slug);
    if(i>-1)a.splice(i,1);
    else if(a.length>=4){toast('Сравнить можно до 4 товаров');return;}
    else a.push(slug);
    sj(CKEY,a);paintCmp();barCmp();};
  window.clearCmp=function(){sj(CKEY,[]);paintCmp();barCmp();};
  function paintCmp(){var a=gj(CKEY);
    document.querySelectorAll('[data-cmp-slug]').forEach(function(el){
      var on=a.indexOf(el.getAttribute('data-cmp-slug'))>-1;
      el.classList.toggle('on',on);
      var card=el.closest('.card');if(card)card.classList.toggle('cmp-selected',on);});}
  function barCmp(){var a=gj(CKEY),b=document.getElementById('cmpbar');if(!b)return;
    var n=document.getElementById('cmpn');if(n)n.textContent=a.length;
    b.classList.toggle('show',a.length>0);
    var go=document.getElementById('cmpgo');if(go)go.href='/catalog/compare/?items='+enc(a);}

  /* ---------- ИЗБРАННОЕ ---------- */
  window.toggleFav=function(slug,ev){if(ev){ev.preventDefault();ev.stopPropagation();}
    var a=gj(FKEY),i=a.indexOf(slug);
    if(i>-1){a.splice(i,1);toast('Убрано из избранного');}else{a.push(slug);toast('Добавлено в избранное');}
    sj(FKEY,a);paintFav();};
  window.clearFav=function(){sj(FKEY,[]);paintFav();};
  function paintFav(){var a=gj(FKEY);
    document.querySelectorAll('[data-fav-slug]').forEach(function(el){
      var on=a.indexOf(el.getAttribute('data-fav-slug'))>-1;
      el.classList.toggle('on',on);el.textContent=on?'♥':'♡';});
    document.querySelectorAll('.favlink').forEach(function(el){
      el.setAttribute('href','/catalog/favorites/?items='+enc(a));
      var c=el.querySelector('.favn');if(c){c.textContent=a.length;c.style.display=a.length?'':'none';}});}

  /* ---------- ДОБАВЛЕНИЕ В КОРЗИНУ (без перехода) ---------- */
  window.addCart=function(slug,qty,srcEl,ev){if(ev){ev.preventDefault();ev.stopPropagation();}
    qty=parseInt(qty)||1;if(qty<1)qty=1;
    var fd=new FormData();fd.append('qty',qty);
    fetch('/cart/add/'+encodeURIComponent(slug)+'/',{method:'POST',
      headers:{'X-CSRFToken':window.CSRF||'','X-Requested-With':'XMLHttpRequest'},body:fd})
      .then(function(r){return r.json();})
      .then(function(d){if(d&&typeof d.count!=='undefined'){updateCount(d.count);fly(srcEl);toast('Товар в корзине');}})
      .catch(function(){window.location='/cart/';});};
  function updateCount(n){document.querySelectorAll('.cart span').forEach(function(s){s.textContent=n;});}
  function fly(srcEl){
    var cart=document.querySelector('.iconbtn.cart');
    if(!srcEl||!cart){return;}
    var s=srcEl.getBoundingClientRect(),c=cart.getBoundingClientRect();
    var dot=document.createElement('div');dot.className='flydot';
    var x0=s.left+s.width/2,y0=s.top+s.height/2;
    dot.style.left=x0+'px';dot.style.top=y0+'px';document.body.appendChild(dot);
    requestAnimationFrame(function(){
      var dx=(c.left+c.width/2)-x0,dy=(c.top+c.height/2)-y0;
      dot.style.transform='translate('+dx+'px,'+dy+'px) scale(.2)';dot.style.opacity='0.2';});
    setTimeout(function(){dot.remove();cart.classList.add('bump');
      setTimeout(function(){cart.classList.remove('bump');},350);},660);}

  var tt;
  function toast(msg){var t=document.getElementById('lpbToast');
    if(!t){t=document.createElement('div');t.id='lpbToast';t.className='lpb-toast';document.body.appendChild(t);}
    t.textContent=msg;t.classList.add('show');clearTimeout(tt);
    tt=setTimeout(function(){t.classList.remove('show');},1700);}
  window.lpbToast=toast;

  document.addEventListener('DOMContentLoaded',function(){paintCmp();barCmp();paintFav();});
})();
