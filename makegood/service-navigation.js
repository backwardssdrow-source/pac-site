/* Category links land on relevant results. Shared menu and intake behavior stay unchanged. */
(() => {
  'use strict';
  const targets = {
    all: 'service-options-heading',
    erg: 'erg-services-heading',
    presence: 'leadership-services-heading',
    individual: 'coaching-services-heading'
  };
  if (!document.getElementById('service-options-heading')) return;
  // The shared script changes the filter first. Keep its URL fragment consistent
  // without moving keyboard focus away from the filter the visitor is using.
  document.querySelectorAll('[data-filter]').forEach(button => {
    button.addEventListener('click', () => {
      const url = new URL(location.href);
      url.hash = targets[button.dataset.filter] || targets.all;
      history.replaceState(history.state, '', url.pathname + url.search + url.hash);
    });
  });
  // Native fragments also work without JavaScript. With JavaScript, give keyboard
  // and assistive-technology users the same starting point as sighted visitors.
  let interacted = false;
  ['pointerdown', 'keydown', 'wheel', 'touchstart'].forEach(type => {
    window.addEventListener(type, () => { interacted = true; }, { once: true, passive: true });
  });
  function focusLinkedSection() {
    if (interacted) return;
    const id = location.hash.slice(1);
    if (!Object.values(targets).includes(id)) return;
    const heading = document.getElementById(id);
    if (!heading || !heading.getClientRects().length) return;
    heading.focus({ preventScroll: true });
    heading.scrollIntoView({ block: 'start', behavior: 'instant' });
  }
  if (document.readyState === 'complete') focusLinkedSection();
  else window.addEventListener('load', focusLinkedSection, { once: true });
})();
