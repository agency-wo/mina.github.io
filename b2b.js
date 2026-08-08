// [UI-007] b2b.js — B2B enquiry post-submit state
// DOES:   when the form provider redirects back with ?success=1, hides the form wrap
//         and reveals the success panel. On a normal visit it does nothing at all.
// IN:     location.search; #b2b-form-wrap / #b2b-success
// OUT:    display toggles only
(function(){
  if(location.search.indexOf('success=1') > -1){
    var fw = document.getElementById('b2b-form-wrap');
    var fs = document.getElementById('b2b-success');
    if(fw) fw.style.display = 'none';
    if(fs) fs.style.display = 'block';
  }
})();
