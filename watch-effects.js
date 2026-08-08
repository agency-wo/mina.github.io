// [UI-012] watch-effects.js — IglisiEffects: the four decorative page effects (UMD)
// DOES:   exposes loupe / tickIn / trail / balanceWheel plus init(config); each
//         effect is self-contained and inert when its selector matches nothing.
// IN:     selectors + option bags per effect (see each concept's header)
// OUT:    window.IglisiEffects (or the AMD/CommonJS export)
// NOTES:  only TickIn honors prefers-reduced-motion itself; callers gate the rest
//         (watch-effects-shop-init.js does exactly that for the balance wheel).
/*!
 * Iglisi Watch — Interactive Effects  v1.0
 * watch-effects.js
 */
(function(root,factory){
  if(typeof define==='function'&&define.amd){define([],factory);}
  else if(typeof module!=='undefined'&&module.exports){module.exports=factory();}
  else{root.IglisiEffects=factory();}
}(typeof self!=='undefined'?self:this,function(){
  'use strict';

  /* ============================================================
     CONCEPT 1: WATCHMAKER'S LOUPE
  ============================================================ */
  /* [UI-012.a] Loupe — watchmaker's magnifier that follows the cursor over cards
     DOES:   builds the lens chrome (glare, rim, reticle) once per section, then on
             rAF-throttled mousemove repositions it and recomputes the zoomed
             background-image of whichever card image the cursor is over.
     IN:     sectionSel + cardSel selectors; options {size,zoom}
     OUT:    an absolutely-positioned lens div in the section; card cursor hidden
     NOTES:  background-image zoom instead of canvas keeps same-origin images free
             of CORS taint (see the inline note). */
  function Loupe(sectionSel,cardSel,options){
    var opts={size:148,zoom:3};
    if(options){if(options.size)opts.size=options.size;if(options.zoom)opts.zoom=options.zoom;}
    var section=document.querySelector(sectionSel);
    if(!section)return;
    section.style.position='relative';

    var half=opts.size/2;

    /* Loupe shell — background-image/size/position drives the actual zoom.
       No canvas means no CORS taint issues with same-origin images. */
    var loupe=document.createElement('div');
    loupe.className='iw-loupe';
    loupe.style.cssText=[
      'position:absolute',
      'width:'+opts.size+'px',
      'height:'+opts.size+'px',
      'border-radius:50%',
      'pointer-events:none',
      'display:none',
      'transform:translate(-50%,-50%)',
      'z-index:100',
      'overflow:hidden',
      'background-repeat:no-repeat',
      /* Gold ring + outer glow */
      'box-shadow:0 0 0 2.5px #b8953f,0 0 0 4px rgba(184,149,63,0.25),0 8px 36px rgba(0,0,0,0.45)',
      'will-change:left,top,background-position'
    ].join(';');

    /* Glass glare — two radial gradients stacked: top-left highlight + bottom-right counter-glow */
    var glare=document.createElement('div');
    glare.style.cssText=[
      'position:absolute',
      'inset:0',
      'border-radius:50%',
      'pointer-events:none',
      'z-index:2',
      'background:radial-gradient(ellipse 52% 42% at 33% 28%,rgba(255,255,255,0.26) 0%,rgba(255,255,255,0) 68%),'+
                 'radial-gradient(ellipse 40% 35% at 68% 72%,rgba(255,255,255,0.07) 0%,rgba(255,255,255,0) 65%)',
      'box-shadow:inset 0 0 22px rgba(0,0,0,0.28)'
    ].join(';');

    /* Fine inner rim — gives the lens barrel depth */
    var rim=document.createElement('div');
    rim.style.cssText=[
      'position:absolute',
      'inset:0',
      'border-radius:50%',
      'border:1px solid rgba(184,149,63,0.4)',
      'pointer-events:none',
      'z-index:3'
    ].join(';');

    /* Tiny gold reticle dot at center */
    var dot=document.createElement('div');
    dot.style.cssText=[
      'position:absolute',
      'left:50%',
      'top:50%',
      'width:5px',
      'height:5px',
      'border-radius:50%',
      'background:rgba(184,149,63,0.7)',
      'transform:translate(-50%,-50%)',
      'pointer-events:none',
      'z-index:4'
    ].join(';');

    loupe.appendChild(glare);
    loupe.appendChild(rim);
    loupe.appendChild(dot);
    section.appendChild(loupe);

    var activeImg=null;
    var mx=0, my=0, rafId=null;

    function render(){
      rafId=null;
      if(!activeImg||!activeImg.complete||!activeImg.naturalWidth)return;
      var sRect=section.getBoundingClientRect();
      var imgRect=activeImg.getBoundingClientRect();
      /* Position loupe over cursor */
      loupe.style.left=(mx-sRect.left)+'px';
      loupe.style.top=(my-sRect.top)+'px';
      /* Compute zoomed background */
      var relX=Math.max(0,Math.min(1,(mx-imgRect.left)/imgRect.width));
      var relY=Math.max(0,Math.min(1,(my-imgRect.top)/imgRect.height));
      var bgW=imgRect.width*opts.zoom;
      var bgH=imgRect.height*opts.zoom;
      var posX=-(relX*bgW-half);
      var posY=-(relY*bgH-half);
      loupe.style.backgroundImage='url("'+activeImg.src+'")';
      loupe.style.backgroundSize=bgW+'px '+bgH+'px';
      loupe.style.backgroundPosition=posX+'px '+posY+'px';
    }

    var cards=section.querySelectorAll(cardSel);
    for(var c=0;c<cards.length;c++){
      (function(card){
        card.addEventListener('mouseenter',function(){
          activeImg=card.querySelector('img');
          card.style.cursor='none';
          loupe.style.display='block';
        });
        card.addEventListener('mouseleave',function(){
          loupe.style.display='none';
          card.style.cursor='';
          activeImg=null;
          if(rafId){cancelAnimationFrame(rafId);rafId=null;}
        });
        card.addEventListener('mousemove',function(e){
          mx=e.clientX; my=e.clientY;
          if(!rafId) rafId=requestAnimationFrame(render);
        });
      }(cards[c]));
    }
  }

  /* ============================================================
     CONCEPT 2: ESCAPEMENT TICK-IN
  ============================================================ */
  /* [UI-012.b] TickIn — reveals text character by character with a watch-tick sound
     DOES:   when a [data-tick-in] element scrolls into view, wraps its text nodes in
             per-char spans and fades them in at a jittered cadence, optionally
             ticking per character from a pooled <audio> element.
     IN:     data-tick-in / data-tick-speed / data-tick-delay / data-tick-sound attrs
     OUT:    span-wrapped text; a 3-element <audio> pool fed by a WAV built at runtime
     NOTES:  reduced-motion shows everything at once; audio stays silent until a user
             gesture unlocks the pool. The <audio>-not-WebAudio choice is explained
             in the note below. */
  function TickIn(){
    /* Use <audio> elements instead of Web Audio API.
       Web Audio requires AudioContext.resume() which is async and
       unreliable on iOS Safari — the context state lags behind the
       Promise resolution, causing every tick() guard to bail early.
       <audio> elements unlock once in a gesture and play freely after. */

    /* Build a 35 ms tick sound as a WAV data-URL at runtime.
       22050 Hz mono 16-bit PCM — shaped noise burst, sounds like a watch tick. */
    function buildTickURL(){
      var SR=22050, N=Math.floor(SR*0.035);
      var ab=new ArrayBuffer(44+N*2), v=new DataView(ab);
      var wb=function(o,x){v.setUint32(o,x,false);};
      var wl=function(o,x){v.setUint32(o,x,true);};
      var ws=function(o,x){v.setUint16(o,x,true);};
      /* RIFF/WAVE header */
      wb(0,0x52494646); wl(4,36+N*2); wb(8,0x57415645);
      wb(12,0x666d7420); wl(16,16); ws(20,1); ws(22,1);
      wl(24,SR); wl(28,SR*2); ws(32,2); ws(34,16);
      wb(36,0x64617461); wl(40,N*2);
      /* PCM samples: white noise with cubic decay envelope */
      for(var i=0;i<N;i++){
        var env=Math.pow(1-i/N,3)*0.55;
        v.setInt16(44+i*2,(Math.random()*2-1)*env*32767|0,true);
      }
      var u8=new Uint8Array(ab), bin='';
      for(var j=0;j<u8.length;j++) bin+=String.fromCharCode(u8[j]);
      return 'data:audio/wav;base64,'+btoa(bin);
    }

    var pool     = [];   /* 3-element pool prevents rapid ticks from cutting each other off */
    var poolIdx  = 0;
    var unlocked = false;

    function setup(){
      if(pool.length) return;
      try{
        var url=buildTickURL();
        for(var i=0;i<3;i++){
          var a=new Audio(url);
          a.volume=0.28;
          a.load();
          pool.push(a);
        }
      }catch(e){ pool=[]; }
    }

    function unlock(){
      setup();
      if(unlocked || !pool.length) return;
      var a=pool[0];
      a.play().then(function(){ a.pause(); a.currentTime=0; unlocked=true; })
       .catch(function(){
         /* Strict autoplay policy: try muted first, then unmute */
         a.muted=true;
         a.play().then(function(){
           a.muted=false; a.pause(); a.currentTime=0; unlocked=true;
         }).catch(function(){});
       });
    }

    document.addEventListener('touchstart', unlock, {passive:true});
    document.addEventListener('touchend',   unlock, {passive:true});
    document.addEventListener('click',      unlock);

    function tick(){
      if(!unlocked || !pool.length) return;
      var a=pool[poolIdx % pool.length];
      poolIdx++;
      try{ a.currentTime=0; a.play().catch(function(){}); }catch(e){}
    }
    function wrapChars(el){
      (function walk(node){
        if(node.nodeType===3){
          var frag=document.createDocumentFragment(),text=node.textContent;
          for(var i=0;i<text.length;i++){
            var span=document.createElement('span');
            span.className='iw-char'; span.textContent=text[i];
            if(text[i]===' '||text[i]==='\u00A0'||text[i]==='\n'){
              span.setAttribute('data-space',''); span.style.opacity='1';
            }
            frag.appendChild(span);
          }
          node.parentNode.replaceChild(frag,node);
        }else if(node.nodeType===1&&node.tagName!=='SCRIPT'){
          var kids=Array.prototype.slice.call(node.childNodes);
          for(var k=0;k<kids.length;k++) walk(kids[k]);
        }
      }(el));
      return Array.prototype.slice.call(el.querySelectorAll('.iw-char:not([data-space])'));
    }
    function animate(chars,speed,delay,withSound){
      var i=0;
      setTimeout(function step(){
        if(i>=chars.length)return;
        chars[i].style.opacity='1';
        if(withSound)tick();
        i++;
        var next=speed+(Math.random()*speed*.4-speed*.2);
        setTimeout(step,Math.max(18,next));
      },delay);
    }
    return {
      init:function(){
        var reduced=window.matchMedia&&window.matchMedia('(prefers-reduced-motion:reduce)').matches;
        var elements=document.querySelectorAll('[data-tick-in]');
        if(!elements.length||!window.IntersectionObserver)return;
        var observer=new IntersectionObserver(function(entries){
          for(var e=0;e<entries.length;e++){
            var entry=entries[e];
            if(!entry.isIntersecting)continue;
            var el=entry.target;
            if(el.dataset.tickDone)continue;
            el.dataset.tickDone='1';
            observer.unobserve(el);
            if(reduced){
              var all=el.querySelectorAll('.iw-char');
              for(var a=0;a<all.length;a++) all[a].style.opacity='1';
              continue;
            }
            var speed=parseInt(el.dataset.tickSpeed,10)||50;
            var delay=parseInt(el.dataset.tickDelay,10)||0;
            var sound=el.dataset.tickSound!=='false';
            var chars=wrapChars(el);
            animate(chars,speed,delay,sound);
          }
        },{threshold:0.3});
        for(var i=0;i<elements.length;i++) observer.observe(elements[i]);
      }
    };
  }

  /* ============================================================
     CONCEPT 3: GOLD DUST CURSOR TRAIL
  ============================================================ */
  /* [UI-012.c] Trail — gold-dust particles that drift up from the cursor
     DOES:   overlays a pointer-transparent canvas on the section and, per mousemove,
             spawns short-lived particles that rise, fade and are culled; leaving the
             section clears them all.
     IN:     sectionSel; options {color,count,minSize,maxSize,decay,drift}
     OUT:    a canvas child of the section, redrawn every animation frame
     NOTES:  the particle cap evicts the oldest, so a fast cursor cannot grow the
             array unbounded. */
  function Trail(sectionSel,options){
    var opts={color:'#b8953f',count:60,minSize:2,maxSize:5,decay:0.024,drift:0.3};
    if(options){
      if(options.color)  opts.color=options.color;
      if(options.count)  opts.count=options.count;
      if(options.minSize)opts.minSize=options.minSize;
      if(options.maxSize)opts.maxSize=options.maxSize;
      if(options.decay)  opts.decay=options.decay;
      if(options.drift)  opts.drift=options.drift;
    }
    var section=document.querySelector(sectionSel);
    if(!section)return;

    var canvas=document.createElement('canvas');
    canvas.style.cssText='position:absolute;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:1';
    section.appendChild(canvas);
    var ctx=canvas.getContext('2d');

    var hex=opts.color.replace('#','');
    var cr=parseInt(hex.slice(0,2),16),cg=parseInt(hex.slice(2,4),16),cb=parseInt(hex.slice(4,6),16);

    function resize(){canvas.width=section.offsetWidth;canvas.height=section.offsetHeight;}
    resize();
    var rt; window.addEventListener('resize',function(){clearTimeout(rt);rt=setTimeout(resize,150);});

    var particles=[],mouseX=0,mouseY=0;

    section.addEventListener('mousemove',function(e){
      var rect=section.getBoundingClientRect();
      mouseX=e.clientX-rect.left; mouseY=e.clientY-rect.top;
      spawn(); spawn();
    });
    section.addEventListener('mouseleave',function(){particles=[];});

    function spawn(){
      var p={
        x:mouseX+(Math.random()-.5)*8,y:mouseY+(Math.random()-.5)*8,
        size:opts.minSize+Math.random()*(opts.maxSize-opts.minSize),
        opacity:.65+Math.random()*.35,
        vx:(Math.random()-.5)*.6,
        vy:-(opts.drift+Math.random()*opts.drift)
      };
      if(particles.length>=opts.count){particles.shift();}
      particles.push(p);
    }

    function render(){
      ctx.clearRect(0,0,canvas.width,canvas.height);
      for(var i=particles.length-1;i>=0;i--){
        var p=particles[i];
        p.x+=p.vx; p.y+=p.vy; p.opacity-=opts.decay;
        if(p.opacity<=0.01){particles.splice(i,1);continue;}
        ctx.beginPath();
        ctx.arc(p.x,p.y,p.size/2,0,Math.PI*2);
        ctx.fillStyle='rgba('+cr+','+cg+','+cb+','+p.opacity.toFixed(3)+')';
        ctx.fill();
      }
      requestAnimationFrame(render);
    }
    render();
  }

  /* ============================================================
     CONCEPT 4: LIVING BALANCE WHEEL
  ============================================================ */
  /* [UI-012.d] BalanceWheel — a living balance-wheel drawn in SVG
     DOES:   builds the full wheel (bezel, ticks, screws, hairspring, spokes, hub)
             into every matched target and oscillates the spoke group with a sine
             swing, pausing via IntersectionObserver while off-screen.
     IN:     selector; options {size,swing,speed,color,dark}
     OUT:    one <svg> appended per target + a rAF loop per instance
     NOTES:  does NOT check prefers-reduced-motion itself — callers must gate it. */
  function BalanceWheel(selector,options){
    var opts={size:120,swing:38,speed:0.032,color:'#b8953f',dark:true};
    if(options){
      if(options.size!==undefined) opts.size=options.size;
      if(options.swing!==undefined)opts.swing=options.swing;
      if(options.speed!==undefined)opts.speed=options.speed;
      if(options.color)opts.color=options.color;
      if(options.dark!==undefined)opts.dark=options.dark;
    }
    var targets=document.querySelectorAll(selector);
    if(!targets.length)return;
    var ns='http://www.w3.org/2000/svg';
    var cx=opts.size/2,cy=opts.size/2,r=opts.size/2-4;

    function svgEl(tag,attrs){
      var node=document.createElementNS(ns,tag);
      var keys=Object.keys(attrs);
      for(var k=0;k<keys.length;k++) node.setAttribute(keys[k],attrs[keys[k]]);
      return node;
    }

    function buildSVG(){
      var svg=document.createElementNS(ns,'svg');
      svg.setAttribute('width',opts.size); svg.setAttribute('height',opts.size);
      svg.setAttribute('viewBox','0 0 '+opts.size+' '+opts.size);
      svg.setAttribute('style','display:block;overflow:visible');
      var jewel=opts.dark?'#0d1b3e':'#ffffff';
      var spokeR=r-13;

      /* Outer bezel ring */
      svg.appendChild(svgEl('circle',{cx:cx,cy:cy,r:r,fill:'none',stroke:opts.color,'stroke-width':'2'}));
      /* Chapter track band */
      svg.appendChild(svgEl('circle',{cx:cx,cy:cy,r:r-4,fill:'none',stroke:opts.color,'stroke-width':'0.4',opacity:'0.25'}));
      /* Inner guide ring */
      svg.appendChild(svgEl('circle',{cx:cx,cy:cy,r:r-8,fill:'none',stroke:opts.color,'stroke-width':'0.5',opacity:'0.18'}));

      /* Major ticks at 0°/90°/180°/270° */
      var majTicks=[0,90,180,270];
      for(var m=0;m<majTicks.length;m++){
        var rad=(majTicks[m]-90)*Math.PI/180;
        svg.appendChild(svgEl('line',{
          x1:cx+(r-1)*Math.cos(rad),y1:cy+(r-1)*Math.sin(rad),
          x2:cx+(r-10)*Math.cos(rad),y2:cy+(r-10)*Math.sin(rad),
          stroke:opts.color,'stroke-width':'2','stroke-linecap':'round'
        }));
      }
      /* Mid ticks at 45°/135°/225°/315° */
      var midTicks=[45,135,225,315];
      for(var mi=0;mi<midTicks.length;mi++){
        var radMi=(midTicks[mi]-90)*Math.PI/180;
        svg.appendChild(svgEl('line',{
          x1:cx+(r-1)*Math.cos(radMi),y1:cy+(r-1)*Math.sin(radMi),
          x2:cx+(r-6)*Math.cos(radMi),y2:cy+(r-6)*Math.sin(radMi),
          stroke:opts.color,'stroke-width':'1','stroke-linecap':'round',opacity:'0.5'
        }));
      }
      /* Minor ticks */
      var minTicks=[30,60,120,150,210,240,300,330];
      for(var n=0;n<minTicks.length;n++){
        var rad2=(minTicks[n]-90)*Math.PI/180;
        svg.appendChild(svgEl('line',{
          x1:cx+(r-1)*Math.cos(rad2),y1:cy+(r-1)*Math.sin(rad2),
          x2:cx+(r-5)*Math.cos(rad2),y2:cy+(r-5)*Math.sin(rad2),
          stroke:opts.color,'stroke-width':'0.75',opacity:'0.35','stroke-linecap':'round'
        }));
      }

      /* Timing screws (cross-head) at 45°/135°/225°/315° on the bezel */
      var screwPos=[45,135,225,315];
      for(var sc=0;sc<screwPos.length;sc++){
        var scRad=(screwPos[sc]-90)*Math.PI/180;
        var sx=cx+(r-0.5)*Math.cos(scRad), sy=cy+(r-0.5)*Math.sin(scRad);
        var sl=1.6, perpScRad=scRad+Math.PI/2;
        svg.appendChild(svgEl('circle',{cx:sx.toFixed(2),cy:sy.toFixed(2),r:'2.8',fill:jewel,stroke:opts.color,'stroke-width':'0.8'}));
        svg.appendChild(svgEl('line',{
          x1:(sx+sl*Math.cos(scRad)).toFixed(2),y1:(sy+sl*Math.sin(scRad)).toFixed(2),
          x2:(sx-sl*Math.cos(scRad)).toFixed(2),y2:(sy-sl*Math.sin(scRad)).toFixed(2),
          stroke:opts.color,'stroke-width':'0.6'
        }));
        svg.appendChild(svgEl('line',{
          x1:(sx+sl*Math.cos(perpScRad)).toFixed(2),y1:(sy+sl*Math.sin(perpScRad)).toFixed(2),
          x2:(sx-sl*Math.cos(perpScRad)).toFixed(2),y2:(sy-sl*Math.sin(perpScRad)).toFixed(2),
          stroke:opts.color,'stroke-width':'0.6'
        }));
      }

      /* Hairspring: Archimedean spiral in the centre, drawn under the rotating wheel
         so it peeks through the gaps between spokes as the wheel oscillates. */
      var spPts=80, turns=2.5, rIn=8, rOut=21;
      var spPath='';
      for(var sp=0;sp<=spPts;sp++){
        var t=sp/spPts;
        var ang=t*turns*Math.PI*2-Math.PI/2;
        var rr=rIn+(rOut-rIn)*t;
        spPath+=(sp===0?'M':'L')+(cx+rr*Math.cos(ang)).toFixed(2)+','+(cy+rr*Math.sin(ang)).toFixed(2);
      }
      svg.appendChild(svgEl('path',{d:spPath,fill:'none',stroke:opts.color,'stroke-width':'0.5',opacity:'0.28'}));

      /* Rotating wheel group */
      var g=document.createElementNS(ns,'g');

      /* Tapered spokes: polygon wide at the hub, narrow at the jewel */
      var spokes=[0,90,180,270];
      for(var s=0;s<spokes.length;s++){
        var sRad=(spokes[s]-90)*Math.PI/180;
        var perpRad=sRad+Math.PI/2;
        var tx=cx+spokeR*Math.cos(sRad), ty=cy+spokeR*Math.sin(sRad);
        var w0=2.2, w1=0.7;
        var pts=[
          (cx+w0*Math.cos(perpRad)).toFixed(2)+','+(cy+w0*Math.sin(perpRad)).toFixed(2),
          (tx+w1*Math.cos(perpRad)).toFixed(2)+','+(ty+w1*Math.sin(perpRad)).toFixed(2),
          (tx-w1*Math.cos(perpRad)).toFixed(2)+','+(ty-w1*Math.sin(perpRad)).toFixed(2),
          (cx-w0*Math.cos(perpRad)).toFixed(2)+','+(cy-w0*Math.sin(perpRad)).toFixed(2)
        ].join(' ');
        g.appendChild(svgEl('polygon',{points:pts,fill:opts.color,opacity:'0.9'}));
        /* Jewel at spoke tip (smaller and more refined) */
        g.appendChild(svgEl('circle',{cx:tx.toFixed(2),cy:ty.toFixed(2),r:'4',fill:jewel,stroke:opts.color,'stroke-width':'1.2'}));
        g.appendChild(svgEl('circle',{cx:tx.toFixed(2),cy:ty.toFixed(2),r:'1.5',fill:opts.color,opacity:'0.7'}));
      }

      /* Centre hub — 4 concentric elements for a proper pivot look */
      g.appendChild(svgEl('circle',{cx:cx,cy:cy,r:'6.5',fill:jewel,stroke:opts.color,'stroke-width':'1.5'}));
      g.appendChild(svgEl('circle',{cx:cx,cy:cy,r:'4',fill:'none',stroke:opts.color,'stroke-width':'0.5',opacity:'0.5'}));
      g.appendChild(svgEl('circle',{cx:cx,cy:cy,r:'2.8',fill:opts.color}));
      g.appendChild(svgEl('circle',{cx:cx,cy:cy,r:'1',fill:jewel}));
      svg.appendChild(g);

      return {svg:svg,wheel:g};
    }

    function startAnimation(wheelEl,svgElement){
      var t=0,raf=null,running=false;
      function step(){
        t+=opts.speed;
        var angle=Math.sin(t)*opts.swing;
        wheelEl.setAttribute('transform','rotate('+angle.toFixed(3)+','+cx+','+cy+')');
        raf=requestAnimationFrame(step);
      }
      if(!window.IntersectionObserver){step();return;}
      var obs=new IntersectionObserver(function(entries){
        if(entries[0].isIntersecting&&!running){running=true;step();}
        else if(!entries[0].isIntersecting&&running){running=false;cancelAnimationFrame(raf);}
      },{threshold:0.1});
      obs.observe(svgElement);
    }

    for(var i=0;i<targets.length;i++){
      var target=targets[i];
      var built=buildSVG();
      target.appendChild(built.svg);
      startAnimation(built.wheel,built.svg);
    }
  }

  /* ============================================================
     PUBLIC API
  ============================================================ */
  /* [UI-012.e] public API — thin constructors + init(config)
     DOES:   each key instantiates its effect; init() reads a config object so a page
             can declare its effect set in one literal (see the *-init.js files). */
  return {
    loupe:function(sectionSel,cardSel,options){new Loupe(sectionSel,cardSel,options);},
    tickIn:function(){new TickIn().init();},
    trail:function(sectionSel,options){new Trail(sectionSel,options);},
    balanceWheel:function(selector,options){new BalanceWheel(selector,options);},
    init:function(config){
      config=config||{};
      if(config.loupe)        this.loupe(config.loupe.section,config.loupe.cards,config.loupe.options);
      if(config.tickIn)       this.tickIn();
      if(config.trail)        this.trail(config.trail.section,config.trail.options);
      if(config.balanceWheel) this.balanceWheel(config.balanceWheel.selector,config.balanceWheel.options);
    }
  };
}));
