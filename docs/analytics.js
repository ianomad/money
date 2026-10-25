(() => {
  // Exclude local development and deployment previews.
  if (window.location.hostname !== 'money.ilyusha.xyz') return;

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

  const tag = document.createElement('script');
  tag.async = true;
  tag.src = 'https://www.googletagmanager.com/gtag/js?id=' + measurementId;
  document.head.appendChild(tag);
})();
