// [UI-010] timer.js — "You've been here for…" dwell-time stopwatch with bell chimes
// DOES:   builds the SVG tick ring, then counts up from page load in mm:ss (hh:mm:ss
//         past an hour), rotating the miniature hands; at 1/3/5 minutes it strikes
//         1/2/3 synthesized bells and swaps in a localized message.
// IN:     iwTimer* DOM ids; <html lang> selects the CHIMES message set
// OUT:    per-second DOM updates; Web Audio output once a user gesture unlocks it
// NOTES:  the audio-unlock ritual (silentUnlock/getAudio) is iOS-specific and
//         deliberately re-arms after suspensions — see the comments on each.
/*!
 * Iglisi Watch — You've Been Here For…  v1.0
 * Language-aware. Web Audio chimes. No dependencies.
 */
(function () {
  'use strict';

  var elElapsed = document.getElementById('iwTimerElapsed');
  var elMsg     = document.getElementById('iwTimerMsg');
  var elHour    = document.getElementById('iwTimerHour');
  var elMin     = document.getElementById('iwTimerMin');
  var elSec     = document.getElementById('iwTimerSec');
  var elSecTail = document.getElementById('iwTimerSecTail');
  var elRing    = document.getElementById('iwTimerRing');
  var ticksG    = document.getElementById('iwTimerTicks');
  if (!elElapsed || !ticksG) return;

  /* ----------------------------------------------------------
     LANGUAGE
  ---------------------------------------------------------- */
  var lang = (document.documentElement.lang || 'en').toLowerCase().slice(0, 2);
  if (lang !== 'it' && lang !== 'sq') lang = 'en';

  var CHIMES = {
    en: [
      { at: 60,  count: 1, message: 'One minute. Time moves whether we notice it or not.' },
      { at: 180, count: 2, message: 'Three minutes. Your watch has earned this much attention too.' },
      { at: 300, count: 3, message: "Five minutes. Most repairs take less time than you\u2019ve spent here." }
    ],
    it: [
      { at: 60,  count: 1, message: 'Un minuto. Il tempo passa, che lo notiamo o no.' },
      { at: 180, count: 2, message: 'Tre minuti. Anche il tuo orologio merita questa attenzione.' },
      { at: 300, count: 3, message: 'Cinque minuti. La maggior parte delle riparazioni richiede meno di questo.' }
    ],
    sq: [
      { at: 60,  count: 1, message: 'Një minutë. Koha kalon, ta vëmë re apo jo.' },
      { at: 180, count: 2, message: 'Tre minuta. Edhe ora juaj meriton po aq vëmendje.' },
      { at: 300, count: 3, message: 'Pesë minuta. Shumica e riparimeve zgjat më pak se koha që keni kaluar këtu.' }
    ]
  };

  /* ----------------------------------------------------------
     BUILD SVG TICK MARKS
  ---------------------------------------------------------- */
  var ns = 'http://www.w3.org/2000/svg';
  for (var i = 0; i < 60; i++) {
    var major = (i % 5 === 0);
    var rad   = (i * 6 - 90) * Math.PI / 180;
    var r1    = major ? 23 : 27;
    var x1 = 45 + r1 * Math.cos(rad);
    var y1 = 60 + r1 * Math.sin(rad);
    var x2 = 45 + 30 * Math.cos(rad);
    var y2 = 60 + 30 * Math.sin(rad);
    var ln = document.createElementNS(ns, 'line');
    ln.setAttribute('x1', x1.toFixed(2)); ln.setAttribute('y1', y1.toFixed(2));
    ln.setAttribute('x2', x2.toFixed(2)); ln.setAttribute('y2', y2.toFixed(2));
    ln.setAttribute('stroke', major ? 'rgba(184,149,63,0.55)' : 'rgba(184,149,63,0.2)');
    ln.setAttribute('stroke-width', major ? '1.5' : '0.8');
    ln.setAttribute('stroke-linecap', 'round');
    ticksG.appendChild(ln);
  }

  /* ----------------------------------------------------------
     AUDIO CONTEXT
  ---------------------------------------------------------- */
  var audioCtx = null;

  /* [UI-010.a] silentUnlock — force the AudioContext into 'running' inside a gesture */
  /* Play a 1-sample silent buffer — iOS Safari requires this to truly
     activate the AudioContext; resume() alone is not always enough.
     Only acts when the context is not already running. */
  function silentUnlock() {
    if (!audioCtx || audioCtx.state === 'running') return;
    try {
      var buf = audioCtx.createBuffer(1, 1, audioCtx.sampleRate);
      var src = audioCtx.createBufferSource();
      src.buffer = buf; src.connect(audioCtx.destination); src.start(0);
    } catch (e) {}
    audioCtx.resume().catch(function () {});
  }

  /* [UI-010.b] getAudio — lazy AudioContext factory
     DOES:  creates the context on first use and installs the permanent gesture
            listeners that keep re-unlocking it (rationale in the inline note). */
  function getAudio() {
    if (!audioCtx) {
      try {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        /* Permanent gesture listeners — no once:true so the context can be
           re-unlocked after a phone call or tab switch suspends it again. */
        document.addEventListener('touchstart', silentUnlock, { passive: true, capture: true });
        document.addEventListener('touchend',   silentUnlock, { passive: true, capture: true });
        document.addEventListener('click',      silentUnlock, { capture: true });
      } catch (e) {}
    }
    return audioCtx;
  }

  /* ----------------------------------------------------------
     CHIME SYNTHESIS — warm bell tone
  ---------------------------------------------------------- */
  var CHIME_FREQ = [659.3, 587.3, 523.3]; /* E5, D5, C5 */

  /* [UI-010.c] playChime — n bell strikes, 0.72s apart
     DOES:  each strike layers a sine fundamental, a stretched 2nd harmonic and a
            band-passed noise transient so it reads as a struck bell, not a tone.
     IN:    n — strike count; pitch walks down E5/D5/C5 per strike. */
  function playChime(n) {
    var ctx = getAudio();
    /* Only play when the context is confirmed running — never try to use
       oscillators on a suspended context (iOS ignores them silently). */
    if (!ctx || ctx.state !== 'running') return;

    for (var i = 0; i < n; i++) {
      (function (delay, freq) {
        /* Fundamental */
        var osc1 = ctx.createOscillator(), env1 = ctx.createGain();
        osc1.type = 'sine'; osc1.frequency.value = freq;
        env1.gain.setValueAtTime(0, ctx.currentTime + delay);
        env1.gain.linearRampToValueAtTime(0.09, ctx.currentTime + delay + 0.005);
        env1.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + delay + 2.2);
        osc1.connect(env1); env1.connect(ctx.destination);
        osc1.start(ctx.currentTime + delay); osc1.stop(ctx.currentTime + delay + 2.3);

        /* 2nd harmonic */
        var osc2 = ctx.createOscillator(), env2 = ctx.createGain();
        osc2.type = 'sine'; osc2.frequency.value = freq * 2.756;
        env2.gain.setValueAtTime(0, ctx.currentTime + delay);
        env2.gain.linearRampToValueAtTime(0.025, ctx.currentTime + delay + 0.005);
        env2.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + delay + 1.0);
        osc2.connect(env2); env2.connect(ctx.destination);
        osc2.start(ctx.currentTime + delay); osc2.stop(ctx.currentTime + delay + 1.1);

        /* Strike transient */
        var bufLen = Math.floor(ctx.sampleRate * 0.015);
        var buf = ctx.createBuffer(1, bufLen, ctx.sampleRate);
        var data = buf.getChannelData(0);
        for (var s = 0; s < bufLen; s++) {
          data[s] = (Math.random() - 0.5) * Math.pow(1 - s / bufLen, 2);
        }
        var noise = ctx.createBufferSource();
        var nFilt = ctx.createBiquadFilter();
        var nGain = ctx.createGain();
        nFilt.type = 'bandpass'; nFilt.frequency.value = freq * 1.5; nFilt.Q.value = 1.2;
        nGain.gain.value = 0.06;
        noise.buffer = buf;
        noise.connect(nFilt); nFilt.connect(nGain); nGain.connect(ctx.destination);
        noise.start(ctx.currentTime + delay);
      }(i * 0.72, CHIME_FREQ[i % CHIME_FREQ.length]));
    }
  }

  /* ----------------------------------------------------------
     HAND ROTATION
  ---------------------------------------------------------- */
  /* [UI-010.d] setRot — rotate one hand around the small dial's center */
  function setRot(el, deg) {
    el.setAttribute('transform', 'rotate(' + deg.toFixed(3) + ',45,60)');
  }

  /* ----------------------------------------------------------
     CHIME FIRE
  ---------------------------------------------------------- */
  /* [UI-010.e] fireChime — one milestone crossing
     DOES:  plays the strikes, fades the message out/in with the new text, and
            retriggers the ring's chime animation by dropping/re-adding its class. */
  function fireChime(c) {
    playChime(c.count);

    elMsg.classList.remove('iw-timer--visible');
    setTimeout(function () {
      elMsg.textContent = c.message;
      elMsg.classList.add('iw-timer--visible');
    }, 300);

    elRing.classList.remove('iw-timer--chimed');
    /* Use setTimeout instead of offsetWidth read to avoid a forced reflow. */
    setTimeout(function () { elRing.classList.add('iw-timer--chimed'); }, 20);
  }

  /* ----------------------------------------------------------
     MAIN TICK
  ---------------------------------------------------------- */
  var startTime   = Date.now();
  var chimesFired = {};
  var chimes      = CHIMES[lang];

  function pad(n) { return n < 10 ? '0' + n : String(n); }

  /* [UI-010.f] tick — the 1s heartbeat
     DOES:  recomputes elapsed from Date.now() (never accumulates, so throttled
            background tabs stay correct), updates readout + hands, and fires each
            chime milestone exactly once via the chimesFired map. */
  function tick() {
    var elapsed = Math.floor((Date.now() - startTime) / 1000);
    var s = elapsed % 60;
    var m = Math.floor(elapsed / 60) % 60;
    var h = Math.floor(elapsed / 3600);

    elElapsed.textContent = h > 0
      ? pad(h) + ':' + pad(m) + ':' + pad(s)
      : pad(m) + ':' + pad(s);

    setRot(elSec,     s * 6);
    setRot(elSecTail, s * 6);
    setRot(elMin,     (m + s / 60) * 6);
    setRot(elHour,    ((h % 12) + m / 60) * 30);

    for (var i = 0; i < chimes.length; i++) {
      if (elapsed >= chimes[i].at && !chimesFired[chimes[i].at]) {
        chimesFired[chimes[i].at] = true;
        fireChime(chimes[i]);
      }
    }
  }

  tick();
  setInterval(tick, 1000);

}());
