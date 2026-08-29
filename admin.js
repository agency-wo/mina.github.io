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

  // [CFG-005.k] b64ToUtf8 — the inverse of btoa(unescape(encodeURIComponent(s)))
  // NOTES:  atob() alone hands back a byte string, so every non-ASCII character
  //         in watches.json returned mojibake and was then re-encoded that way.
  //         One publish would have rewritten Cortébert as CortÃ©bert and
  //         wrecked every Albanian and Italian description in the file. The
  //         write side was already correct, which is exactly why nobody saw it.
  function b64ToUtf8(b64){
    return decodeURIComponent(escape(atob(String(b64).replace(/\n/g, ''))));
  }

  // [CFG-005.l] ghGet — GET a repo file via the contents API (content + sha)
  function ghGet(token, path){
    return fetch(GH_API + path, {
      headers: { Authorization: 'token '+token, Accept: 'application/vnd.github.v3+json' }
    }).then(function(r){
      if(!r.ok) throw new Error('GitHub GET failed: '+r.status+' '+r.statusText);
      return r.json();
    });
  }

  // [CFG-005.m] ghPut — create or update a repo file via the contents API
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
  // [CFG-005.n] buildWatch — form data -> the watches.json record
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
  // [CFG-005.o] resetForm — clear everything back to the "add another" state
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
  // [CFG-005.p] the panel's read side: what is on the shelf, grouped by brand.
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

  // This field is PUBLIC (schema.org sku, the visible spec table and the customer's
  // WhatsApp message), and the box is offered at the exact moment the panel has just
  // said "record the sale", so a price typed here would ship to watch.al in three
  // languages within two minutes. But a code shape cannot simply be spelled out: real
  // references in this catalogue include DK 1.12576.2 (a SPACE) and 001808-COL02
  // (leading DIGITS), so rules like "no spaces" or "must start with a letter" reject
  // genuine data. Refuse the money shapes instead, and require at least one letter,
  // which every reference has and no price does. 40 matches the tracker's maxlength.
  var REF_OK = /^[A-Za-z0-9 .\/-]{1,40}$/;
  var REF_HAS_LETTER = /[A-Za-z]/;
  var REF_MONEY = /(^|[^A-Za-z])(eur|euro|lek|leke|usd|gbp|sold|shit|cmimi|price)([^A-Za-z]|$)/i;

  // [CFG-005.q] linkState — how each watch stands with the tracker, in five states.
  // DOES:   Returns {id: state} for EVERY watch, live and archived, where state is
  //         'noref' | 'dup' | 'unknown' | 'linked' | 'stale'.
  // WHY:    tools/sync_stock.py reconciles watches.json against the tracker, and for
  //         a linked watch the tracker wins. A boolean collapsed five different
  //         situations into "not governed", and the copy below has to tell them
  //         apart or it lies to the owner about whether a sale reached his books.
  // NOTES:  The rule must MATCH sync_stock.apply_stock or the two disagree about who
  //         owns a watch: reference in the feed AND unique among LIVE entries. The
  //         duplicate scan skips retired entries, mirroring [DB-006], so archiving a
  //         sold watch never blocks the restock that replaces it.
  //         'noref' and 'dup' are decidable from watches.json alone and are assigned
  //         EVEN WHEN THE FEED IS DOWN, so an outage does not blind the panel to the
  //         ten codeless watches. Only the last three need crmStock.
  //         NEVER returns null. Object.keys(null) throws inside renderStock, which is
  //         bound straight to the search box with no try/catch, so one slow feed would
  //         make every keystroke throw and freeze the list on "Loading".
  //         'stale' is the un-sell trap: sold here, but the tracker still counts one in
  //         stock, so the next reconcile flips it back on sale. See soldMsg.
  function linkState(list){
    var out = {}, seen = {}, dup = {};
    list.forEach(function(w){
      if(w.deleted) return;
      var r = String(w.reference || '').trim().toUpperCase();
      if(r) (seen[r] = seen[r] || []).push(w.id);
    });
    Object.keys(seen).forEach(function(r){ if(seen[r].length > 1) dup[r] = true; });
    list.forEach(function(w){
      var r = String(w.reference || '').trim().toUpperCase();
      if(!r){ out[w.id] = 'noref'; return; }
      if(dup[r]){ out[w.id] = 'dup'; return; }
      if(!crmStock) return;                 // feed down: cannot classify the rest, say nothing
      if(!Object.prototype.hasOwnProperty.call(crmStock, r)){ out[w.id] = 'unknown'; return; }
      out[w.id] = (w.sold && crmStock[r] > 0) ? 'stale' : 'linked';
    });
    return out;
  }

  // Kept so its two call sites do not change. Output stays what it always was:
  // live watches the tracker owns, and {} while the feed is unreachable.
  function crmGoverned(list){
    var st = linkState(list), out = {};
    list.forEach(function(w){
      if(w.deleted) return;
      if(st[w.id] === 'linked' || st[w.id] === 'stale') out[w.id] = true;
    });
    return out;
  }

  // One owner for the five phrasings, so the strip and the list cannot disagree
  // about what the panel is entitled to claim.
  function linkNote(w, state){
    // wrapped so a long-press selects the whole code when an in-app browser
    // refuses the clipboard API and the Copy button falls back to nothing
    var code = '<span class="stock-code">'
      + esc(String(w.reference || '').trim()) + '</span>';
    if(state === 'noref') return 'No code on this watch, so the tracker cannot match it.';
    if(state === 'dup') return 'Two watches here share the code ' + code
      + ', so the tracker cannot tell them apart.';
    if(state === 'unknown') return 'The tracker has no watch with the code ' + code + '.';
    if(state === 'stale') return 'The tracker still lists ' + code + ' as in stock, so the next '
      + 'sync will put this watch back on sale. Archive it here to stop that.';
    return '';
  }

  function refEditHtml(w){
    return '<span class="ref-add">'
      + '<input type="text" id="ref-' + esc(w.id) + '" maxlength="40" list="crm-codes" '
      + 'placeholder="Code, e.g. DK.1.12906-3">'
      + '<button type="button" data-act="setref" data-id="' + esc(w.id) + '">Save code</button>'
      + '</span>';
  }

  // navigator.clipboard needs a secure context, which watch.al has, but an in-app
  // browser can still refuse it. Falls back rather than hanging with the button
  // still saying "Copy code", which is what a missing .catch would do.
  function copyRef(text, btn){
    var label = btn.textContent;
    function done(ok){
      btn.textContent = ok ? 'Copied' : 'Copy failed';
      setTimeout(function(){ btn.textContent = label; }, 1600);
    }
    function fallback(){
      try{
        var ta = document.createElement('textarea');
        ta.value = text;
        ta.setAttribute('readonly', '');
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.select();
        var ok = document.execCommand('copy');
        document.body.removeChild(ta);
        done(ok);
      }catch(e){ done(false); }
    }
    if(navigator.clipboard && navigator.clipboard.writeText){
      navigator.clipboard.writeText(text).then(function(){ done(true); }, fallback);
    } else { fallback(); }
  }

  function alertRow(w, state){
    var code = String(w.reference || '').trim();
    return '<div class="stock-row"><div class="stock-meta">'
      + '<strong>' + esc(w.brand) + ' ' + esc(w.model) + '</strong>'
      + '<span class="stock-note">' + linkNote(w, state) + '</span></div>'
      + '<div class="stock-acts">'
      + (code ? '<button type="button" data-act="copyref" data-id="' + esc(w.id)
                + '">Copy code</button>' : '')
      + (w.deleted ? '' : '<button type="button" data-act="archive-sold" data-id="' + esc(w.id)
                          + '">Archive</button>')
      + (state === 'noref' ? refEditHtml(w) : '')
      + '</div></div>';
  }

  // [CFG-005.r] alertsHtml — sales the tracker cannot confirm.
  // NOTES:  Covers ARCHIVED watches too. Archiving is the correct first step, so if
  //         this list dropped a row on archive it would clear its own warning in one
  //         tap with the sale still missing from the books. The row leaves only when
  //         the tracker confirms it, which is state 'linked'.
  //         Empty today: nothing is sold.
  function alertsHtml(all, link){
    var rows = all.filter(function(w){
      var s = link[w.id];
      return w.sold && s && s !== 'linked';
    });
    if(!rows.length) return '';
    return '<div class="stock-alert">'
      + '<h4>Sold here, not recorded in the tracker</h4>'
      + '<p>You marked these sold on the site. The tracker cannot confirm the sale, so it will not '
      + 'reach Bilanci, the printed reports or the export. Archive each one here first, then add it '
      + 'in the tracker under Stoku i Oreve, Shto ore, and record what it sold for.</p>'
      + rows.map(function(w){ return alertRow(w, link[w.id]); }).join('')
      + '</div>';
  }

  // [CFG-005.s] unlinkedHtml — the standing worklist, collapsed.
  // NOTES:  The only surface that works whether or not Mark sold is ever pressed.
  //         Honours the search box, or filtering would hide the brand groups and
  //         leave all sixty rows here. Open state is restored by renderStock.
  function unlinkedHtml(live, link, q){
    var rows = live.filter(function(w){
      var s = link[w.id];
      if(!s || s === 'linked' || s === 'stale') return false;
      if(!q) return true;
      return (w.brand + ' ' + w.model + ' ' + (w.reference || '')).toLowerCase().indexOf(q) >= 0;
    });
    if(!rows.length) return '';
    var taken = {};
    live.forEach(function(w){
      var r = String(w.reference || '').trim().toUpperCase();
      if(r) taken[r] = true;
    });
    var free = crmStock ? Object.keys(crmStock).filter(function(r){ return !taken[r]; }).sort() : [];
    return '<details class="stock-group" id="unlinked-details">'
      + '<summary>Not linked to the tracker<span class="count">' + rows.length + '</span></summary>'
      + '<p class="form-hint">Marking one of these sold on this page records the sale nowhere else. '
      + 'Give the watch a code here, then add it in the tracker under Stoku i Oreve, Shto ore, with '
      + 'the same code in the Shifra / referenca box. It links itself on the next page load.</p>'
      + '<datalist id="crm-codes">'
      + free.map(function(r){ return '<option value="' + esc(r) + '">'; }).join('')
      + '</datalist>'
      + rows.map(function(w){ return alertRow(w, link[w.id]); }).join('')
      + '</details>';
  }

  // Never implies a sale reached the books when it did not, and always gives the
  // ORDER. Archiving first is what makes the sale survive: apply_stock skips retired
  // records in both its flip loop and its duplicate scan, so the tracker can never
  // undo them. Do it the other way round and adding the tracker row fires a full
  // reconcile that finds the code in stock and puts the watch back on sale.
  function soldMsg(id){
    var w = findWatch(id);
    if(!w) return 'Marked sold saved.';
    if(!crmStock) return 'Saved. I could not reach the tracker, so I cannot tell you whether this '
      + 'sale will reach your books. Check it in Stoku i Oreve.';
    var s = linkState(stockList || [])[id], code = String(w.reference || '').trim();
    if(s === 'linked' || s === 'stale') return 'Marked sold saved.';
    var why = s === 'noref'
      ? 'This watch has no code, so the tracker cannot match it'
      : s === 'dup'
        ? 'Two watches here share the code ' + code + ', so the tracker cannot tell which one sold'
        : 'The tracker has no watch with the code ' + code;
    return 'Saved. ' + why + ', so this sale will not reach Bilanci or the reports. Archive it here '
      + 'first, then add it in the tracker under Stoku i Oreve.';
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
    var link = linkState(stockList);
    var governed = crmGoverned(stockList);
    // Unreachable tracker is not an error, but the panel must not imply it checked.
    var note = crmStock ? '' : '<p class="form-hint">Could not reach the tracker just now, '
      + 'so rows it manages are not marked, and a sale marked now cannot be confirmed as '
      + 'recorded. A watch the tracker knows has its sold state set there, not here.</p>';
    // read the disclosure state before the rewrite, or the section snaps shut on every
    // keystroke and after every code saved
    var det = document.getElementById('unlinked-details');
    var wasOpen = !!(det && det.open);
    document.getElementById('stock-alerts').innerHTML = alertsHtml(stockList, link);
    document.getElementById('stock-groups').innerHTML = note + groupHtml(live, q, false, governed);
    document.getElementById('stock-unlinked').innerHTML = unlinkedHtml(live, link, q);
    document.getElementById('archive-groups').innerHTML = groupHtml(gone, q, true, governed);
    var reopened = document.getElementById('unlinked-details');
    if(reopened && (wasOpen || q)) reopened.open = true;
  }

  // [CFG-005.t] setFlag — the only write this panel makes to an existing record.
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
    if((key === 'sold' || key === 'reference') && crmGoverned(stockList || [])[id]){
      stockMsg('The tracker manages that watch. Mark it sold there and the site follows.');
      return;
    }
    if(key === 'reference'){
      var code = String(val || '').trim();
      if(!code){ stockMsg('Type a code first.'); return; }
      if(!REF_OK.test(code) || !REF_HAS_LETTER.test(code) || REF_MONEY.test(code)){
        stockMsg('That does not look like a code. Use the code from the watch tag, up to '
                 + '40 characters, letters and numbers with dots or dashes. This is not '
                 + 'where a price goes.');
        return;
      }
      var clash = null;
      (stockList || []).forEach(function(x){
        if(x.id !== id && !x.deleted
           && String(x.reference || '').trim().toUpperCase() === code.toUpperCase()) clash = x;
      });
      if(clash){
        stockMsg('That code is already on ' + clash.brand + ' ' + clash.model + '. Two '
                 + 'watches with the same code can never link, so give this one its own.');
        return;
      }
      val = code;
    }
    stockMsg('Saving\u2026');
    ghGet(token, 'watches.json').then(function(res){
      var arr = JSON.parse(b64ToUtf8(res.content)), w = null;
      for(var i = 0; i < arr.length; i++){ if(arr[i].id === id){ w = arr[i]; break; } }
      if(!w) throw new Error(id + ' is no longer in watches.json');
      if(key === 'sold'){ w.sold = !!val; }
      else if(key === 'reference'){ w.reference = val; }
      else if(val){ w.deleted = true; }
      else { delete w.deleted; }
      var body = btoa(unescape(encodeURIComponent(JSON.stringify(arr, null, 2))));
      return ghPut(token, 'watches.json', body,
                   label + ': ' + w.brand + ' ' + w.model, res.sha);
    }).then(function(){
      stockMsg(key === 'sold' && val ? soldMsg(id)
        : key === 'reference'
          ? 'Code saved. Add the same code in the tracker under Stoku i Oreve, Shto ore, in '
            + 'the Shifra / referenca box.'
          : label + ' saved. The site rebuilds itself; give it a minute or two.');
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
      } else if(act === 'archive-sold'){
        // its own confirm: archiving from the alert strip is about protecting a sale,
        // not about the restock story the ordinary Archive button tells
        if(!confirm('Archive ' + w.brand + ' ' + w.model + '?\n\nThis takes it off the shop '
                    + 'and protects the sale from being undone by the tracker sync. It stays '
                    + 'on this list until the tracker knows about the sale.')) return;
        setFlag(id, 'deleted', true, 'Archive');
      } else if(act === 'copyref'){
        copyRef(String(w.reference || '').trim(), btn);
      } else if(act === 'setref'){
        var inp = document.getElementById('ref-' + id);
        setFlag(id, 'reference', inp ? inp.value : '', 'Code');
      }
    });
    var searchEl = document.getElementById('stock-search');
    if(searchEl) searchEl.addEventListener('input', renderStock);
  }

})();
