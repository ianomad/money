"""Write docs/disclosure.html and docs/privacy.html (affiliate disclosure + privacy policy)."""

DISCLOSURE = """<section class="pagehead"><p class="eyebrow">ADVERTISER DISCLOSURE</p>
<h1>How Money <em>makes money.</em></h1>
<p class="lead">Money (getmoneybeast.com) is independent and reader-supported. This page explains affiliate links and sponsorships.</p></section>
<section class="digest" id="affiliate">
<p class="eyebrow"><span class="dot"></span> AFFILIATE LINKS</p>
<h2 class="takeaway">Some links may earn us a commission, at no cost to you.</h2>
<p>Some links on this site may be affiliate links, for example through networks such as CJ Affiliate. If you click one and open an account, apply for a card, or make a purchase, we may receive a commission from the provider. You pay nothing extra.</p>
</section>
<section class="digest" id="rankings">
<p class="eyebrow"><span class="dot"></span> RANKINGS</p>
<h2 class="takeaway">Compensation never changes the order of the tables.</h2>
<p>Rate tables and card lists are sorted by published rates and terms, never by payout. Providers cannot pay for a higher row, a badge, or a calculator default. We don't list every product on the market.</p>
</section>
<section class="digest" id="sponsors">
<p class="eyebrow"><span class="dot"></span> SPONSORSHIPS</p>
<h2 class="takeaway">Paid display is always labeled.</h2>
<p>Display sponsorships (see <a href="/sponsor">Sponsor</a>) are labeled "Sponsored" and kept separate from the rankings.</p>
</section>
<section class="digest" id="accuracy">
<p class="eyebrow"><span class="dot"></span> ACCURACY</p>
<h2 class="takeaway">Always confirm with the provider before you apply.</h2>
<p>Rates and offers change often. We check them by hand, but always confirm current terms on the provider's site. Nothing here is financial advice. Spot an error? <a href="mailto:dev@ilyusha.xyz?subject=Money%20correction">Tell us ↗</a></p>
</section>"""

PRIVACY = """<section class="pagehead"><p class="eyebrow">PRIVACY POLICY</p>
<h1>What we collect, <em>and what we don't.</em></h1>
<p class="lead">Last updated: October 14, 2026. This policy covers getmoneybeast.com ("Money", "we").</p></section>
<section class="digest" id="collect">
<p class="eyebrow"><span class="dot"></span> WHAT WE COLLECT</p>
<h2 class="takeaway">No accounts, no sign-ups, no email lists.</h2>
<p>We use Google Analytics 4 to measure aggregate usage such as pages viewed, referrer, device and browser type, and approximate region. Our hosting provider (Cloudflare) processes standard request logs to deliver and secure the site. If you email us, we receive your email address and message.</p>
</section>
<section class="digest" id="cookies">
<p class="eyebrow"><span class="dot"></span> COOKIES &amp; AFFILIATE TRACKING</p>
<h2 class="takeaway">Partners may set cookies when you click an outbound link.</h2>
<p>When you click an affiliate link, the affiliate network (such as CJ Affiliate) and the advertiser may set cookies or use similar technology to attribute the referral. Those sites follow their own privacy policies. You can block or delete cookies in your browser settings.</p>
</section>
<section class="digest" id="use">
<p class="eyebrow"><span class="dot"></span> HOW WE USE IT</p>
<h2 class="takeaway">To run and improve the site. We never sell your data.</h2>
<p>We use data only to operate, secure, and improve the site and to measure referrals. We do not sell or share personal information for cross-context behavioral advertising.</p>
</section>
<section class="digest" id="rights">
<p class="eyebrow"><span class="dot"></span> YOUR CHOICES</p>
<h2 class="takeaway">Ask, and we'll access or delete what we hold.</h2>
<p>You can request access to or deletion of personal information we hold, including under California law (CCPA/CPRA), by emailing <a href="mailto:dev@ilyusha.xyz?subject=Privacy%20request">dev@ilyusha.xyz</a>. The site is not directed to children under 13. We'll post any changes to this policy on this page.</p>
</section>"""


def write(page, finalize, lazyimg, rd, D, DIGEST_CSS, UI_CSS):
    for fn, title, desc, path, body in (
        ("disclosure.html", "Advertiser Disclosure — getmoneybeast.com",
         "How getmoneybeast.com is funded: affiliate links and labeled sponsorships. Rankings are never paid.",
         "/disclosure", DISCLOSURE),
        ("privacy.html", "Privacy Policy — getmoneybeast.com",
         "Privacy policy for getmoneybeast.com: analytics, cookies, affiliate tracking, and your choices.",
         "/privacy", PRIVACY),
    ):
        (D / fn).write_text(finalize(lazyimg(page(title, desc, path, "x", body, DIGEST_CSS + UI_CSS))))
    for name in ("cards.html",):
        h = rd(name)
        if 'href="/privacy"' not in h and '<a href="/sponsor">Sponsor</a> · ' in h:
            h = h.replace('<a href="/sponsor">Sponsor</a> · ',
                          '<a href="/sponsor">Sponsor</a> · <a href="/disclosure">Disclosure</a> · <a href="/privacy">Privacy</a> · ', 1)
            (D / name).write_text(h)
