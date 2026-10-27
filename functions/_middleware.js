// Send old and secondary hosts to the canonical domain, keeping path and query.
const CANONICAL = 'getmoneybeast.com';
const REDIRECT_HOSTS = new Set(['money.ilyusha.xyz', 'www.getmoneybeast.com']);

// Google Search Console HTML-file verification must answer 200 on every host
// (no redirect), so both the old and new properties stay verified for Change of Address.
const GSC_FILE = '/google84212aea3ca8c810.html';

export async function onRequest(context) {
  const url = new URL(context.request.url);
  if (url.pathname === GSC_FILE || url.pathname === GSC_FILE.slice(0, -5)) {
    return new Response('google-site-verification: google84212aea3ca8c810.html', {
      headers: { 'content-type': 'text/html; charset=utf-8' },
    });
  }
  const host = (context.request.headers.get('host') || url.hostname).toLowerCase().split(':')[0];
  if (REDIRECT_HOSTS.has(host)) {
    return Response.redirect(`https://${CANONICAL}${url.pathname}${url.search}`, 301);
  }
  return context.next();
}
