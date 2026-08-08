// [UI-009] clock.js — the interactive shop clock: SVG hands, six world times, tick sound
// DOES:   drives the analog SVG clock (#iglHour/#iglMin/#iglSec) and the six
//         time-zone readouts once a second, and toggles a synthesized ticking
//         sound from the #iglTickBtn button.
// IN:     page language sniffed from the URL path; DOM ids iglHour/iglMin/iglSec,
//         ict0..5 / icd0..5, iglTickBtn / iglTickDot / iglTickLabel
// OUT:    per-second transform + textContent updates; Web Audio noise bursts while on
// NOTES:  all Intl calls are try/catch wrapped because timeZone support varies;
//         everything hangs off init() so the inline SVG is guaranteed parsed.
(function(){
  'use strict';

  var CX=110, CY=110;
  var TZ=['Europe/Tirane','Europe/London','Europe/Rome','Asia/Tokyo','America/New_York','Europe/Paris'];

  // [UI-009.a] init — one-time wiring once the DOM (and inline SVG) is parsed
  // DOES:   resolves language + hand elements, starts the 1s update loop, and binds
  //         the tick-sound toggle.
  function init(){
    var lang=/\/it\//.test(location.pathname)?'it':/\/sq\//.test(location.pathname)?'sq':'en';
    var LABELS_ON  ={en:'Ticking on',  it:'Attivo', sq:'Aktiv'}[lang];
    var LABELS_OFF ={en:'Ticking sound',it:'Suono tic-tac',sq:'Ticking'}[lang];

    /* Hand elements — try both APIs; SVG inline-in-HTML can behave
       differently across browsers */
    var hourEl = document.getElementById('iglHour') || document.querySelector('[id=iglHour]');
    var minEl  = document.getElementById('iglMin')  || document.querySelector('[id=iglMin]');
    var secEl  = document.getElementById('iglSec')  || document.querySelector('[id=iglSec]');

    // [UI-009.b] rotate — position one hand
    // DOES:   applies an SVG rotate() around the dial center; swallows the throw some
    //         engines produce for transform attributes on inline SVG.
    function rotate(el,deg){
      if(!el) return;
      try{ el.setAttribute('transform','rotate('+deg+','+CX+','+CY+')'); }catch(e){}
    }

    /* ── Tick every second ── */
    // [UI-009.c] update — the per-second frame
    // DOES:   fractional hand angles (so the minute hand creeps rather than jumps)
    //         plus the six world-time and date readouts, each with a local-time
    //         fallback when the timeZone is unsupported.
    function update(){
      var now=new Date();
      var s=now.getSeconds()+now.getMilliseconds()/1000;
      var m=now.getMinutes()+s/60;
      var h=(now.getHours()%12)+m/60;
      rotate(hourEl,h*30);
      rotate(minEl, m*6);
      rotate(secEl, s*6);
      for(var i=0;i<TZ.length;i++){
        var tel=document.getElementById('ict'+i);
        var del=document.getElementById('icd'+i);
        if(tel){
          try{
            tel.textContent=now.toLocaleTimeString('en-GB',
              {timeZone:TZ[i],hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false});
          }catch(e){
            tel.textContent=now.toTimeString().slice(0,8);
          }
        }
        if(del){
          try{
            del.textContent=now.toLocaleDateString('en-GB',
              {timeZone:TZ[i],weekday:'short',month:'short',day:'numeric'});
          }catch(e){}
        }
      }
    }
    update();
    setInterval(update,1000);

    /* ── Ticking sound ── */
    var actx=null,ticking=false,tto=null,tiv=null;
    // [UI-009.d] playTick — one 40ms tick
    // DOES:   synthesizes an exponentially-decaying noise burst so the tick sounds
    //         mechanical rather than like a beep; silently no-ops without a context.
    function playTick(){
      try{
        if(!actx) return;
        var sr=actx.sampleRate,len=Math.floor(sr*.04);
        var buf=actx.createBuffer(1,len,sr),ch=buf.getChannelData(0);
        for(var j=0;j<len;j++) ch[j]=(Math.random()*2-1)*Math.exp(-j/(sr*.008));
        var src=actx.createBufferSource(),g=actx.createGain();
        g.gain.value=0.18; src.buffer=buf; src.connect(g); g.connect(actx.destination); src.start();
      }catch(e){}
    }
    // [UI-009.e] toggleTick — sound on/off from the button
    // DOES:   flips state + indicator dot/label; on enable it creates/resumes the
    //         AudioContext inside the click gesture (autoplay policy) and aligns the
    //         first tick to the next wall-clock second before starting the interval.
    function toggleTick(){
      ticking=!ticking;
      var dot=document.getElementById('iglTickDot');
      var lbl=document.getElementById('iglTickLabel');
      if(dot) dot.className='clock-tick-dot'+(ticking?' on':'');
      if(lbl) lbl.textContent=ticking?LABELS_ON:LABELS_OFF;
      if(ticking){
        try{
          if(!actx) actx=new(window.AudioContext||window.webkitAudioContext)();
          if(actx.state==='suspended') actx.resume();
          var ms=1000-new Date().getMilliseconds();
          tto=setTimeout(function(){
            if(!ticking) return;
            playTick();
            tiv=setInterval(function(){if(ticking) playTick();},1000);
          },ms);
        }catch(e){}
      }else{clearTimeout(tto);clearInterval(tiv);}
    }
    var btn=document.getElementById('iglTickBtn');
    if(btn) btn.addEventListener('click',toggleTick);
  }

  /* defer guarantees DOM is parsed, but DOMContentLoaded is a safety net */
  if(document.readyState==='loading'){
    document.addEventListener('DOMContentLoaded',init);
  }else{
    init();
  }
})();
