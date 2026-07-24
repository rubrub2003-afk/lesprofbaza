(function(){
  function maskPhone(v){
    var d=v.replace(/\D/g,'');
    if(d[0]==='8') d='7'+d.slice(1);
    if(d[0]!=='7') d='7'+d;
    d=d.slice(0,11);
    var r='+7';
    if(d.length>1) r+=' ('+d.slice(1,4);
    if(d.length>=5) r+=') '+d.slice(4,7);
    else if(d.length>4) r+=') '+d.slice(4);
    if(d.length>=8) r+='-'+d.slice(7,9);
    else if(d.length>7) r+='-'+d.slice(7);
    if(d.length>=10) r+='-'+d.slice(9,11);
    else if(d.length>9) r+='-'+d.slice(9);
    return r;
  }
  function isPhone(el){
    if(el.tagName!=='INPUT') return false;
    var ph=(el.getAttribute('placeholder')||'');
    return el.type==='tel' || el.name==='phone' || ph.indexOf('+7')===0;
  }
  function bind(el){
    el.addEventListener('focus',function(){ if(!el.value) el.value='+7 '; });
    el.addEventListener('input',function(){ el.value=maskPhone(el.value); });
    el.addEventListener('blur',function(){ if(el.value==='+7 '||el.value==='+7') el.value=''; });
    el.dataset.bound='1';
  }
  document.querySelectorAll('input').forEach(function(el){ if(isPhone(el) && !el.dataset.bound) bind(el); });

  window.openCallback=function(title, productSlug, comment){
    var m=document.getElementById('cbModal'); if(!m) return;
    document.getElementById('cbTitle').textContent=title||'Заказать звонок';
    document.getElementById('cbProduct').value=productSlug||'';
    document.getElementById('cbComment').value=comment||'';
    document.getElementById('cbKind').value=productSlug?'quick':'callback';
    document.getElementById('cbOk').style.display='none';
    document.getElementById('cbForm').style.display='block';
    m.classList.add('show');
    var ph=m.querySelector('input[name=phone]'); ph.value=''; if(!ph.dataset.bound) bind(ph); setTimeout(function(){ph.focus();},50);
  };
  window.closeCallback=function(){ var m=document.getElementById('cbModal'); if(m) m.classList.remove('show'); };
  window.submitCallback=function(){
    var fd=new FormData(document.getElementById('cbForm'));
    fetch(window.LEAD_URL,{method:'POST',headers:{'X-CSRFToken':window.CSRF},body:fd})
      .then(function(r){return r.json();})
      .then(function(d){ if(d.ok){ document.getElementById('cbForm').style.display='none'; document.getElementById('cbOk').style.display='block'; } else { alert(d.error||'Проверьте телефон'); } })
      .catch(function(){ alert('Не удалось отправить, попробуйте позвонить нам.'); });
  };

  function lpbGuardNumeric(){
    document.querySelectorAll('input[type="number"], input[inputmode="numeric"], input.q').forEach(function(el){
      if(el.dataset.ng) return; el.dataset.ng='1';
      var dec = (el.step && el.step!=='' && el.step!=='1') || el.classList.contains('dec') || ['vol','cost','price','genqty'].indexOf(el.id)>-1;
      el.addEventListener('keydown',function(e){
        if(e.ctrlKey||e.metaKey||e.altKey) return;
        var ok=['Backspace','Delete','Tab','Escape','Enter','ArrowLeft','ArrowRight','ArrowUp','ArrowDown','Home','End'];
        if(ok.indexOf(e.key)>-1) return;
        if(e.key.length>1) return;
        if(/[0-9]/.test(e.key)) return;
        if(dec && (e.key==='.'||e.key===',') && el.value.indexOf('.')<0 && el.value.indexOf(',')<0) return;
        e.preventDefault();
      });
      el.addEventListener('input',function(){
        var v=el.value;
        var c = dec ? v.replace(/[^0-9.,]/g,'').replace(',','.').replace(/(\..*)\./g,'$1') : v.replace(/[^0-9]/g,'');
        var ip=c.split('.')[0]; if(ip.length>6){ c = ip.slice(0,6) + (c.indexOf('.')>-1 ? c.slice(c.indexOf('.')) : ''); }
        if(c!==v) el.value=c;
      });
    });
  }
  document.addEventListener('DOMContentLoaded',lpbGuardNumeric);
})();