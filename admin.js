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

  var EUR_TO_LEK = 97;
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
        var currentArr = JSON.parse(atob(res.content.replace(/\n/g,'')));
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

})();
