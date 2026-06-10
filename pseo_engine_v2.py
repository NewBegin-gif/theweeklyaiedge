#!/usr/bin/env python3
"""pSEO-engine v2 voor theweeklyaiedge.com — veilige herbouw van run_pseo_engine.py.

Wat het doet, één artikel per run:
  1. Pull de site-repo (master — de branch waar GitHub Pages van deployt).
  2. Pak het eerste onderwerp uit pseo_topics.json waarvoor nog geen <slug>.html bestaat.
  3. Genereer het artikel via de Claude API (claude-opus-4-8, structured output),
     met een strak persona-/eerlijkheidskader: geen verzonnen cijfers, producten
     of diensten; alleen goedgekeurde affiliate-links.
  4. Valideer de output (lengte, alleen toegestane links).
  5. Render de pagina in de site-stijl (template uit runpod.html), voeg een kaart
     toe aan de homepage-sectie "Nederlandstalige gidsen", werk sitemap.xml bij.
  6. --apply: commit + push naar master. Zonder --apply: dry-run, schrijft lokaal
     maar commit/pusht niet (let op: de API-call wordt wél gedaan en kost geld).

Veiligheid:
  - GEEN hardcoded secrets. De API-key komt uit env ANTHROPIC_API_KEY
    (zet hem in /root/felix_hq/.env en source die in de cron-wrapper).
  - De GitHub-token wordt uit de remote-URL van de bestaande aibuildermarketplace-
    repo op de VPS gelezen — staat dus nergens in dit (publieke) bestand.

Gebruik op de VPS:
    python3 /root/felix_hq/pseo_engine_v2.py            # dry-run
    python3 /root/felix_hq/pseo_engine_v2.py --apply    # genereren + publiceren

Kosten: ± $0,10–0,15 per artikel (claude-opus-4-8).
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_DIR = Path("/root/felix_hq/repos/theweeklyaiedge")
AIBM_REPO = Path("/root/felix_hq/repos/aibuildermarketplace")
GITHUB_REPO = "github.com/NewBegin-gif/theweeklyaiedge.git"
BRANCH = "master"  # Pages deployt van master — NIET van main!
BASE = "https://theweeklyaiedge.com"
MODEL = "claude-opus-4-8"

GA4 = """  <script async src="https://www.googletagmanager.com/gtag/js?id=G-CW1KZ258ZV"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', 'G-CW1KZ258ZV');
  </script>"""

DISCLAIMER = ('<p style="font-size:.85rem;color:#64748b;border:1px solid var(--border);'
              'border-radius:8px;padding:1rem;margin-top:2.5rem"><strong style="color:#94a3b8">'
              "Disclaimer:</strong> dit artikel deelt mijn persoonlijke ervaring en is geen "
              "financieel advies. Crypto en gehandelde producten zijn risicovol — koersen kunnen "
              "hard dalen en een systeem dat in het verleden werkte, biedt geen garantie voor de "
              "toekomst. Handel alleen met geld dat je kunt missen.</p>")

# Toegestane links — álles daarbuiten laat de run falen.
ALLOWED_LINKS = {
    "https://account.bitvavo.com/create?a=68DCE39715": True,   # True = sponsored
    "https://replit.com/signup?referral=dglhaket": True,
    "https://www.hostinger.com?REFERRALCODE=UZUDGLHAKW67": True,
    "https://try.turbotic.com/9bsnqewlv0qm": True,
    "https://theweekly2pctedge.com": False,
    "https://aibuildermarketplace.com": False,
    "https://aibuildermarketplace.com/b2b/bitvavo-trading-bot/": False,
    "https://aibuildermarketplace.com/b2b/replit-trading-bot/": False,
    "https://aibuildermarketplace.com/b2b/hostinger-vps-review/": False,
    "https://aibuildermarketplace.com/b2b/turbotic-ai-review/": False,
}

SIDEBARS = {
    "bitvavo": ("bitvavo.com", "Bitvavo", "https://account.bitvavo.com/create?a=68DCE39715", "Open een Bitvavo-account →", True),
    "replit": ("replit.com", "Replit", "https://replit.com/signup?referral=dglhaket", "Bouw je eigen systeem →", True),
    "hostinger": ("hostinger.com", "Hostinger VPS", "https://www.hostinger.com?REFERRALCODE=UZUDGLHAKW67", "Start je eigen VPS →", True),
    "w2e": ("theweekly2pctedge.com", "The Weekly 2% Edge", "https://theweekly2pctedge.com", "Bekijk het live systeem →", False),
}

SYSTEM_PROMPT = """Je schrijft Nederlandstalige artikelen voor theweeklyaiedge.com, in de stem van Daan.

WIE IS DAAN (alleen deze feiten gebruiken, NIETS anders verzinnen):
- 48, Nederlander, 23 jaar gewerkt in de internationale bankenwereld (ex-banker).
- Woont nu met vrouw, zoon en dochter in Saigon (Ho Chi Minh City), Vietnam.
- Bouwde zonder developer-achtergrond een crypto-tradingbot met de AI-agent van Replit,
  gekoppeld aan de API van Bitvavo (EUR/BTC). De bot draait 24/7, heeft een dashboard.
- Runt een eigen AI-agent genaamd Victor op een Hostinger VPS die zijn websites
  in 35 talen onderhoudt (programmatic SEO).
- Sites: aibuildermarketplace.com (B2B-softwaredirectory met reviews),
  theweekly2pctedge.com (volgt zijn eigen live tradingsysteem van week tot week),
  theweeklyaiedge.com (persoonlijke hub, dit is de site waarvoor je schrijft).
- Drijfveer: tijd terugwinnen voor zijn gezin; de techniek doet de corvee.

HARDE REGELS:
1. Verzin NOOIT cijfers, rendementen, percentages, bedragen, productnamen, diensten
   of klantverhalen. Geen beloften over winst. Wat je niet zeker weet, schrijf je niet.
2. Wees eerlijk over risico's en nadelen — dat is de merkstem (E-E-A-T).
3. Geen financieel advies geven; de site voegt zelf een disclaimer toe.
4. Toon: warm, persoonlijk, nuchter Nederlands, eerste persoon ("ik"). Geen hype,
   geen uitroeptekens-spam, geen Amerikaanse marketingtaal.
5. Links: gebruik UITSLUITEND URL's uit de lijst die per opdracht wordt meegegeven,
   als gewone <a href="...">-tags in de lopende tekst waar ze natuurlijk passen
   (2 tot 4 links totaal). Geen andere URL's, ook geen verzonnen interne links.

VORM (body_html):
- 550 à 800 woorden. Alleen deze HTML-elementen: <p>, <h2>, <ul>, <li>, <strong>, <em>, <a>.
- 3 à 4 <h2>-secties met concrete, niet-clickbait koppen.
- Precies één blok: <div class="crosslink-box"><h3>The Edge Perspective</h3><p>...</p></div>
  als een-na-laatste element, met daarin de persoonlijke kern van het verhaal.
- Geen <h1> in de body (de pagina heeft er al een), geen <script>, geen <img>."""

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "description": "SEO-paginatitel, max 60 tekens, zonder site-suffix"},
        "meta_description": {"type": "string", "description": "Meta description, 140-158 tekens, Nederlands"},
        "h1": {"type": "string", "description": "De kop van het artikel"},
        "body_html": {"type": "string", "description": "De artikel-body als HTML volgens de vormregels"},
    },
    "required": ["title", "meta_description", "h1", "body_html"],
    "additionalProperties": False,
}


def run(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True).stdout


def github_token():
    url = run(["git", "-C", str(AIBM_REPO), "remote", "get-url", "origin"]).strip()
    m = re.match(r"https://([^@]+)@github\.com/", url)
    if not m:
        sys.exit("❌ kon geen token uit de aibuildermarketplace-remote halen")
    return m.group(1)


def ensure_repo():
    if not REPO_DIR.exists():
        run(["git", "clone", "-b", BRANCH, f"https://{github_token()}@{GITHUB_REPO}", str(REPO_DIR)])
    run(["git", "-C", str(REPO_DIR), "checkout", BRANCH])
    run(["git", "-C", str(REPO_DIR), "pull", "--ff-only", "origin", BRANCH])


def pick_topic():
    topics = json.loads((REPO_DIR / "pseo_topics.json").read_text(encoding="utf-8"))
    for t in topics:
        if not (REPO_DIR / f"{t['slug']}.html").exists():
            return t
    return None


def generate(topic):
    import anthropic
    client = anthropic.Anthropic()  # leest ANTHROPIC_API_KEY uit de omgeving

    links = "\n".join(f"- {u}" for u in topic["links"])
    user_msg = (
        f"Schrijf het artikel voor slug '{topic['slug']}'.\n"
        f"Werktitel/onderwerp: {topic['onderwerp']}\n"
        f"Invalshoek en aandachtspunten: {topic['invalshoek']}\n"
        f"Toegestane links voor dit artikel (gebruik er 2 à 4, geen andere):\n{links}"
    )
    response = client.messages.create(
        model=MODEL,
        max_tokens=16000,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
        output_config={"format": {"type": "json_schema", "schema": OUTPUT_SCHEMA}},
    )
    text = next(b.text for b in response.content if b.type == "text")
    usage = response.usage
    print(f"   tokens: in={usage.input_tokens} uit={usage.output_tokens}")
    return json.loads(text)


def validate(article, topic):
    body = article["body_html"]
    words = len(re.sub(r"<[^>]+>", " ", body).split())
    if words < 450:
        sys.exit(f"❌ artikel te dun ({words} woorden) — run afgebroken, niets gepubliceerd")
    if re.search(r"<(script|img|h1)\b", body, re.I):
        sys.exit("❌ verboden element in body — run afgebroken")
    allowed = set(topic["links"])
    for href in re.findall(r'href="([^"]+)"', body):
        if href not in allowed:
            sys.exit(f"❌ niet-toegestane link in output: {href} — run afgebroken")
    print(f"   gevalideerd: {words} woorden, links ok")


def esc(s):
    return s.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")


def mark_sponsored(body):
    def fix(m):
        href = m.group(1)
        rel = 'rel="sponsored noopener"' if ALLOWED_LINKS.get(href) else 'rel="noopener"'
        tgt = ' target="_blank"' if href.startswith("http") else ""
        return f'<a href="{href}" {rel}{tgt}>'
    return re.sub(r'<a href="([^"]+)"[^>]*>', fix, body)


def nl_articles():
    out = []
    for f in sorted(REPO_DIR.glob("*.html")):
        h = f.read_text(encoding="utf-8", errors="replace")
        if '<html lang="nl"' in h:
            m = re.search(r"<h1\b[^>]*>(.*?)</h1>", h, re.S)
            naam = re.sub(r"<[^>]+>", "", m.group(1)).split("?")[0].split(":")[0].strip() if m else f.stem
            out.append((f.stem, naam))
    return out


def render(topic, article, date):
    tpl = (REPO_DIR / "runpod.html").read_text(encoding="utf-8")
    css = re.search(r"<style>.*?</style>", tpl, re.S).group(0)
    network = re.search(r'<div class="network-section">.*?</div>\s*</div>', tpl, re.S).group(0)
    slug = topic["slug"]
    url = f"{BASE}/{slug}.html"
    dom, naam, cta_url, cta_txt, sponsored = SIDEBARS[topic["sidebar"]]
    rel = 'rel="sponsored noopener"' if sponsored else 'rel="noopener"'
    title = f'{article["title"]} | The Weekly AI Edge'
    ld = json.dumps({
        "@context": "https://schema.org", "@type": "Article",
        "headline": article["h1"], "inLanguage": "nl", "mainEntityOfPage": url,
        "datePublished": date, "dateModified": date,
        "author": {"@type": "Person", "name": "Daan", "url": "https://aibuildermarketplace.com/about/"},
        "publisher": {"@type": "Organization", "name": "The Weekly AI Edge"},
    }, ensure_ascii=False)
    related = "\n            ".join(
        f'<a href="{s}.html" class="related-card"><img src="https://www.google.com/s2/favicons?domain=theweeklyaiedge.com&sz=128" class="related-icon" alt="{n}"><span class="related-name">{n}</span></a>'
        for s, n in nl_articles() if s != slug
    )
    body = mark_sponsored(article["body_html"])
    disclaimer = DISCLAIMER if topic.get("disclaimer") else ""
    return f"""<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    {css}
  <link rel="canonical" href="{url}">
  <meta name="description" content="{esc(article["meta_description"])}">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(article["meta_description"])}">
  <meta property="og:url" content="{url}">
{GA4}
  <script type="application/ld+json">{ld}</script>
</head>
<body>
    <div class="top-bar">Cutting through the AI hype to find what actually works.</div>
    <nav>
        <a href="/" class="logo"><span class="logo-dot">●</span> The Weekly AI Edge</a>
        <div class="nav-links"><a href="https://aibuildermarketplace.com" target="_blank">Marketplace →</a></div>
    </nav>
    <div class="layout-wrapper">
        <main>
            <h1>{article["h1"]}</h1>
            {body}
            {disclaimer}
        </main>
        <aside class="sticky-sidebar">
            <img src="https://www.google.com/s2/favicons?domain={dom}&sz=128" alt="{naam} logo" class="sidebar-logo">
            <div class="sidebar-title">{naam}</div>
            <a href="{cta_url}" target="_blank" class="btn-sidebar" {rel}>{cta_txt}</a>
            <div style="font-size: 0.75rem; color: #475569;">Affiliate disclosure · Laatst bijgewerkt {date}</div>
        </aside>
    </div>

    <div class="related-tools">
        <h3>Meer Nederlandstalige gidsen</h3>
        <div class="related-grid">
            {related}
        </div>
    </div>

    {network}

    <footer class="footer-strip"><div class="footer-strip-left">© 2026 The Weekly AI Edge.</div><p style="font-size:.75rem;opacity:.6;text-align:center;margin:12px 0">Some links are affiliate links — we may earn a commission at no extra cost to you.</p>
</footer>
</body>
</html>
"""


def update_index(topic, article):
    idx = REPO_DIR / "index.html"
    h = idx.read_text(encoding="utf-8")
    slug = topic["slug"]
    if f'href="{slug}.html"' in h:
        return
    sec_start = h.find('<section id="nl-gidsen"')
    sec_end = h.find("</section>", sec_start)
    if sec_start == -1:
        print("   ⚠️ nl-gidsen-sectie niet gevonden in index — kaart overgeslagen")
        return
    kop = article["h1"].split("?")[0].split(":")[0].strip()
    card = (f'<a href="{slug}.html" class="bg-slate-900/50 border border-slate-800 rounded-xl p-6 '
            f'hover:border-sky-500 transition-all duration-300 block">'
            f'<h3 class="text-lg font-bold text-white mb-2">{kop} &rarr;</h3>'
            f'<p class="text-sm text-slate-400">{esc(article["meta_description"])[:110]}</p></a>')
    section = h[sec_start:sec_end]
    insert_at = section.rfind("</a>")
    if insert_at == -1:
        return
    section = section[: insert_at + 4] + "\n                " + card + section[insert_at + 4:]
    idx.write_text(h[:sec_start] + section + h[sec_end:], encoding="utf-8")


def update_sitemap(slug):
    sm = REPO_DIR / "sitemap.xml"
    h = sm.read_text(encoding="utf-8")
    loc = f"{BASE}/{slug}.html"
    if loc not in h:
        sm.write_text(h.replace("</urlset>", f"  <url><loc>{loc}</loc></url>\n</urlset>"), encoding="utf-8")


def main():
    apply = "--apply" in sys.argv
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("❌ ANTHROPIC_API_KEY niet gezet. Zet hem in /root/felix_hq/.env en source die.")
    import datetime
    date = datetime.date.today().isoformat()

    ensure_repo()
    topic = pick_topic()
    if topic is None:
        print("alle onderwerpen zijn al geschreven — voeg nieuwe toe aan pseo_topics.json")
        return
    print(f"▶ genereren: {topic['slug']} ({MODEL})")
    article = generate(topic)
    validate(article, topic)

    page = render(topic, article, date)
    (REPO_DIR / f"{topic['slug']}.html").write_text(page, encoding="utf-8")
    update_index(topic, article)
    update_sitemap(topic["slug"])
    print(f"   geschreven: {topic['slug']}.html + indexkaart + sitemap")

    if not apply:
        print("\nDRY-RUN — lokaal geschreven, NIET gecommit/gepusht.")
        print(f"   bekijk: {REPO_DIR}/{topic['slug']}.html")
        print("   publiceren: zelfde commando met --apply (of commit handmatig)")
        return
    run(["git", "-C", str(REPO_DIR), "add", "-A"])
    run(["git", "-C", str(REPO_DIR), "commit", "-m", f"pSEO v2: {topic['slug']} (Claude, gevalideerd)"])
    run(["git", "-C", str(REPO_DIR), "push", "origin", BRANCH])
    print(f"✅ gepubliceerd: {BASE}/{topic['slug']}.html (live na Pages-deploy)")


if __name__ == "__main__":
    main()
