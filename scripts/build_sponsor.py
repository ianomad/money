"""Write docs/sponsor.html and ensure footer Sponsor links on served pages."""
from pathlib import Path

BODY = """<p class="trust"><span><b>●</b> Display sponsorship</span><span>Rankings stay unpaid</span><span>Finance advertisers only</span></p><section class="pagehead"><p class="eyebrow">SPONSOR / DISPLAY ONLY</p>
<h1>Reach people who are <em>moving their cash.</em></h1>
<p class="lead">Money is a hand-checked tracker of savings rates, cards, and markets at <b>money.ilyusha.xyz</b>. Editorial rankings stay unpaid. Sponsorship is a separate display slot, never a better rank.</p></section>
<section class="digest" id="sponsor-who">
<p class="eyebrow"><span class="dot"></span> WHO SHOWS UP</p>
<h2 class="takeaway">Readers comparing where idle cash earns more, and what the day's rates mean for them.</h2>
<p>Traffic comes from the Money Beast account on X (<a href="https://x.com/MoneyBeastHQ">@MoneyBeastHQ</a>) and from people who land on the site directly. We do not sell or rent emails. We do not take payment to raise a bank or card in the tables.</p>
</section>
<section class="digest" id="sponsor-offer">
<p class="eyebrow"><span class="dot"></span> WHAT YOU GET</p>
<h2 class="takeaway">One week on every main page: name, short pitch, and a link.</h2>
<ul>
<li>A sponsor bar on Rates, Markets, and Cards for seven days: your name or brand, about 40 characters of pitch, and one outbound link.</li>
<li>Copy goes live after we approve the creative (no misleading claims, no "#1 bank" language that contradicts the tables).</li>
<li>If another sponsor is already booked, yours starts when that week ends.</li>
</ul>
<p><b>Starting rate:</b> $200 per week. Goes up $50 after every sold week. First three weeks are at the starter price.</p>
<p><a href="mailto:dev@ilyusha.xyz?subject=Money%20sponsorship%20inquiry&amp;body=Hi%20%E2%80%94%20I%27d%20like%20to%20sponsor%20money.ilyusha.xyz.%0A%0ACompany%3A%0AWebsite%3A%0APitch%20(max%20~40%20chars)%3A%0APreferred%20week%3A%0A">Email to book a week ↗</a></p>
</section>
<section class="digest" id="sponsor-rules">
<p class="eyebrow"><span class="dot"></span> GUARDRAILS</p>
<h2 class="takeaway">Paid display. Unpaid rankings.</h2>
<p>We keep "No sponsored rankings" on every data page. Sponsors cannot buy a higher APY row, a badge, or a calculator default. Finance advertisers only (banks, fintech, cards, investing tools). We can decline a creative.</p>
</section>"""


def write(page, finalize, lazyimg, rd, D, DIGEST_CSS, UI_CSS):
    sp = page(
        "Sponsor Money — money.ilyusha.xyz",
        "Display sponsorship on money.ilyusha.xyz. Rankings stay unpaid; one-week sponsor bar on Rates, Markets, and Cards.",
        "/sponsor",
        "x",
        BODY,
        DIGEST_CSS + UI_CSS,
    )
    (D / "sponsor.html").write_text(finalize(lazyimg(sp)))
    for name in ("index.html", "markets.html", "cards.html", "sponsor.html"):
        h = rd(name)
        if 'href="/sponsor"' in h:
            continue
        if 'mailto:dev@ilyusha.xyz?subject=Money%20correction' in h:
            h = h.replace(
                '<a href="mailto:dev@ilyusha.xyz?subject=Money%20correction">Suggest a correction ↗</a>',
                '<span><a href="/sponsor">Sponsor</a> · <a href="mailto:dev@ilyusha.xyz?subject=Money%20correction">Suggest a correction ↗</a></span>',
                1,
            )
        elif '<a href="index.html">Back to savings</a>' in h:
            h = h.replace(
                '<a href="index.html">Back to savings</a>',
                '<span><a href="/sponsor">Sponsor</a> · <a href="/">Rates</a></span>',
                1,
            )
        elif '</footer>' in h:
            h = h.replace('</footer>', '<span><a href="/sponsor">Sponsor</a></span></footer>', 1)
        (D / name).write_text(h)
