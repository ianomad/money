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

  const tag = document.createElement('script');
  tag.async = true;
  tag.src = 'https://www.googletagmanager.com/gtag/js?id=' + measurementId;
  document.head.appendChild(tag);
})();
