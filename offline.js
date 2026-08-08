// [UI-015] offline.js — offline fallback page's retry button
// DOES:   reloads the page when #retry-btn is clicked; that is the whole file.
document.getElementById('retry-btn').addEventListener('click',function(){location.reload();});
