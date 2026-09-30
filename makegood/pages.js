/* Progressive enhancements only. Page content and navigation are real HTML. */
(() => {
  'use strict';
  const root = document.body.dataset.root || '';
  const serviceIds = ['coaching','decision-session','practice-lab','erg-portfolio-diagnostic','erg-operating-model-build','fractional-erg-office','presence-scan','presence-lab','senior-presence-advisory'];
  const routes = {home:'index.html',services:'services.html',approach:'approach.html',about:'about.html',faq:'faq.html',contact:'contact.html'};
  const hash = location.hash.slice(1);
  const serviceId = hash.startsWith('service-') ? hash.slice(8) : hash.startsWith('/service/') ? hash.slice(9) : '';
  let legacyTarget = serviceIds.includes(serviceId) ? 'services/' + serviceId + '.html' : routes[hash] || routes[hash.replace(/^\//, '')];
  if (hash === 'terms' && document.body.dataset.page !== 'faq') legacyTarget = 'faq.html#terms';
  if (legacyTarget) {
    const next = new URL(root + legacyTarget, location.href);
    next.search = location.search;
    if (next.href !== location.href) { location.replace(next.href); return; }
  }
  const toggle = document.querySelector('.menu-toggle');
  const navigation = document.querySelector('#navigation');
  function closeMenu() {
    if (!toggle || !navigation) return;
    navigation.classList.remove('open');
    toggle.setAttribute('aria-expanded', 'false');
  }
  if (toggle && navigation) {
    toggle.addEventListener('click', () => {
      const open = toggle.getAttribute('aria-expanded') !== 'true';
      navigation.classList.toggle('open', open);
      toggle.setAttribute('aria-expanded', String(open));
    });
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape' && navigation.classList.contains('open')) { closeMenu(); toggle.focus(); }
    });
    navigation.addEventListener('click', event => { if (event.target.closest('a')) closeMenu(); });
  }
  const query = new URLSearchParams(location.search);
  const filterButtons = Array.from(document.querySelectorAll('[data-filter]'));
  if (filterButtons.length) {
    const categories = {all:'All services',individual:'Services for individuals',erg:'Services for ERG programs',presence:'Services for leaders and teams'};
    function filter(category) {
      if (!(category in categories)) category = 'all';
      filterButtons.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.filter === category)));
      document.querySelectorAll('[data-service-category]').forEach(card => {
        const kind = card.dataset.serviceCategory;
        card.hidden = !(category === 'all' || kind === category || (kind === 'focused' && (category === 'erg' || category === 'presence')));
      });
      [['.session-grid','#sessions-label'],['.studio-grid','#studio-label']].forEach(([gridSelector,labelSelector]) => {
        const grid = document.querySelector(gridSelector);
        const label = document.querySelector(labelSelector);
        const visible = grid && Array.from(grid.children).some(child => !child.hidden);
        if (grid) grid.hidden = !visible;
        if (label) label.hidden = !visible;
      });
      const count = document.querySelectorAll('.session-card:not([hidden])').length + Array.from(document.querySelectorAll('.studio-panel:not([hidden])')).reduce((n,panel) => n + panel.querySelectorAll('.studio-row').length,0);
      const status = document.querySelector('#filter-status');
      if (status) status.textContent = categories[category] + ' · ' + count + (count === 1 ? ' service' : ' services');
    }
    filterButtons.forEach(button => button.addEventListener('click', () => {
      filter(button.dataset.filter);
      const next = new URL(location.href);
      if (button.dataset.filter === 'all') next.searchParams.delete('category'); else next.searchParams.set('category',button.dataset.filter);
      history.replaceState(null,'',next);
    }));
    filter(query.get('category') || 'all');
  }
  if (location.hash === '#terms') {
    const terms = document.getElementById('terms');
    if (terms) { terms.open = true; terms.scrollIntoView(); }
  }
  const form = document.querySelector('#inquiry-form');
  if (form) {
    const select = document.querySelector('#service-select');
    if (serviceIds.includes(query.get('service'))) select.value = query.get('service');
    form.querySelector('[data-preview-submit]').disabled = false;
    const panel = document.querySelector('#inquiry-preview-panel');
    const preview = document.querySelector('#inquiry-text');
    const status = document.querySelector('#copy-status');
    form.addEventListener('submit', event => {
      event.preventDefault();
      if (!form.reportValidity()) return;
      const data = new FormData(form);
      preview.textContent = ['MAKEGOOD CO. — INQUIRY PREVIEW (NOT SENT)', '', 'Name: ' + String(data.get('name') || '').trim(), 'Email: ' + String(data.get('email') || '').trim(), 'Organization: ' + (String(data.get('organization') || '').trim() || 'Not provided'), 'Starting point: ' + select.options[select.selectedIndex].text, '', String(data.get('message') || '').trim(), '', 'Nothing has been sent. This draft creates no booking or charge.'].join('\n');
      status.textContent = '';
      panel.hidden = false;
      panel.focus();
    });
    document.querySelector('#copy-inquiry').addEventListener('click', async () => {
      try { await navigator.clipboard.writeText(preview.textContent); status.textContent = 'Draft copied. Nothing was sent.'; }
      catch (_) { status.textContent = 'Copy is unavailable here. Select the draft text to copy it manually, or use Save as text.'; }
    });
    document.querySelector('#save-inquiry').addEventListener('click', () => {
      const url = URL.createObjectURL(new Blob([preview.textContent],{type:'text/plain;charset=utf-8'}));
      const link = document.createElement('a'); link.href = url; link.download = 'MakeGood-inquiry-draft.txt';
      document.body.appendChild(link); link.click(); link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      status.textContent = 'Text-file download requested. Nothing was sent.';
    });
    document.querySelector('#edit-inquiry').addEventListener('click', () => { panel.hidden = true; form.querySelector('textarea').focus(); });
  }
})();
