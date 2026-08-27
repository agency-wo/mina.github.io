// [CFG-005] admin.js — password-gated panel that publishes a new watch to GitHub
// DOES:   gates the panel behind a SHA-256-checked password, keeps the GitHub token
//         AES-GCM-encrypted in localStorage (key derived from that password via
//         PBKDF2), and on submit uploads the photo then appends the watch to
//         watches.json through the GitHub contents API — the resulting push is what
//         triggers the live-site rebuild.
// IN:     panel form fields, a dropped/picked image file, a GitHub token (repo scope)
// OUT:    two commits on agency-wo/mina.github.io (image + watches.json); progress UI
// CALLS:  WebCrypto (PBKDF2 / AES-GCM / SHA-256), api.github.com
// NOTES:  the password hash only gates the UI — the token is the real credential.
//         The token is re-encrypted and saved only after a successful publish.
(function(){
  // Password is stored as SHA-256 hash — never compare plaintext in source
  var PW_HASH = 'e7b2b52f1b9d39adddf8fd2834458ad862aecf4bbca24d7248af4fd1e8f8a7aa';
  var REPO = 'agency-wo/mina.github.io';
  var GH_API = 'https://api.github.com/repos/' + REPO + '/contents/';

  var imageFile = null;   // File object
  var imageB64  = null;   // base64 string (no prefix)
  var imagePath = null;   // final path in repo e.g. images/watches/foo.jpg

  var sessionPassword = ''; // set on successful login, used to encrypt/decrypt token

  // Lek per euro. MIRRORS catalog_stats.LEK_RATE -- change both together;
  // verify-stats.py check C now fails the build if they disagree.
  var EUR_TO_LEK = 92.25;
  document.getElementById('f-price').addEventListener('input', function(){
    var price = parseFloat(this.value);
    var preview = document.getElementById('lek-preview');
    if(price > 0){
      preview.textContent = '≈ ' + (Math.round(price * EUR_TO_LEK / 100) * 100).toLocaleString() + ' L (Albanian Lek)';
      preview.style.display = 'block';
    } else {
      preview.style.display = 'none';
    }
  });

  // ── Crypto helpers ───────────────────────────────────────────────────────────
  // [CFG-005.a] deriveKey — password + salt -> AES-GCM key
  // DOES:   PBKDF2 (100k iterations, SHA-256) so the stored token blob is useless
  //         without the login password; key is non-extractable.
  function deriveKey(password, salt){
    return crypto.subtle.importKey(
      'raw', new TextEncoder().encode(password), 'PBKDF2', false, ['deriveKey']
    ).then(function(keyMaterial){
      return crypto.subtle.deriveKey(
        { name: 'PBKDF2', salt: salt, iterations: 100000, hash: 'SHA-256' },
        keyMaterial,
        { name: 'AES-GCM', length: 256 },
        false,
        ['encrypt', 'decrypt']
      );
    });
  }

  // [CFG-005.b] encryptToken — token -> {salt, iv, data} JSON, all base64
  // DOES:   fresh random salt + IV per encryption, so re-saving never reuses either.
  function encryptToken(token, password){
    var salt = crypto.getRandomValues(new Uint8Array(16));
    var iv   = crypto.getRandomValues(new Uint8Array(12));
    return deriveKey(password, salt).then(function(key){
      return crypto.subtle.encrypt(
        { name: 'AES-GCM', iv: iv },
        key,
        new TextEncoder().encode(token)
      ).then(function(ciphertext){
        return JSON.stringify({
          salt: btoa(String.fromCharCode.apply(null, salt)),
          iv:   btoa(String.fromCharCode.apply(null, iv)),
          data: btoa(String.fromCharCode.apply(null, new Uint8Array(ciphertext)))
        });
      });
    });
  }

  // [CFG-005.c] decryptToken — the inverse of encryptToken
  // OUT:    resolves to the plaintext token; rejects on wrong password or a
  //         corrupted blob (AES-GCM authenticates, so tampering also rejects).
  function decryptToken(storedJson, password){
    var stored = JSON.parse(storedJson);
    var salt = new Uint8Array(atob(stored.salt).split('').map(function(c){ return c.charCodeAt(0); }));
    var iv   = new Uint8Array(atob(stored.iv).split('').map(function(c){ return c.charCodeAt(0); }));
    var data = new Uint8Array(atob(stored.data).split('').map(function(c){ return c.charCodeAt(0); }));
    return deriveKey(password, salt).then(function(key){
      return crypto.subtle.decrypt({ name: 'AES-GCM', iv: iv }, key, data)
        .then(function(plaintext){
          return new TextDecoder().decode(plaintext);
        });
    });
  }

  // ── Gate ────────────────────────────────────────────────────────────────────
  var gateEl    = document.getElementById('gate');
  var panelEl   = document.getElementById('panel');
  var pwInput   = document.getElementById('pw-input');
  var gateError = document.getElementById('gate-error');

  // [CFG-005.d] sha256hex — string -> lowercase hex digest (for the gate check)
  function sha256hex(str){
    var buf = new TextEncoder().encode(str);
    return crypto.subtle.digest('SHA-256', buf).then(function(hash){
      return Array.from(new Uint8Array(hash)).map(function(b){ return b.toString(16).padStart(2,'0'); }).join('');
    });
  }

  // [CFG-005.e] tryLogin — the gate
  // DOES:   compares the hash of the typed password with PW_HASH; on a match keeps
  //         the plaintext in memory (needed later to decrypt/encrypt the token),
  //         reveals the panel and tries to restore a saved token.
  function tryLogin(){
    var pw = pwInput.value;
    sha256hex(pw).then(function(hash){
      if(hash === PW_HASH){
        sessionPassword = pw;
        gateEl.style.display = 'none';
        panelEl.style.display = 'block';
        loadSavedToken();
        loadStock();
      } else {
        gateError.textContent = 'Incorrect password. Try again.';
        pwInput.value = '';
        pwInput.focus();
      }
    });
  }

  // [CFG-005.f] loadSavedToken — restore the encrypted token from a past session
  // DOES:   decrypts with the session password and validates the token against
  //         GitHub before showing "connected"; a dead token or failed decryption
  //         clears storage so a stale credential can never look alive.
  function loadSavedToken(){
    var enc = localStorage.getItem('iglisi_gh_token_enc');
    if(!enc) return;

    decryptToken(enc, sessionPassword)
      .then(function(token){
        // Validate token is still alive before showing connected state
        return ghValidateToken(token).then(function(valid){
          if(valid){
            document.getElementById('gh-token').value = token;
            document.getElementById('token-connected-wrap').style.display = 'block';
            document.getElementById('token-setup-wrap').style.display = 'none';
          } else {
            localStorage.removeItem('iglisi_gh_token_enc');
            var note = document.getElementById('token-expired-note');
            if(note) note.style.display = 'block';
          }
        });
      })
      .catch(function(){
        // Decryption failed (wrong password or corrupted) — clear it
        localStorage.removeItem('iglisi_gh_token_enc');
      });
  }

  // [CFG-005.g] ghValidateToken — liveness probe: GET /user, true iff 2xx
  function ghValidateToken(token){
    return fetch('https://api.github.com/user', {
      headers: { Authorization: 'token ' + token, Accept: 'application/vnd.github.v3+json' }
    }).then(function(r){ return r.ok; }).catch(function(){ return false; });
  }

  document.getElementById('token-change-btn').addEventListener('click', function(){
    localStorage.removeItem('iglisi_gh_token_enc');
    document.getElementById('gh-token').value = '';
    document.getElementById('gh-token-visible').value = '';
    document.getElementById('token-connected-wrap').style.display = 'none';
    document.getElementById('token-setup-wrap').style.display = 'block';
  });
  document.getElementById('login-btn').addEventListener('click', tryLogin);
  pwInput.addEventListener('keydown', function(e){ if(e.key==='Enter') tryLogin(); });
  document.getElementById('logout-btn').addEventListener('click', function(){
    panelEl.style.display = 'none';
    gateEl.style.display = 'block';
    pwInput.value = '';
    gateError.textContent = '';
    sessionPassword = '';
    resetForm();
  });

  // ── GitHub token toggle ──────────────────────────────────────────────────────
  var ghTokenVisible = document.getElementById('gh-token-visible');
  var ghTokenEl      = document.getElementById('gh-token'); // hidden field holding actual value
  // Keep hidden field in sync with visible input
  ghTokenVisible.addEventListener('input', function(){ ghTokenEl.value = this.value.trim(); });
  document.getElementById('token-toggle').addEventListener('click', function(){
    var isHidden = ghTokenVisible.type === 'password';
    ghTokenVisible.type = isHidden ? 'text' : 'password';
    this.textContent = isHidden ? 'hide' : 'show';
  });

  // ── Image file picker ────────────────────────────────────────────────────────
  var fileInput    = document.getElementById('f-image-file');
  var uploadArea   = document.getElementById('upload-area');
  var previewWrap  = document.getElementById('image-preview-wrap');
  var previewImg   = document.getElementById('image-preview');
  var nameDisplay  = document.getElementById('image-name-display');
  var changeBtn    = document.getElementById('change-image-btn');

  fileInput.addEventListener('change', function(){
    if(this.files && this.files[0]) handleFile(this.files[0]);
  });
  uploadArea.addEventListener('dragover', function(e){ e.preventDefault(); this.classList.add('drag-over'); });
  uploadArea.addEventListener('dragleave', function(){ this.classList.remove('drag-over'); });
  uploadArea.addEventListener('drop', function(e){
    e.preventDefault(); this.classList.remove('drag-over');
    if(e.dataTransfer.files && e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
  });
  changeBtn.addEventListener('click', function(){
    imageFile = null; imageB64 = null; imagePath = null;
    fileInput.value = '';
    previewWrap.style.display = 'none';
    uploadArea.style.display = 'block';
  });

  // [CFG-005.h] handleFile — accept a photo from the picker or a drop
  // DOES:   enforces the 5 MB cap, reads the file as a data URL for both preview and
  //         base64 upload payload, and derives the repo filename from the current
  //         brand/model/reference fields.
  function handleFile(file){
    if(file.size > 5*1024*1024){ alert('Image is too large. Max 5 MB.'); return; }
    imageFile = file;
    var reader = new FileReader();
    reader.onload = function(ev){
      var dataUrl = ev.target.result;
      imageB64 = dataUrl.split(',')[1]; // strip data:...;base64,
      previewImg.src = dataUrl;
      var ext = file.name.split('.').pop().toLowerCase() || 'jpg';
      var generatedName = generateFilename(ext);
      imagePath = 'images/watches/' + generatedName;
      nameDisplay.textContent = generatedName;
      uploadArea.style.display = 'none';
      previewWrap.style.display = 'block';
    };
    reader.readAsDataURL(file);
  }

  // [CFG-005.i] generateFilename — brand-model-ref slug + original extension
  // DOES:   lowercases and hyphenates each part, dropping empties, so the image name
  //         stays readable in the repo and stable for a given watch.
  function generateFilename(ext){
    var brand = (document.getElementById('f-brand').value.trim() || 'watch').toLowerCase()
      .replace(/[^a-z0-9]+/g,'-').replace(/-+$/,'');
    var model = (document.getElementById('f-model').value.trim() || '').toLowerCase()
      .replace(/[^a-z0-9]+/g,'-').replace(/-+$/,'');
    var ref   = (document.getElementById('f-reference').value.trim() || '').toLowerCase()
      .replace(/[^a-z0-9]+/g,'-').replace(/-+$/,'');
    var parts = [brand, model, ref].filter(Boolean);
    return parts.join('-') + '.' + ext;
  }

  // Regenerate filename when brand/model/ref change (if image already picked)
  ['f-brand','f-model','f-reference'].forEach(function(id){
    document.getElementById(id).addEventListener('input', function(){
      if(!imageFile) return;
      var ext = imageFile.name.split('.').pop().toLowerCase() || 'jpg';
      var generatedName = generateFilename(ext);
      imagePath = 'images/watches/' + generatedName;
      nameDisplay.textContent = generatedName;
    });
  });

  // ── Form submit ──────────────────────────────────────────────────────────────
  document.getElementById('watch-form').addEventListener('submit', function(e){
    e.preventDefault();

    var brand     = document.getElementById('f-brand').value.trim();
    var model     = document.getElementById('f-model').value.trim();
    var reference = document.getElementById('f-reference').value.trim();
    var year      = parseInt(document.getElementById('f-year').value,10) || 2025;
    var price     = parseFloat(document.getElementById('f-price').value) || 0;
    var condition = document.getElementById('f-condition').value;
    var descEn    = document.getElementById('f-desc-en').value.trim();
    var descIt    = document.getElementById('f-desc-it').value.trim();
    var descSq    = document.getElementById('f-desc-sq').value.trim();
    var sold      = document.getElementById('f-sold').checked;
    var token     = document.getElementById('gh-token').value.trim();

    if(!brand || !model || !price || !descEn){
      alert('Please fill in Brand, Model name, Price and Description (marked *).');
      return;
    }
    if(!imageFile || !imageB64){
      alert('Please select a photo of the watch.');
      return;
    }

    var addBtn = document.getElementById('add-btn');
    addBtn.disabled = true;

    if(token){
      publishViaGitHub(token, {brand:brand,model:model,reference:reference,year:year,price:price,condition:condition,descEn:descEn,descIt:descIt,descSq:descSq,sold:sold}, function(){
        addBtn.disabled = false;
      });
    } else {
      var statusEl = document.getElementById('submit-status');
      statusEl.style.display = 'block';
      statusEl.className = 'error';
      statusEl.textContent = 'Not connected to GitHub. Please contact your admin to set up the connection.';
      addBtn.disabled = false;
    }
  });

  // ── GitHub publish flow ──────────────────────────────────────────────────────
  // [CFG-005.j] publishViaGitHub — the whole publish pipeline, with progress UI
  // DOES:   1) PUT the image, 2) GET watches.json + append the new watch, 3) PUT it
  //         back with its sha (optimistic-lock against concurrent edits); on success
  //         re-encrypts and saves the token and resets the form.
  // IN:     token; data — the validated form fields; done — always-called finisher
  // OUT:    two commits, step-by-step status dots, or an error panel on any failure
  function publishViaGitHub(token, data, done){
    var statusEl = document.getElementById('submit-status');
    statusEl.style.display = 'block';
    statusEl.className = 'info';

    function step(id, state, text){
      var el = document.getElementById('step-'+id);
      if(!el) return;
      el.querySelector('.step-dot').className = 'step-dot '+state;
      el.querySelector('span').textContent = text;
    }

    statusEl.innerHTML =
      '<div class="progress-step" id="step-img"><span class="step-dot pending"></span><span>Uploading image\u2026</span></div>' +
      '<div class="progress-step" id="step-json"><span class="step-dot pending"></span><span>Updating watches.json\u2026</span></div>' +
      '<div class="progress-step" id="step-done"><span class="step-dot pending"></span><span>Waiting\u2026</span></div>';

    step('img','active','Uploading image\u2026');

    // 1. Upload image
    ghPut(token, imagePath, imageB64, 'Add watch image: '+imagePath, null)
      .then(function(){
        step('img','done','Image uploaded \u2713');
        step('json','active','Updating watches.json\u2026');
        // 2. Fetch current watches.json
        return ghGet(token, 'watches.json');
      })
      .then(function(res){
        var currentArr = JSON.parse(b64ToUtf8(res.content.replace(/\n/g,'')));
        var newWatch = buildWatch(currentArr, data);
        currentArr.push(newWatch);
        var newContent = btoa(unescape(encodeURIComponent(JSON.stringify(currentArr, null, 2))));
        return ghPut(token, 'watches.json', newContent, 'Add watch: '+data.brand+' '+data.model, res.sha);
      })
      .then(function(){
        step('json','done','watches.json updated \u2713');
        step('done','done','All done \u2014 watch is live!');
        statusEl.className = 'success';
        // Encrypt and save token for next session
        if(sessionPassword){
          encryptToken(token, sessionPassword).then(function(enc){
            localStorage.setItem('iglisi_gh_token_enc', enc);
          });
        }
        // Show connected state for next time
        document.getElementById('token-connected-wrap').style.display = 'block';
        document.getElementById('token-setup-wrap').style.display = 'none';
        resetForm();
        done();
      })
      .catch(function(err){
        statusEl.className = 'error';
        statusEl.innerHTML = '<strong>Error:</strong> ' + err.message + '<br><small>Check your GitHub token has repo scope and try again.</small>';
        done();
      });
  }

  // [CFG-005.n] b64ToUtf8 — the inverse of btoa(unescape(encodeURIComponent(s)))
  // NOTES:  atob() alone hands back a byte string, so every non-ASCII character
  //         in watches.json returned mojibake and was then re-encoded that way.
  //         One publish would have rewritten Cortébert as CortÃ©bert and
  //         wrecked every Albanian and Italian description in the file. The
  //         write side was already correct, which is exactly why nobody saw it.
  function b64ToUtf8(b64){
    return decodeURIComponent(escape(atob(String(b64).replace(/\n/g, ''))));
  }

  // [CFG-005.k] ghGet — GET a repo file via the contents API (content + sha)
  function ghGet(token, path){
    return fetch(GH_API + path, {
      headers: { Authorization: 'token '+token, Accept: 'application/vnd.github.v3+json' }
    }).then(function(r){
      if(!r.ok) throw new Error('GitHub GET failed: '+r.status+' '+r.statusText);
      return r.json();
    });
  }

  // [CFG-005.l] ghPut — create or update a repo file via the contents API
  // NOTES:  sha present = update (required by GitHub), absent = create; the error
  //         path surfaces GitHub's response body because "409" alone is useless.
  function ghPut(token, path, contentB64, message, sha){
    var body = { message: message, content: contentB64 };
    if(sha) body.sha = sha;
    return fetch(GH_API + path, {
      method: 'PUT',
      headers: { Authorization: 'token '+token, Accept: 'application/vnd.github.v3+json', 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    }).then(function(r){
      if(!r.ok) return r.text().then(function(t){ throw new Error('GitHub PUT failed ('+r.status+'): '+t); });
      return r.json();
    });
  }

  // ── Build watch object ───────────────────────────────────────────────────────
  // [CFG-005.m] buildWatch — form data -> the watches.json record
  // DOES:   ids continue the watch-N sequence from the array length; optional fields
  //         (reference, it/sq descriptions) are omitted rather than written empty.
  function buildWatch(arr, data){
    var w = {
      id: 'watch-'+(arr.length+1),
      brand: data.brand,
      model: data.model,
      year: data.year,
      condition: data.condition,
      price: data.price,
      currency: 'EUR',
      image: '/'+imagePath,
      sold: data.sold,
      description_en: data.descEn
    };
    if(data.reference) w.reference = data.reference;
    if(data.descIt)    w.description_it = data.descIt;
    if(data.descSq)    w.description_sq = data.descSq;
    return w;
  }

  // ── Reset ────────────────────────────────────────────────────────────────────
  // [CFG-005.n] resetForm — clear everything back to the "add another" state
  function resetForm(){
    document.getElementById('watch-form').reset();
    document.getElementById('f-year').value = '2025';
    document.getElementById('f-condition').value = 'New';
    imageFile = null; imageB64 = null; imagePath = null;
    document.getElementById('image-preview-wrap').style.display = 'none';
    document.getElementById('upload-area').style.display = 'block';
    document.getElementById('f-image-file').value = '';
  }

  // ── Copy button ──────────────────────────────────────────────────────────────
  document.getElementById('copy-btn').addEventListener('click', function(){
    var ta = document.getElementById('json-output');
    ta.select();
    var btn = document.getElementById('copy-btn');
    var note = document.getElementById('copy-success');
    if(navigator.clipboard && navigator.clipboard.writeText){
      navigator.clipboard.writeText(ta.value).then(function(){
        btn.textContent = 'Copied \u2713'; note.style.display = 'block';
        setTimeout(function(){ btn.textContent = 'Copy to clipboard'; note.style.display = 'none'; }, 2000);
      });
    } else {
      document.execCommand('copy');
      btn.textContent = 'Copied \u2713'; note.style.display = 'block';
      setTimeout(function(){ btn.textContent = 'Copy to clipboard'; note.style.display = 'none'; }, 2000);
    }
  });

  // ── Stock list ───────────────────────────────────────────────────────────────
  // [CFG-005.o] the panel's read side: what is on the shelf, grouped by brand.
  // NOTES:  archive/restore only set and clear the `deleted` flag. Every generator
  //         already honours it (gen_shop_index drops it from the grid and ItemList,
  //         gen_product_pages turns its page into a noindex stub, catalog_stats and
  //         shop_seo drop it from every number, all three shop.js filter it), which
  //         is why this is a flag write and not a subsystem.
  var stockList = null;
  var crmStock = null;
  // The CRM's one public route, read-only and credential-free ([API-001]).
  var CRM_FEED = 'https://api.watch.al/public/stock';

  function currentToken(){
    var el = document.getElementById('gh-token');
    return el ? el.value.trim() : '';
  }
  function stockMsg(s){
    var el = document.getElementById('stock-status');
    if(el) el.textContent = s || '';
  }
  function esc(s){
    return String(s == null ? '' : s).replace(/[&<>"]/g, function(c){
      return { '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;' }[c];
    });
  }

  // Reads through the API when a token is present, because that is repo HEAD and
  // therefore what a write will be based on. Without a token it falls back to the
  // deployed file, which is fine for looking but may lag by a rebuild.
  function loadStock(){
    var token = currentToken();
    var p = token
      ? ghGet(token, 'watches.json').then(function(res){ return JSON.parse(b64ToUtf8(res.content)); })
      : fetch('/watches.json', { cache: 'no-store' }).then(function(r){ return r.json(); });
    return Promise.all([p, loadCrm()]).then(function(r){
      stockList = r[0];
      renderStock();
    }).catch(function(err){
      stockMsg('Could not load the stock list: ' + err.message);
    });
  }

  // [CFG-005.q] crmGoverned — which watches the CRM, not this panel, owns.
  // DOES:   Returns {id:true} for every LIVE watch whose reference the CRM feed
  //         publishes, using apply_stock's exact linking rule.
  // WHY:    tools/sync_stock.py reconciles watches.json against the CRM every
  //         night at 05:17 UTC, and for a linked watch the CRM wins: it flips
  //         `sold` back and the owner's click disappears overnight with nothing
  //         on screen to explain it. Rather than let the panel lose that race, it
  //         does not offer the control. Sell it in the CRM and the site follows
  //         by itself, which is the direction that already works.
  // NOTES:  The rule must MATCH sync_stock.apply_stock or the two disagree about
  //         who owns a watch: reference present in the feed AND unique among LIVE
  //         entries. A retired entry's reference is excluded on both sides, so
  //         archiving a sold watch never blocks the restock that replaces it.
  //         Archive/Restore stay on every row: apply_stock skips retired records,
  //         so the CRM can never undo them.
  //         The feed is public, credential-free and CORS *, so the browser reads
  //         it directly. Unreachable is not an error here, it just means the
  //         panel cannot prove ownership and says so.
  function crmGoverned(list){
    var out = {}, seen = {};
    if(!crmStock) return out;
    list.forEach(function(w){
      if(w.deleted) return;
      var r = String(w.reference || '').trim().toUpperCase();
      if(r) (seen[r] = seen[r] || []).push(w.id);
    });
    Object.keys(seen).forEach(function(r){
      if(seen[r].length === 1 && Object.prototype.hasOwnProperty.call(crmStock, r)){
        out[seen[r][0]] = true;
      }
    });
    return out;
  }

  // Never lets a slow CRM hold up the stock list. The feed only decides which
  // rows are badged, so timing out degrades to 'could not check' and the panel
  // still works; without this a hung request meant the list never rendered at
  // all, because fetch() has no timeout of its own and Promise.all waits for it.
  // Resolves, never rejects: an unreachable CRM is an expected state here.
  function loadCrm(){
    return new Promise(function(resolve){
      var done = false;
      function finish(stock){
        if(done) return;
        done = true; clearTimeout(timer); crmStock = stock; resolve();
      }
      var timer = setTimeout(function(){ finish(null); }, 6000);
      fetch(CRM_FEED, { cache: 'no-store' })
        .then(function(r){ return r.ok ? r.json() : null; })
        .then(function(d){ finish((d && d.stock) || null); })
        .catch(function(){ finish(null); });
    });
  }

  function rowHtml(w, archived, governed){
    var img   = w.image ? '<img src="' + esc(w.image) + '" alt="" loading="lazy">' : '';
    var price = w.price ? '\u20ac' + w.price : 'Price on request';
    var sold  = w.sold ? ' <span class="tag-sold">Sold</span>' : '';
    var soldBtn = governed
      ? '<span class="tag-crm" title="This watch is linked to the CRM by its reference. '
        + 'Mark it sold there and the site follows within a day. A change made here '
        + 'would be reverted by the nightly sync.">CRM-managed</span>'
      : '<button type="button" data-act="sold" data-id="' + esc(w.id) + '">'
        + (w.sold ? 'Back in stock' : 'Mark sold') + '</button>';
    var acts  = archived
      ? '<button type="button" data-act="restore" data-id="' + esc(w.id) + '">Bring back</button>'
      : soldBtn + '<button type="button" data-act="archive" data-id="' + esc(w.id) + '">Archive</button>';
    return '<div class="stock-row">' + img
      + '<div class="stock-meta"><strong>' + esc(w.brand) + ' ' + esc(w.model) + '</strong>' + sold
      + '<span>' + esc(w.reference || 'no reference') + ' \u00b7 ' + price + '</span></div>'
      + '<div class="stock-acts">' + acts + '</div></div>';
  }

  // Biggest brand first: the point of the grouping is that the longest list is the
  // one you most want collapsed by default.
  function groupHtml(list, q, archived, governed){
    var by = {}, n = 0;
    list.forEach(function(w){
      var hay = (w.brand + ' ' + w.model + ' ' + (w.reference || '')).toLowerCase();
      if(q && hay.indexOf(q) < 0) return;
      (by[w.brand] = by[w.brand] || []).push(w);
      n++;
    });
    if(!n) return '<p class="form-hint">' + (q ? 'Nothing matches that.' : 'Nothing here.') + '</p>';
    return Object.keys(by).sort(function(a, b){
      return by[b].length - by[a].length || a.localeCompare(b);
    }).map(function(brand){
      return '<details class="stock-group"' + (q ? ' open' : '') + '><summary>'
        + esc(brand) + '<span class="count">' + by[brand].length + '</span></summary>'
        + by[brand].map(function(w){ return rowHtml(w, archived, governed && governed[w.id]); }).join('')
        + '</details>';
    }).join('');
  }

  function renderStock(){
    if(!stockList) return;
    var sEl = document.getElementById('stock-search');
    var q = (sEl && sEl.value || '').trim().toLowerCase();
    var live = [], gone = [];
    stockList.forEach(function(w){ (w.deleted ? gone : live).push(w); });
    var governed = crmGoverned(stockList);
    // Unreachable CRM is not an error, but the panel must not imply it checked.
    var note = crmStock ? '' : '<p class="form-hint">Could not reach the CRM just now, '
      + 'so rows it manages are not marked. A watch the CRM tracks has its sold state '
      + 'set there, not here.</p>';
    document.getElementById('stock-groups').innerHTML = note + groupHtml(live, q, false, governed);
    document.getElementById('archive-groups').innerHTML = groupHtml(gone, q, true, governed);
  }

  // [CFG-005.p] setFlag — the only write this panel makes to an existing record.
  // NOTES:  re-reads watches.json immediately before writing so the sha is current
  //         and a stale tab cannot clobber a change made elsewhere; GitHub rejects a
  //         stale sha rather than silently overwriting.
  //         `sold` exists on every record, so it is set. `deleted` exists on none, so
  //         it is added and then removed, which keeps watches.json free of
  //         "deleted": false noise.
  function setFlag(id, key, val, label){
    var token = currentToken();
    if(!token){ stockMsg('Connect a GitHub token first \u2014 see GitHub Connection above.'); return; }
    // A stale tab can still be showing a Sold button for a watch the CRM has
    // since taken over. Writing it would be undone by the next reconcile.
    if(key === 'sold' && crmGoverned(stockList || [])[id]){
      stockMsg('The CRM manages that watch. Mark it sold there and the site follows.');
      return;
    }
    stockMsg('Saving\u2026');
    ghGet(token, 'watches.json').then(function(res){
      var arr = JSON.parse(b64ToUtf8(res.content)), w = null;
      for(var i = 0; i < arr.length; i++){ if(arr[i].id === id){ w = arr[i]; break; } }
      if(!w) throw new Error(id + ' is no longer in watches.json');
      if(key === 'sold'){ w.sold = !!val; }
      else if(val){ w.deleted = true; }
      else { delete w.deleted; }
      var body = btoa(unescape(encodeURIComponent(JSON.stringify(arr, null, 2))));
      return ghPut(token, 'watches.json', body,
                   label + ': ' + w.brand + ' ' + w.model, res.sha);
    }).then(function(){
      stockMsg(label + ' saved. The site rebuilds itself; give it a minute or two.');
      return loadStock();
    }).catch(function(err){
      stockMsg('Failed: ' + err.message);
    });
  }

  function findWatch(id){
    for(var i = 0; stockList && i < stockList.length; i++){
      if(stockList[i].id === id) return stockList[i];
    }
    return null;
  }

  var stockCard = document.getElementById('stock-card');
  if(stockCard){
    stockCard.addEventListener('click', function(e){
      var btn = e.target && e.target.closest ? e.target.closest('button[data-act]') : null;
      if(!btn) return;
      var id = btn.getAttribute('data-id'), act = btn.getAttribute('data-act');
      var w = findWatch(id);
      if(!w) return;
      if(act === 'sold'){
        setFlag(id, 'sold', !w.sold, w.sold ? 'Back in stock' : 'Marked sold');
      } else if(act === 'archive'){
        if(!confirm('Archive ' + w.brand + ' ' + w.model + '?\n\nIt leaves the shop but keeps its '
                    + 'record, so you can bring it back when the same piece comes in.')) return;
        setFlag(id, 'deleted', true, 'Archive');
      } else if(act === 'restore'){
        setFlag(id, 'deleted', false, 'Restore');
      }
    });
    var searchEl = document.getElementById('stock-search');
    if(searchEl) searchEl.addEventListener('input', renderStock);
  }

})();
