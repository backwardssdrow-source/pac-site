/* Shared MakeGood website behavior. Inquiry content is held in memory until submission. */
(()=>{'use strict';
const menu=document.querySelector('.menu-toggle'),nav=document.getElementById('navigation'),header=document.getElementById('site-header'),main=document.getElementById('main');
function closeMenu(){if(nav)nav.classList.remove('open');if(menu){menu.setAttribute('aria-expanded','false');menu.textContent='Menu';}}
if(menu&&nav){
 menu.addEventListener('click',()=>{const on=menu.getAttribute('aria-expanded')!=='true';nav.classList.toggle('open',on);menu.setAttribute('aria-expanded',String(on));menu.textContent=on?'Close':'Menu';});
 document.addEventListener('keydown',e=>{if(e.key==='Escape'&&nav.classList.contains('open')){closeMenu();menu.focus();}});
 document.addEventListener('pointerdown',e=>{if(header&&!header.contains(e.target))closeMenu();});
 nav.addEventListener('click',e=>{if(e.target.closest('a'))closeMenu();});
 nav.addEventListener('focusout',e=>{if(header&&e.relatedTarget&&!header.contains(e.relatedTarget))closeMenu();});
 window.addEventListener('resize',()=>{if(innerWidth>900)closeMenu();});
 window.addEventListener('pageshow',closeMenu);
 document.documentElement.classList.add('menu-ready');
}
function updateHeader(){if(!header)return;const h=header.getBoundingClientRect().height;const tall=h>innerHeight*.30;header.classList.toggle('unstick',tall);document.documentElement.style.setProperty('--nav-h',tall?'0px':Math.ceil(h)+'px');}
if(header&&'ResizeObserver'in window)new ResizeObserver(updateHeader).observe(header);window.addEventListener('resize',updateHeader);updateHeader();
const params=new URLSearchParams(location.search);
function filter(category){if(!['all','erg','presence','individual'].includes(category))category='all';document.querySelectorAll('[data-filter]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.filter===category)));document.querySelectorAll('.offer').forEach(o=>{o.hidden=category!=='all'&&!o.dataset.audiences.split(' ').includes(category);});document.querySelectorAll('[data-group]').forEach(g=>{const visible=[...g.querySelectorAll('.offer')].filter(x=>!x.hidden);g.hidden=!visible.length;const h=g.querySelector('h2'),intro=g.querySelector('.group-intro'),shared=g.dataset.group==='presence'&&category==='erg';h.textContent=shared?'A focused decision for your ERG program.':h.dataset.default;intro.hidden=shared;});const n=document.querySelectorAll('.offer:not([hidden])').length,names={all:'All services',erg:'ERG Studio',presence:'Leaders & Teams',individual:'Individual Coaching'},status=document.getElementById('filter-status');if(status)status.textContent=names[category]+' · '+n+(n===1?' service':' services')+' · Fees and scope on each service page.';}
if(document.getElementById('filter-status')){filter(params.get('category')||'all');document.querySelectorAll('[data-filter]').forEach(b=>b.addEventListener('click',()=>{const url=new URL(location.href),v=b.dataset.filter;if(v==='all')url.searchParams.delete('category');else url.searchParams.set('category',v);history.replaceState(null,'',url.pathname+url.search+url.hash);filter(v);}));}
const form=document.getElementById('inquiry-form');
if(form&&form.querySelector('[data-inquiry-submit]')&&document.getElementById('contact-availability')&&document.getElementById('inquiry-status')&&document.getElementById('inquiry-reference')){
 // Replace only after the private handler is deployed and its readable response is verified.
 const CONTACT_ENDPOINT='https://script.google.com/macros/s/AKfycbw2dDQdUO9h2D8M4Np23fV6YxbIpAXsnW7mhQCrKL11t_mWRUzXkIhIbD08fdOdkCLE/exec';
 const REQUEST_TIMEOUT_MS=25000;
 const select=document.getElementById('service-select'),service=params.get('service');
 const submit=form.querySelector('[data-inquiry-submit]');
 const fields=[...form.querySelectorAll('input, select, textarea')];
 const status=document.getElementById('inquiry-status');
 const result=document.getElementById('inquiry-result');
 const availability=document.getElementById('contact-availability');
 let inFlight=false,pending=null;
 function say(message){status.textContent=message;}
 function setBusy(busy){inFlight=busy;form.setAttribute('aria-busy',String(busy));fields.forEach(field=>field.disabled=busy);submit.disabled=busy;submit.textContent=busy?'Sending…':pending?'Try again':'Send inquiry';}
 function readPayload(){
  const d=new FormData(form),value=name=>String(d.get(name)||'').trim();
  return {name:value('name'),email:value('email'),organization:value('organization'),service:value('service'),message:value('message'),website:String(d.get('website')||'')};
 }
 function validPayload(p){
  return p.name.length>0&&p.name.length<=100&&!/[\r\n\x00-\x1f]/.test(p.name)
   &&p.email.length<=254&&/^[^\s@,;<>]+@[^\s@,;<>]+\.[^\s@,;<>]+$/.test(p.email)
   &&p.organization.length<=160&&!/[\r\n\x00-\x1f]/.test(p.organization)
   &&[...select.options].some(option=>option.value===p.service)
   &&p.message.length>0&&p.message.length<=2000&&!/[\x00-\x08\x0b\x0c\x0e-\x1f]/.test(p.message)
   &&p.website==='';
 }
 let configured=false;
 try{const endpoint=new URL(CONTACT_ENDPOINT);configured=endpoint.protocol==='https:'&&endpoint.hostname==='script.google.com'&&/^\/macros\/s\/[A-Za-z0-9_-]+\/exec$/.test(endpoint.pathname)&&!endpoint.search&&!endpoint.hash;}catch(_){}
 if(service&&[...select.options].some(option=>option.value===service))select.value=service;
 if(!configured||!window.crypto||typeof window.crypto.randomUUID!=='function'){
  form.addEventListener('submit',event=>event.preventDefault());
  availability.querySelector('strong').textContent='Online submission is temporarily unavailable';
  availability.querySelector('p').textContent='Please return later to send your inquiry.';
  say('The form is not connected. Nothing can be sent from this page.');
 }else{
  setBusy(false);
  form.addEventListener('input',()=>{
   if(pending&&JSON.stringify(readPayload())!==pending.fingerprint){
    say('Your earlier attempt may already have reached us. Sending changed details creates a separate inquiry. To retry the same inquiry, restore your original details.');
    submit.textContent='Send changed inquiry';
   }else if(pending){
    say('Your original details are restored. Try again to check or complete the same inquiry.');
    submit.textContent='Try again';
   }
  });
  form.addEventListener('submit',async e=>{
   e.preventDefault();
   if(inFlight||!form.reportValidity())return;
   const payload=readPayload();
   if(!validPayload(payload)){say('Please check your name, email, and inquiry. Blank or invalid details cannot be sent.');return;}
   const fingerprint=JSON.stringify(payload);
   if(!pending||pending.fingerprint!==fingerprint)pending={fingerprint,body:JSON.stringify({request_id:window.crypto.randomUUID(),...payload})};
   const request=JSON.parse(pending.body);
   const controller=new AbortController();
   const timeout=setTimeout(()=>controller.abort(),REQUEST_TIMEOUT_MS);
   setBusy(true);say('Sending your inquiry…');
   try{
    const response=await fetch(CONTACT_ENDPOINT,{method:'POST',mode:'cors',credentials:'omit',redirect:'follow',headers:{'Content-Type':'text/plain;charset=UTF-8'},body:pending.body,signal:controller.signal});
    if(!response.ok||response.type==='opaque')throw new Error('Unreadable response');
    const data=await response.json();
    if(data&&data.ok===true&&data.inquiry_id===request.request_id){
     document.getElementById('inquiry-reference').textContent='Reference: '+request.request_id;
     pending=null;form.reset();form.hidden=true;result.hidden=false;result.focus();say('');
    }else if(data&&data.ok===false&&data.code==='NOTIFICATION_FAILED'&&data.stored===true&&data.inquiry_id===request.request_id){
     say('Your inquiry was saved, but we could not complete the notification to our team. Try again with the same details to complete this inquiry.');
    }else if(data&&data.ok===false&&['INVALID','BUSY','CONFIG','CONFLICT','LIMIT','UNAVAILABLE'].includes(data.code)){
     const messages={INVALID:'Please check your details before trying again.',BUSY:'The sending service is busy. Try again with the same details in a moment.',CONFIG:'Online submission is temporarily unavailable. Please try again later.',CONFLICT:'We could not safely match this inquiry to its earlier attempt. Please try again later.',LIMIT:'The sending service has reached its temporary limit. Please try again later with the same details.',UNAVAILABLE:'We could not confirm completion. Try again with the same details to check or complete this inquiry.'};
     say(messages[data.code]);
    }else{throw new Error('Unconfirmed response');}
   }catch(_){
    say('We could not confirm whether your inquiry was received. It may already have reached us. Try again with the same details to check or complete the same inquiry.');
   }finally{clearTimeout(timeout);setBusy(false);}
  });
  document.getElementById('edit-inquiry').addEventListener('click',()=>{result.hidden=true;form.hidden=false;form.querySelector('[name="name"]').focus();});
 }
}
function revealAnchor(){let id='';try{id=decodeURIComponent(location.hash.slice(1));}catch(_){return;}const el=document.getElementById(id);if(!el)return;if(el.tagName==='DETAILS')el.open=true;requestAnimationFrame(()=>el.scrollIntoView({block:'start'}));}
window.addEventListener('hashchange',revealAnchor);revealAnchor();
const skip=document.querySelector('.skip');if(skip)skip.addEventListener('click',e=>{e.preventDefault();main.focus();main.scrollIntoView();});
})();

