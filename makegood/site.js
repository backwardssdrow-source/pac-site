/* Shared behavior for the hosted MakeGood review. No form information is transmitted or stored. */
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
if(form){const select=document.getElementById('service-select'),service=params.get('service');if(service&&[...select.options].some(o=>o.value===service))select.value=service;form.addEventListener('submit',e=>{e.preventDefault();if(!form.reportValidity())return;const d=new FormData(form);document.getElementById('inquiry-text').textContent=['DRAFT — NOT SENT','Name: '+d.get('name'),'Email: '+d.get('email'),'Organization: '+(d.get('organization')||'Not provided'),'Support: '+select.options[select.selectedIndex].text,'',String(d.get('message')).trim()].join('\n');const result=document.getElementById('inquiry-result');result.hidden=false;result.focus();});document.getElementById('edit-inquiry').addEventListener('click',()=>{document.getElementById('inquiry-result').hidden=true;form.querySelector('textarea').focus();});form.querySelectorAll('[disabled]').forEach(el=>el.disabled=false);}
function revealAnchor(){let id='';try{id=decodeURIComponent(location.hash.slice(1));}catch(_){return;}const el=document.getElementById(id);if(!el)return;if(el.tagName==='DETAILS')el.open=true;requestAnimationFrame(()=>el.scrollIntoView({block:'start'}));}
window.addEventListener('hashchange',revealAnchor);revealAnchor();
const skip=document.querySelector('.skip');if(skip)skip.addEventListener('click',e=>{e.preventDefault();main.focus();main.scrollIntoView();});
})();
