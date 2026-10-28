"""Write docs/disclosure.html and docs/privacy.html (affiliate disclosure + privacy policy)."""

DISCLOSURE = """<section class="pagehead"><p class="eyebrow">How we work</p>
<h1>How we check, rank <em>and make money.</em></h1>
<p class="lead">Money Beast (getmoneybeast.com) is independent and reader-supported. This page explains where the numbers come from, how lists are ordered, how to report a mistake, and how the site is paid for.</p></section>
<section class="digest" id="checking">
<p class="eyebrow"><span class="dot"></span> HOW WE CHECK</p>
<h2 class="takeaway">Every rate links to the page we checked it on, with the date.</h2>
<p>Savings rates, card terms and foreign deposit rates are read by hand from each provider’s own page (or a named official source) and stored with the source link and the date we last confirmed them. Market numbers come from public data series such as FRED, BLS and CoinGecko, each shown with its date. When we can’t confirm something, we say so on the page instead of guessing: it gets a “check date not recorded”, “may be out of date” or “not verified” label and is never put first.</p>
</section>
<section class="digest" id="ranking">
<p class="eyebrow"><span class="dot"></span> HOW WE RANK</p>
<h2 class="takeaway">By what you would actually keep, not by the biggest number.</h2>
<p>The savings calculator works out first-year earnings for your balance: a promo counts only for the months it lasts, balance caps and tiers are applied, and membership fees are subtracted. Offers you said you can’t meet (direct deposit, fees, referral links) are left out. Accounts that have stopped taking applications or that we couldn’t recheck recently are shown but not ranked first. Card picks are ranked on value after the annual fee for the spending you enter. Banks abroad can be ordered by headline rate or by an estimated dollar result that includes currency moves, and they cover only the countries we track.</p>
</section>
<section class="digest" id="corrections">
<p class="eyebrow"><span class="dot"></span> CORRECTIONS</p>
<h2 class="takeaway">Found a wrong number? Tell us and we’ll fix it.</h2>
<p>Email <a href="mailto:dev@ilyusha.xyz?subject=Money%20Beast%20correction">dev@ilyusha.xyz</a> with the page and what looks wrong. We recheck the source and update the page, usually within a day.</p>
</section>
<section class="digest" id="affiliate">
<p class="eyebrow"><span class="dot"></span> AFFILIATE LINKS</p>
<h2 class="takeaway">Some links may earn us a commission, at no cost to you.</h2>
<p>Some links on this site may be affiliate links, for example through networks such as CJ Affiliate. If you click one and open an account, apply for a card, or make a purchase, we may receive a commission from the provider. You pay nothing extra.</p>
</section>
<section class="digest" id="rankings">
<p class="eyebrow"><span class="dot"></span> RANKINGS</p>
<h2 class="takeaway">Compensation never changes the order of the tables.</h2>
<p>Rate tables and card lists are sorted by published rates, terms and the math above, never by payout. Providers cannot pay for a higher row, a badge, or a calculator default. We don't list every product on the market.</p>
</section>
<section class="digest" id="sponsors">
<p class="eyebrow"><span class="dot"></span> SPONSORSHIPS</p>
<h2 class="takeaway">Paid display is always labeled.</h2>
<p>Display sponsorships (see <a href="/sponsor">Sponsor</a>) are labeled "Sponsored" and kept separate from the rankings.</p>
</section>
<section class="digest" id="accuracy">
<p class="eyebrow"><span class="dot"></span> ACCURACY</p>
<h2 class="takeaway">Always confirm with the provider before you apply.</h2>
<p>Rates and offers change often. We check them by hand, but always confirm current terms on the provider's site. Nothing here is financial advice. Spot an error? <a href="mailto:dev@ilyusha.xyz?subject=Money%20Beast%20correction">Tell us ↗</a></p>
</section>"""

PRIVACY = """<section class="pagehead"><p class="eyebrow">PRIVACY POLICY</p>
<h1>What we collect, <em>and what we don't.</em></h1>
<p class="lead">Last updated: October 14, 2026. This policy covers getmoneybeast.com ("Money Beast", "we").</p></section>
<section class="digest" id="collect">
<p class="eyebrow"><span class="dot"></span> WHAT WE COLLECT</p>
<h2 class="takeaway">No accounts, no sign-ups, no email lists.</h2>
<p>We use Google Analytics 4 to measure aggregate usage such as pages viewed, referrer, device and browser type, and approximate region. Our hosting provider (Cloudflare) processes standard request logs to deliver and secure the site. If you email us, we receive your email address and message. If you pick briefing topics or enter your bank’s rate, those settings and your last-visit date are saved only in your own browser’s local storage; they are never sent to us, and the Reset button on the home page clears them.</p>
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
        ("disclosure.html", "How we check and rank — Money Beast",
         "Where Money Beast numbers come from, how lists are ranked, how to report a correction, and how the site is funded. Rankings are never paid.",
         "/disclosure", DISCLOSURE),
        ("privacy.html", "Privacy Policy — Money Beast",
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
