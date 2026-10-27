// Send old and secondary hosts to the canonical domain, keeping path and query.
const CANONICAL = 'getmoneybeast.com';
const REDIRECT_HOSTS = new Set(['money.ilyusha.xyz', 'www.getmoneybeast.com']);

export async function onRequest(context) {
  const url = new URL(context.request.url);
  const host = (context.request.headers.get('host') || url.hostname).toLowerCase().split(':')[0];
  if (REDIRECT_HOSTS.has(host)) {
    return Response.redirect(`https://${CANONICAL}${url.pathname}${url.search}`, 301);
  }
  return context.next();
}
