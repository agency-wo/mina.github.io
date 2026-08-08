// [SEC-003] tt-policy.js — Trusted Types default policy shim
// DOES:   registers a pass-through 'default' policy so browsers enforcing a
//         require-trusted-types-for CSP keep the site's legacy innerHTML/script
//         sinks working instead of throwing.
// OUT:    a permissive trustedTypes 'default' policy; nothing else
// NOTES:  intentionally NOT a sanitizer — it restores pre-TT behavior verbatim.
//         try/catch because registering 'default' twice throws.
try{if(window.trustedTypes&&trustedTypes.createPolicy)trustedTypes.createPolicy('default',{createHTML:function(s){return s;},createScript:function(s){return s;},createScriptURL:function(s){return s;}});}catch(e){}
