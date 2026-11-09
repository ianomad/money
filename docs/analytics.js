(() => {
  // Exclude local development and deployment previews.
  if (window.location.hostname !== 'getmoneybeast.com') return;

  const measurementId = 'G-7WGRRRQQRB';
  window.dataLayer = window.dataLayer || [];
  function gtag() { window.dataLayer.push(arguments); }
  gtag('js', new Date());
  // Enhanced measurement is off for this stream. Filters must not create pageviews.
  gtag('config', measurementId, {
    page_location: window.location.origin + window.location.pathname,
    page_referrer: document.referrer ? document.referrer.split(/[?#]/)[0] : '',
    allow_google_signals: false,
    allow_ad_personalization_signals: false
  });

  // Measure clicks on the "Follow on X" links (header pill + footer line).
  document.addEventListener('click', (e) => {
    const a = e.target.closest && e.target.closest('a[data-x-follow]');
    if (!a) return;
    gtag('event', 'x_follow_click', { link_location: a.dataset.xFollow, page_path: window.location.pathname, transport_type: 'beacon' });
  });

  // Measure clicks on home cards/links tagged data-ev (e.g. feat = top savings list -> /rates, due-proptax).
  document.addEventListener('click', (e) => {
    const a = e.target.closest && e.target.closest('a[data-ev]');
    if (!a) return;
    gtag('event', 'card_click', { card: a.dataset.ev, page_path: window.location.pathname, transport_type: 'beacon' });
  });

  // Home "what is your cash earning?" check: first interaction + CTA to the matching account.
  let calcOnce = false;
  function calcRoot(el) { return el && el.closest && el.closest('#home-calc'); }
  function onCalcInteract(e) {
    if (calcOnce || !calcRoot(e.target)) return;
    calcOnce = true;
    gtag('event', 'calc_interact', { page_path: window.location.pathname, transport_type: 'beacon' });
  }
  document.addEventListener('input', onCalcInteract, true);
  document.addEventListener('change', onCalcInteract, true);
  document.addEventListener('click', (e) => {
    if (e.target.closest && e.target.closest('#home-calc .fchips button, #home-calc input')) onCalcInteract(e);
    const a = e.target.closest && e.target.closest('a[data-calc-cta]');
    if (!a) return;
    gtag('event', 'calc_cta_click', { account: a.dataset.calcCta, page_path: window.location.pathname, transport_type: 'beacon' });
  });

  const tag = document.createElement('script');
  tag.async = true;
  tag.src = 'https://www.googletagmanager.com/gtag/js?id=' + measurementId;
  document.head.appendChild(tag);
})();
