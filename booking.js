// [UI-005] booking.js — service-booking form that hands off to WhatsApp
// DOES:   validates #bookForm, builds a localized booking message (en/it/sq from
//         <html lang>) and opens a pre-filled WhatsApp chat; no backend, no storage.
// IN:     #bookForm fields: service, name, phone (required); date, time, notes (optional)
// OUT:    window.open on api.whatsapp.com with the encoded message; also sets today
//         as the minimum pickable date on #bk-date
// NOTES:  the date line is rendered in a locale matching the page language and falls
//         back to the raw ISO string if toLocaleDateString throws.
(function(){
  'use strict';
  var form=document.getElementById('bookForm');
  if(!form)return;
  var lang=(document.documentElement.lang||'en').split('-')[0];
  var di=document.getElementById('bk-date');
  if(di)di.min=new Date().toISOString().split('T')[0];
  var T={
    en:{intro:"Hi, I'd like to book a service at Iglisi Watch:\n\n",svc:'Service: ',name:'Name: ',phone:'Phone: ',date:'Date: ',time:'Time: ',notes:'Notes: '},
    it:{intro:"Salve, vorrei prenotare un servizio da Iglisi Watch:\n\n",svc:'Servizio: ',name:'Nome: ',phone:'Telefono: ',date:'Data: ',time:'Orario: ',notes:'Note: '},
    sq:{intro:"Pershendetje, dua te rezervoj nje sherbim tek Iglisi Watch:\n\n",svc:'Sherbimi: ',name:'Emri: ',phone:'Telefoni: ',date:'Data: ',time:'Ora: ',notes:'Shenime: '}
  };
  var t=T[lang]||T.en;
  // [UI-005.a] err — inline "required field" feedback
  // DOES:   tints the offending field red and focuses it; the tint clears itself on
  //         the next keystroke. The color IS the message — no error text is shown.
  function err(el){el.style.borderColor='#c0392b';el.addEventListener('input',function(){el.style.borderColor='';},{once:true});el.focus();}
  // [UI-005.b] submit handler — validate, compose, hand off
  // DOES:   blocks the native submit, checks the three required fields (first failure
  //         wins), then assembles the localized message and opens WhatsApp.
  form.addEventListener('submit',function(e){
    e.preventDefault();
    var s=document.getElementById('bk-service'),n=document.getElementById('bk-name'),p=document.getElementById('bk-phone');
    if(!s.value){err(s);return;}
    if(!n.value.trim()){err(n);return;}
    if(!p.value.trim()){err(p);return;}
    var date=document.getElementById('bk-date').value,time=document.getElementById('bk-time').value,notes=document.getElementById('bk-notes').value.trim();
    var msg=t.intro+t.svc+s.value+'\n'+t.name+n.value.trim()+'\n'+t.phone+p.value.trim()+'\n';
    if(date){try{var d=new Date(date+'T12:00:00'),loc=lang==='sq'?'sq-AL':lang==='it'?'it-IT':'en-GB';msg+=t.date+d.toLocaleDateString(loc,{weekday:'long',day:'numeric',month:'long'})+'\n';}catch(x){msg+=t.date+date+'\n';}}
    if(time)msg+=t.time+time+'\n';
    if(notes)msg+=t.notes+notes+'\n';
    window.open('https://api.whatsapp.com/send?phone=355676360510&text='+encodeURIComponent(msg),'_blank','noopener,noreferrer');
  });
}());
