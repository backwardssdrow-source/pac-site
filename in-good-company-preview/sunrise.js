
'use strict';
const services=JSON.parse(document.getElementById('services-data').textContent);
const byId=Object.fromEntries(services.map(s=>[s.id,s]));
const serviceModal=document.getElementById('service-modal');
const inquiryModal=document.getElementById('inquiry-modal');
const nav=document.getElementById('navigation');
const menu=document.querySelector('.menu-toggle');
let lastTrigger=null;
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
menu.addEventListener('click',()=>{const open=menu.getAttribute('aria-expanded')!=='true';menu.setAttribute('aria-expanded',String(open));nav.classList.toggle('open',open);});
nav.querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>{menu.setAttribute('aria-expanded','false');nav.classList.remove('open');}));
document.addEventListener('keydown',e=>{if(e.key==='Escape'){nav.classList.remove('open');menu.setAttribute('aria-expanded','false');}});
document.querySelectorAll('[data-filter]').forEach(button=>button.addEventListener('click',()=>{
 const f=button.dataset.filter;
 document.querySelectorAll('[data-filter]').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));
 document.querySelectorAll('[data-service-category]').forEach(el=>{const c=el.dataset.serviceCategory;el.hidden=!(f==='all'||c===f||c==='focused'&&(f==='erg'||f==='presence'));});
 document.getElementById('sessions-label').hidden=false;
 document.getElementById('studio-label').hidden=f==='individual';
 document.querySelector('.studio-grid').hidden=f==='individual';
 document.querySelector('.studio-grid').style.gridTemplateColumns=f==='all'?'':'1fr';
 document.querySelector('.session-grid').style.gridTemplateColumns=f==='individual'?'minmax(0,650px)':'';
}));
function openService(id){
 const s=byId[id];if(!s)return;
 if(!serviceModal.open)lastTrigger=document.activeElement;
 document.getElementById('service-practice').textContent=s.practice;
 document.getElementById('service-body').innerHTML=`<h2 id="service-title">${esc(s.name)}</h2><p class="modal-price">${esc(s.fee)}${s.suffix?' <span style="font-size:14px;font-weight:400">'+esc(s.suffix)+'</span>':''}</p><p class="modal-meta">${esc(s.duration)} · Remote-first · USD</p><p class="modal-intro">${esc(s.details)}</p><h3>What you receive</h3><ul>${s.items.map(i=>'<li>'+esc(i)+'</li>').join('')}</ul><div class="modal-boundary">${esc(s.boundary)}</div><button class="button dark" id="inquire-service" type="button">Ask about this service <span class="arrow" aria-hidden="true">↗</span></button><p class="form-foot">Inquiry preview only. Scope and fee are confirmed before paid work begins.</p>`;
 document.getElementById('inquire-service').addEventListener('click',()=>{serviceModal.close();document.getElementById('service-select').value=id;location.hash='contact';setTimeout(()=>document.querySelector('[name="name"]').focus({preventScroll:true}),150);});
 if(!serviceModal.open)serviceModal.showModal();
 document.title=s.name+' | MakeGood Co.';
}
function closeService(){serviceModal.close();if(location.hash.startsWith('#service-'))history.replaceState(null,'',location.href.split('#')[0]+'#services');document.title='Make Good | Services and Founding Pricing';if(lastTrigger&&document.contains(lastTrigger))lastTrigger.focus({preventScroll:true});}
serviceModal.querySelector('.close').addEventListener('click',closeService);
serviceModal.addEventListener('cancel',e=>{e.preventDefault();closeService();});
serviceModal.addEventListener('click',e=>{if(e.target===serviceModal){const r=serviceModal.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)closeService();}});
function route(){let raw;try{raw=decodeURIComponent(location.hash.slice(1));}catch{return;}let key=raw.replace(/^\/?service\//,'service-').replace(/^\//,'');const aliases={'coaching':'services','erg-studio':'services','presence-studio':'services','connect':'contact','service-embedded-senior-presence-advisory':'service-senior-presence-advisory'};key=aliases[key]||key;if(key!==raw){history.replaceState(null,'',location.href.split('#')[0]+'#'+key);}if(key.startsWith('service-')){openService(key.slice(8));}else{if(serviceModal.open)serviceModal.close();document.title='Make Good | Services and Founding Pricing';if(key!==raw)document.getElementById(key)?.scrollIntoView();}}
addEventListener('hashchange',route);route();
inquiryModal.querySelector('.close').addEventListener('click',()=>inquiryModal.close());
inquiryModal.addEventListener('click',e=>{if(e.target===inquiryModal){const r=inquiryModal.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)inquiryModal.close();}});
document.getElementById('inquiry-form').addEventListener('submit',e=>{e.preventDefault();const f=e.currentTarget;if(!f.reportValidity())return;const d=new FormData(f);const name=String(d.get('name')).trim();const email=String(d.get('email')).trim();const org=String(d.get('organization')).trim();const message=String(d.get('message')).trim();if(!name||!message){if(!name)f.elements.name.setCustomValidity('Please enter your name.');if(!message)f.elements.message.setCustomValidity('Please add a short description.');f.reportValidity();return;}
 const service=byId[d.get('service')]?.name||'An introductory conversation';
 const text=`MakeGood Co. — Inquiry draft (not sent)\n\nName: ${name}\nEmail: ${email}\nOrganization: ${org||'Not provided'}\nInterested in: ${service}\n\n${message}`;
 document.getElementById('inquiry-text').textContent=text.replace(/\\n/g,'\n');document.getElementById('copy-status').textContent='';inquiryModal.showModal();});
document.querySelector('[name="name"]').addEventListener('input',e=>e.target.setCustomValidity(''));
document.querySelector('[name="message"]').addEventListener('input',e=>e.target.setCustomValidity(''));
document.getElementById('copy-inquiry').addEventListener('click',async()=>{const text=document.getElementById('inquiry-text').textContent;const status=document.getElementById('copy-status');try{await navigator.clipboard.writeText(text);status.textContent='Copied to your clipboard. Nothing has been sent.';}catch{const sel=getSelection();const range=document.createRange();range.selectNodeContents(document.getElementById('inquiry-text'));sel.removeAllRanges();sel.addRange(range);status.textContent='Select and copy the highlighted text, or use Save as text.';}});
document.getElementById('save-inquiry').addEventListener('click',()=>{const blob=new Blob([document.getElementById('inquiry-text').textContent],{type:'text/plain;charset=utf-8'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='MakeGood_Inquiry_Draft.txt';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);document.getElementById('copy-status').textContent='Your draft has been saved locally. Nothing has been sent.';});
