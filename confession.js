// [UI-011] confession.js — the watch "confession booth": seeded feed + anonymous posts
// DOES:   renders a per-language feed of seeded confessions, lets a visitor add one
//         (localStorage only — nothing ever leaves the browser), enforces a 30s
//         cooldown, and re-ages visitor timestamps every minute.
// IN:     iwConfession* DOM ids; <html lang> picks the seed set, strings, storage key
// OUT:    DOM feed rebuilds; localStorage under STR[lang].key (last 20 visitor posts)
// NOTES:  seeds always precede stored visitor posts and the feed shows the last 8;
//         a "new" post animates in immediately while the rest stagger.
/*!
 * Iglisi Watch — Confession Booth  v1.0
 * Language-aware. No backend. localStorage for visitor submissions.
 */
(function () {
  'use strict';

  var scrollEl  = document.getElementById('iwConfessionScroll');
  var input     = document.getElementById('iwConfessionInput');
  var countEl   = document.getElementById('iwConfessionCount');
  var submitBtn = document.getElementById('iwConfessionSubmit');
  if (!scrollEl || !input || !submitBtn) return;

  /* ----------------------------------------------------------
     LANGUAGE DETECTION
  ---------------------------------------------------------- */
  var lang = (document.documentElement.lang || 'en').toLowerCase().slice(0, 2);
  if (lang !== 'it' && lang !== 'sq') lang = 'en';

  /* ----------------------------------------------------------
     STRINGS PER LANGUAGE
  ---------------------------------------------------------- */
  var STR = {
    en: {
      key:    'iw_confessions_en_v1',
      submit: 'Confess \u2192',
      sent:   'Sent \u2713',
      wait:   function (s) { return 'Wait ' + s + 's'; }
    },
    it: {
      key:    'iw_confessions_it_v1',
      submit: 'Confessa \u2192',
      sent:   'Inviato \u2713',
      wait:   function (s) { return 'Attendi ' + s + 's'; }
    },
    sq: {
      key:    'iw_confessions_sq_v1',
      submit: 'Rrëfe \u2192',
      sent:   'Dërguar \u2713',
      wait:   function (s) { return 'Prit ' + s + 's'; }
    }
  };
  var S = STR[lang];

  /* ----------------------------------------------------------
     SEED DATA
  ---------------------------------------------------------- */
  var SEEDS = {
    en: [
      { text: '"Mine stopped in 2019. I told myself it just needed a battery. It is now 2025."',                                    ago: '2m ago'  },
      { text: '"Inherited my grandfather\'s Omega. It hasn\'t moved from the box in four years. I\'m ashamed."',                   ago: '7m ago'  },
      { text: '"The crystal cracked on holiday. I put clear nail varnish over it. It\'s been there two years."',                   ago: '14m ago' },
      { text: '"I wore it in the shower once. Just once. It never forgave me."',                                                   ago: '23m ago' },
      { text: '"Still wearing it even though it runs 11 minutes fast. I just do the mental arithmetic."',                          ago: '38m ago' },
      { text: '"The strap snapped. I put it in a drawer meaning to fix it. Found it there three years later while moving house."', ago: '1h ago'  },
      { text: '"Overwound it trying to be careful. Heard a quiet snap. Have not touched it since."',                               ago: '2h ago'  },
      { text: '"My husband bought me a beautiful watch. I\'ve worn it twice in five years. I am the problem."',                    ago: '3h ago'  },
      { text: '"Dropped it on tile. The hands went crooked. Every morning I pretend they are not."',                               ago: '5h ago'  },
      { text: '"It belonged to my father. I keep meaning to restore it for his birthday. I have missed six of them."',             ago: '8h ago'  }
    ],
    it: [
      { text: '"Si è fermata nel 2019. Mi sono detto che bastava la batteria. Siamo nel 2025."',                                   ago: '2m fa'  },
      { text: '"Ho ereditato l\'Omega di mio nonno. Non l\'ho mai toccata dalla scatola da quattro anni. Ho vergogna."',          ago: '7m fa'  },
      { text: '"Il vetro si è crepato in vacanza. Ho messo lo smalto trasparente. Sono passati due anni."',                       ago: '14m fa' },
      { text: '"L\'ho indossata sotto la doccia una volta. Solo una. Non me l\'ha mai perdonata."',                               ago: '23m fa' },
      { text: '"Va avanti di 11 minuti. La indosso lo stesso. Faccio il calcolo ogni mattina."',                                  ago: '38m fa' },
      { text: '"Il cinturino si è rotto. L\'ho messa in un cassetto. L\'ho trovata tre anni dopo durante il trasloco."',          ago: '1h fa'  },
      { text: '"L\'ho caricata troppo cercando di stare attento. Ho sentito uno schiocco silenzioso. Non la tocco più."',         ago: '2h fa'  },
      { text: '"Mio marito mi ha regalato un orologio bellissimo. L\'ho indossato due volte in cinque anni. Il problema sono io."', ago: '3h fa'  },
      { text: '"Mi è caduta sul pavimento. Le lancette si sono storte. Ogni mattina faccio finta di niente."',                   ago: '5h fa'  },
      { text: '"Era di mio padre. Volevo restaurarla per il suo compleanno. Ne ho mancati sei."',                                 ago: '8h fa'  }
    ],
    sq: [
      { text: '"U ndal në 2019. I thashë vetes se i duhej vetëm bateria. Tani është 2025."',                                     ago: '2m më parë'  },
      { text: '"Trashëgova Omega-n e gjyshit tim. Nuk ka lëvizur nga kutia katër vjet. Turp kam."',                              ago: '7m më parë'  },
      { text: '"Xhami u ça në pushime. Vura llak transparent mbi të. Kanë kaluar dy vjet."',                                     ago: '14m më parë' },
      { text: '"E vura nën dush njëherë. Vetëm njëherë. Nuk m\'u fal kurrë."',                                                  ago: '23m më parë' },
      { text: '"Shkon 11 minuta para. E vesh akoma. I bëj llogaritjen çdo mëngjes."',                                            ago: '38m më parë' },
      { text: '"Rripi u këput. E futa në sirtar. E gjeta tre vjet më vonë gjatë shpërnguljes."',                                 ago: '1h më parë'  },
      { text: '"E çilova duke u kujdesur. Dëgjova një kërcitje të lehtë. Nuk e kam prekur që atëherë."',                        ago: '2h më parë'  },
      { text: '"Burri im më bleu një orë të bukur. E kam veshur dy herë në pesë vjet. Problemi jam unë."',                       ago: '3h më parë'  },
      { text: '"Më ra mbi pllakë. Duart u kthyen të shtrembëra. Çdo mëngjes sillhem sikur nuk është kështu."',                  ago: '5h më parë'  },
      { text: '"Ishte e babait tim. Doja ta restauroja. Kam humbur gjashtë ditëlindje të tija."',                                ago: '8h më parë'  }
    ]
  };

  /* ----------------------------------------------------------
     CONFIG
  ---------------------------------------------------------- */
  var MAX_CHAR    = 120;
  var COOLDOWN    = 30000;
  var MAX_STORED  = 40;

  /* ----------------------------------------------------------
     STATE
  ---------------------------------------------------------- */
  var confessions = [];
  var lastSubmit  = 0;

  /* ----------------------------------------------------------
     LOAD
  ---------------------------------------------------------- */
  // [UI-011.a] load — seeds + surviving visitor posts into memory
  // DOES:   parses the stored visitor list (corrupt/absent -> empty) and appends it
  //         after the seeds, capped to the newest MAX_STORED overall.
  function load() {
    var stored = [];
    try { stored = JSON.parse(localStorage.getItem(S.key) || '[]'); } catch (e) {}
    confessions = SEEDS[lang].concat(stored).slice(-MAX_STORED);
  }

  /* ----------------------------------------------------------
     SAVE
  ---------------------------------------------------------- */
  // [UI-011.b] save — persist ONLY visitor posts (seeds are code, not data)
  // DOES:   writes the newest 20 visitor entries; storage failures are silently
  //         ignored (private mode / quota), the feed just becomes session-only.
  function save() {
    var visitor = confessions.filter(function (c) { return c.visitor; });
    try { localStorage.setItem(S.key, JSON.stringify(visitor.slice(-20))); } catch (e) {}
  }

  /* ----------------------------------------------------------
     FORMAT
  ---------------------------------------------------------- */
  // [UI-011.c] formatText — every confession reads as a quotation
  // DOES:   wraps the text in curly quotes unless the visitor already typed them.
  function formatText(t) {
    t = t.trim();
    if (t.charAt(0) !== '\u201C') t = '\u201C' + t;
    if (t.charAt(t.length - 1) !== '\u201D') t = t + '\u201D';
    return t;
  }

  /* ----------------------------------------------------------
     RENDER
  ---------------------------------------------------------- */
  // [UI-011.d] render — full rebuild of the visible feed
  // DOES:   clears and re-creates the last 8 items via createElement/textContent
  //         (Trusted-Types safe), staggers their entrance, then scrolls the feed to
  //         the newest entry.
  function render() {
    while (scrollEl.firstChild) scrollEl.removeChild(scrollEl.firstChild);

    var visible = confessions.slice(-8);
    for (var i = 0; i < visible.length; i++) {
      (function (c, idx) {
        var el = document.createElement('div');
        el.className = 'iw-confession__item' + (c.isNew ? ' iw-new' : '');

        var textEl = document.createElement('div');
        textEl.className = 'iw-confession__text';
        textEl.textContent = formatText(c.text);

        var metaEl = document.createElement('div');
        metaEl.className = 'iw-confession__meta';
        metaEl.textContent = 'Anonymous \u00B7 ' + c.ago;

        el.appendChild(textEl);
        el.appendChild(metaEl);
        scrollEl.appendChild(el);

        var delay = c.isNew ? 0 : idx * 60;
        setTimeout(function () { el.classList.add('iw-visible'); }, delay + 30);
      }(visible[i], i));
    }

    /* Scroll feed to bottom */
    setTimeout(function () {
      var feed = document.querySelector('.iw-confession__feed');
      if (feed) feed.scrollTop = feed.scrollHeight;
    }, 100);
  }

  /* ----------------------------------------------------------
     CHARACTER COUNT
  ---------------------------------------------------------- */
  input.addEventListener('input', function () {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 100) + 'px';
    var remaining = MAX_CHAR - this.value.length;
    countEl.textContent = remaining;
    countEl.className = 'iw-confession__count' + (remaining < 20 ? ' iw-near-limit' : '');
  });

  /* ----------------------------------------------------------
     SHAKE
  ---------------------------------------------------------- */
  // [UI-011.e] shake — rejection feedback for a too-short confession
  // DOES:   a decaying left-right wobble via transform; no text, the motion is the
  //         message.
  function shake(el) {
    var steps = [4, -4, 3, -3, 2, -2, 0], i = 0;
    function step() {
      if (i >= steps.length) { el.style.transform = ''; return; }
      el.style.transform = 'translateX(' + steps[i] + 'px)';
      i++;
      setTimeout(step, 50);
    }
    el.style.transition = 'transform 0.08s ease';
    step();
  }

  /* ----------------------------------------------------------
     SUBMIT
  ---------------------------------------------------------- */
  // [UI-011.f] submit — validate, rate-limit, append, persist
  // DOES:   rejects entries under 8 chars (shake), enforces the 30s cooldown with a
  //         localized countdown label, appends the post as the single "new" item,
  //         saves, re-renders and resets the composer.
  function submit() {
    var val = input.value.trim();
    if (!val || val.length < 8) { shake(input); return; }

    var now = Date.now();
    if (now - lastSubmit < COOLDOWN) {
      var wait = Math.ceil((COOLDOWN - (now - lastSubmit)) / 1000);
      submitBtn.textContent = S.wait(wait);
      submitBtn.classList.add('iw-cooldown');
      submitBtn.disabled = true;
      return;
    }
    lastSubmit = now;

    confessions.forEach(function (c) { c.isNew = false; });
    confessions.push({ text: val, ago: 'just now', isNew: true, visitor: true, _ts: now });
    if (confessions.length > MAX_STORED) confessions = confessions.slice(-MAX_STORED);

    save();
    render();

    input.value = '';
    input.style.height = 'auto';
    countEl.textContent = MAX_CHAR;

    submitBtn.textContent = S.sent;
    submitBtn.disabled = true;
    setTimeout(function () {
      submitBtn.textContent = S.submit;
      submitBtn.disabled = false;
      submitBtn.classList.remove('iw-cooldown');
    }, COOLDOWN);
  }

  submitBtn.addEventListener('click', submit);
  input.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submit(); }
  });

  /* ----------------------------------------------------------
     AUTO-AGE (update timestamps every 60s)
  ---------------------------------------------------------- */
  setInterval(function () {
    var now = Date.now();
    confessions.forEach(function (c) {
      if (!c.visitor || !c._ts) return;
      var diff = Math.floor((now - c._ts) / 60000);
      if (diff < 1)       c.ago = 'just now';
      else if (diff < 60) c.ago = diff + 'm ago';
      else                c.ago = Math.floor(diff / 60) + 'h ago';
    });
    render();
  }, 60000);

  /* ----------------------------------------------------------
     INIT
  ---------------------------------------------------------- */
  load();
  render();

}());
