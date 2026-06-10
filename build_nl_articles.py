#!/usr/bin/env python3
"""Genereert de Nederlandstalige gidsen (herschreven versies van Victors
pSEO-stubs van de main-branch) in de site-stijl van theweeklyaiedge.com.
Idempotent: draait gewoon opnieuw bij contentwijzigingen hieronder.

Gebruik: python3 build_nl_articles.py
"""
import json
import re
from pathlib import Path

BASE = "https://theweeklyaiedge.com"
DATE = "2026-06-10"

GA4 = """  <script async src="https://www.googletagmanager.com/gtag/js?id=G-CW1KZ258ZV"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', 'G-CW1KZ258ZV');
  </script>"""

DISCLAIMER = """<p style="font-size:.85rem;color:#64748b;border:1px solid var(--border);border-radius:8px;padding:1rem;margin-top:2.5rem"><strong style="color:#94a3b8">Disclaimer:</strong> dit artikel deelt mijn persoonlijke ervaring en is geen financieel advies. Crypto en gehandelde producten zijn risicovol — koersen kunnen hard dalen en een systeem dat in het verleden werkte, biedt geen garantie voor de toekomst. Handel alleen met geld dat je kunt missen.</p>"""

ARTICLES = {
    "algoritmisch-traden": {
        "title": "Wat is algoritmisch traden? Uitleg van een ex-bankier | The Weekly AI Edge",
        "desc": "Algoritmisch traden uitgelegd zonder hype, door iemand die 23 jaar in de bankenwereld zat en nu zijn eigen bot 24/7 laat draaien. Wat het is, wat het niet is, en hoe je begint.",
        "h1": "Wat is algoritmisch traden? Uitleg van een ex-bankier",
        "sidebar": ("bitvavo.com", "Bitvavo", "https://account.bitvavo.com/create?a=68DCE39715", "Open een Bitvavo-account →", True),
        "disclaimer": True,
        "body": """
            <p>Ik heb 23 jaar in de internationale bankenwereld gewerkt, en als er één ding is dat ik daar heb geleerd, dan is het dit: de meeste handelsbeslissingen die mensen nemen, worden niet door analyse gestuurd maar door emotie. Algoritmisch traden is in de kern niets anders dan die emotie uit de vergelijking halen: je schrijft je regels van tevoren op, en een computer voert ze uit. Elke keer hetzelfde, zonder twijfel, zonder paniek, zonder FOMO.</p>
            <h2>Wat een handelsalgoritme wél is</h2>
            <p>Een handelsalgoritme is een set afspraken met jezelf, vertaald naar code. Bijvoorbeeld: onder welke voorwaarden je koopt, wanneer je verkoopt, hoeveel kapitaal je per positie inzet en wat je maximale verlies per dag mag zijn. Mijn eigen systeem draait op <a href="https://aibuildermarketplace.com/b2b/replit-trading-bot/" target="_blank">een bot die ik met de AI-agent van Replit heb gebouwd</a>, gekoppeld aan <a href="https://aibuildermarketplace.com/b2b/bitvavo-trading-bot/" target="_blank">de API van Bitvavo</a>. De bot leest de markt, plaatst orders en houdt zich aan de regels — 24 uur per dag, ook als ik met mijn gezin in Saigon op pad ben.</p>
            <h2>Wat het níét is</h2>
            <p>Laten we eerlijk zijn, want daar ontbreekt het nogal eens aan in deze hoek van het internet: een algoritme is geen geldmachine. Het voorspelt de markt niet. Het enige dat een goed systeem doet, is een kleine, vooraf gedefinieerde edge consistent uitvoeren en je grootste vijand — jijzelf, om drie uur 's nachts, starend naar een rode grafiek — buitenspel zetten. Een slecht systeem voert ook consistent uit: het verliest dan consistent. De kwaliteit van je regels bepaalt alles.</p>
            <h2>De drie bouwstenen</h2>
            <ul>
                <li><strong>Een exchange met een goede API.</strong> Ik gebruik Bitvavo: EU-gereguleerd, eurorekening, en een uitstekend gedocumenteerde API. Belangrijk: geef je API-sleutels alléén handelsrechten, nooit opnamerechten.</li>
                <li><strong>Een plek waar je code draait.</strong> Mijn bot draait op Replit en wordt daar 24/7 gehost. Je kunt ook een eigen VPS gebruiken — daarover meer in <a href="ai-agent-kopen.html">mijn artikel over AI-agents</a>.</li>
                <li><strong>Regels die je begrijpt.</strong> Dit is de belangrijkste. Ik bespreek mijn handelsstrategieën met een AI-assistent, lees er boeken over en laat pas iets live gaan als ik élke regel zelf kan uitleggen. Code die je niet begrijpt, is geen systeem maar een gok.</li>
            </ul>
            <div class="crosslink-box">
                <h3>The Edge Perspective</h3>
                <p>Het mooiste van algoritmisch traden is niet het rendement — het is de rust. Mijn dashboard vertelt me in één oogopslag wat het systeem doet, en de rest van de dag ben ik gewoon vader, geen daytrader. Wil je zien hoe zo'n systeem er in de praktijk uitziet? Op <a href="https://theweekly2pctedge.com" target="_blank">The Weekly 2% Edge</a> volg ik mijn eigen systeem van week tot week.</p>
            </div>
            <h2>Zo begin je (zonder jezelf op te blazen)</h2>
            <p>Begin op papier: schrijf je regels uit voordat je ook maar één regel code schrijft. Test daarna met bedragen die je pijnloos kunt verliezen. Verhoog pas als het systeem zich maanden — niet dagen — bewezen heeft. En automatiseer je risicobeheer eerst, je instaplogica daarna; de meeste mensen doen het andersom en dat is precies de verkeerde volgorde.</p>"""
    },
    "emotieloos-crypto-traden": {
        "title": "Emotieloos crypto traden: waarom mijn bot beter slaapt dan ik | The Weekly AI Edge",
        "desc": "Niemand kan de markt voorspellen. Wat wél kan: een vast systeem dat zonder emotie je regels uitvoert. Mijn ervaring na maanden 24/7 geautomatiseerd handelen op Bitvavo.",
        "h1": "Emotieloos crypto traden: waarom mijn bot beter slaapt dan ik",
        "sidebar": ("bitvavo.com", "Bitvavo", "https://account.bitvavo.com/create?a=68DCE39715", "Open een Bitvavo-account →", True),
        "disclaimer": True,
        "body": """
            <p>Het eerlijke verhaal: in mijn jaren als banker heb ik getalenteerde, hoogopgeleide professionals de domste handelsbeslissingen zien nemen — niet omdat ze de kennis misten, maar omdat een dalende markt iets met je hoofd doet. Angst en hebzucht zijn geen karakterfouten; het is menselijke bedrading. En precies daarom heb ik het handelen uitbesteed aan iets zonder bedrading: een bot.</p>
            <h2>Waarom voorspellen niet werkt (en regels wel)</h2>
            <p>Niemand kan de markt voorspellen. Niet de analisten op TV, niet de goeroes op YouTube, en jij en ik al helemaal niet. Wat je wél kunt: vooraf bepalen hoe je reageert op wat de markt doet. Dat is het hele verschil tussen gokken en systematisch handelen. Mijn systeem heeft geen mening over waar Bitcoin "naartoe gaat". Het heeft regels: bij situatie A doen we B, met maximaal C aan risico. Elke dag, elke nacht, zonder uitzondering.</p>
            <h2>Wat er verandert als de emotie eruit gaat</h2>
            <ul>
                <li><strong>Geen schermverslaving meer.</strong> Vroeger checkte ik koersen tijdens het eten, op het toilet, midden in de nacht. Nu kijk ik één keer per dag op mijn dashboard — dat naast mijn bed staat, dat dan weer wel.</li>
                <li><strong>Drawdowns worden data in plaats van drama.</strong> Een verliesperiode betekent niet meer "paniek en alles verkopen", maar "het systeem houdt zich aan zijn maximale risico, precies zoals afgesproken".</li>
                <li><strong>Consistentie verslaat heldenmoed.</strong> Langzaam compounden met een kleine, vaste edge voelt saai. Saai is precies de bedoeling.</li>
            </ul>
            <h2>Mijn setup in twee zinnen</h2>
            <p>Een bot, gebouwd met <a href="https://aibuildermarketplace.com/b2b/replit-trading-bot/" target="_blank">de AI-agent van Replit</a> (ik heb geen developer-achtergrond), handelt via <a href="https://aibuildermarketplace.com/b2b/bitvavo-trading-bot/" target="_blank">de API van Bitvavo</a> in euro en Bitcoin. Een dashboard laat me kapitaal, posities, beslissingen en resultaat zien — en waarschuwt me als een strategie hapert, zodat ik alleen hoef in te grijpen als het echt nodig is.</p>
            <div class="crosslink-box">
                <h3>The Edge Perspective</h3>
                <p>De grootste winst van emotieloos traden staat op geen enkel dashboard: ik slaap weer. Geen nachten meer wakker liggen of de markt crasht — de bot heeft geen slaap nodig en geen zenuwen. Volg op <a href="https://theweekly2pctedge.com" target="_blank">The Weekly 2% Edge</a> hoe mijn systeem week na week zijn werk doet.</p>
            </div>
            <h2>De valkuil: emotie sluipt terug via de achterdeur</h2>
            <p>Eén waarschuwing uit eigen ervaring: het gevaarlijkste moment is niet het bouwen van je systeem, maar de verleiding om "even handmatig in te grijpen" als het tegenzit. Op het moment dat je je bot overrulet, ben je weer gewoon een emotionele handelaar — alleen nu eentje met een duur excuus. Vertrouw je je regels niet meer? Zet het systeem dan stil, evalueer rustig, en pas de regels aan. Maar handel er niet doorheen.</p>"""
    },
    "passief-inkomen-crypto": {
        "title": "Passief inkomen met crypto-systemen: de eerlijke versie | The Weekly AI Edge",
        "desc": "Kan een crypto-bot passief inkomen opleveren? Soort van — maar niet zoals de goeroes beweren. Wat er echt komt kijken bij een systeem dat zelfstandig draait.",
        "h1": "Passief inkomen met crypto-systemen: de eerlijke versie",
        "sidebar": ("replit.com", "Replit", "https://replit.com/signup?referral=dglhaket", "Bouw je eigen systeem →", True),
        "disclaimer": True,
        "body": """
            <p>"Passief inkomen" is misschien wel de meest misbruikte term op het internet, dus laat ik beginnen met wat het níét is: gratis geld terwijl je slaapt. Wat het in mijn geval wél is: een handelssysteem dat zelfstandig draait, dat ik heb gebouwd in avonduren op een balkon in Ho Chi Minh City, en dat sindsdien mijn aandacht alleen nog nodig heeft voor onderhoud en verbetering. Dat is geen passiviteit — dat is vooraf geïnvesteerd werk dat zich daarna laat herhalen.</p>
            <h2>De wiskunde achter een "vaste edge"</h2>
            <p>Het idee is simpel: je zoekt geen jackpot maar een kleine, herhaalbare voorsprong, en je laat die consistent zijn werk doen. Een wekelijkse doelstelling halen is dan geen kwestie van voorspellen, maar van uitvoeren: structureel de markt analyseren, klein en gedisciplineerd inzetten, verliezen begrenzen en winsten laten compounden. Saai? Absoluut. Maar saai en herhaalbaar wint het op termijn van spectaculair en eenmalig.</p>
            <h2>Wat je daadwerkelijk bouwt</h2>
            <ul>
                <li><strong>Een exchange-koppeling.</strong> Mijn bot handelt via <a href="https://aibuildermarketplace.com/b2b/bitvavo-trading-bot/" target="_blank">de API van Bitvavo</a> — EU-gereguleerd en euro-gebaseerd, wat het voor een Europeaan aanzienlijk eenvoudiger maakt.</li>
                <li><strong>Een draaiende machine.</strong> De code zelf bouwde ik met <a href="https://aibuildermarketplace.com/b2b/replit-trading-bot/" target="_blank">de AI-agent van Replit</a>, waar hij ook 24/7 gehost wordt. Programmeerervaring had ik niet; discussiëren met een AI over handelsregels kan iedereen leren.</li>
                <li><strong>Een dashboard dat je vertrouwt.</strong> Kapitaal, posities, beslissingen, resultaat — in één oogopslag. Zonder zicht op wat je systeem doet, is "passief" gewoon een ander woord voor "blind".</li>
            </ul>
            <div class="crosslink-box">
                <h3>The Edge Perspective</h3>
                <p>Het werkelijke passieve inkomen zit niet in de trades — het zit in de uren die ik terugkrijg. Geen grafieken staren, geen koersen checken tijdens het avondeten. Het systeem werkt, ik leef. De wekelijkse voortgang van mijn eigen systeem deel ik open en eerlijk op <a href="https://theweekly2pctedge.com" target="_blank">The Weekly 2% Edge</a>.</p>
            </div>
            <h2>De kosten die niemand noemt</h2>
            <p>Voor het eerlijke plaatje: een systeem draaien kost geld. Hosting, handelskosten per transactie (die bij Bitvavo overigens dalen naarmate je volume stijgt — een prettige bijkomstigheid van geautomatiseerd handelen), en vooral: leergeld. Reken erop dat je eerste versie niet je beste versie is. Begin met een bedrag waarvan je het verlies kunt dragen als collegegeld, niet met je spaargeld. En wantrouw iedereen die je het tegenovergestelde vertelt.</p>"""
    },
    "prop-firm-bot": {
        "title": "Prop firm bot: kan een algoritme je evaluatie halen? | The Weekly AI Edge",
        "desc": "Prop firms beloven gefinancierde accounts na een evaluatie. Kan een handelsbot die discipline-test voor je doen? Wat wel kan, wat niet mag, en waar je op moet letten.",
        "h1": "Prop firm bot: kan een algoritme je evaluatie halen?",
        "sidebar": ("theweekly2pctedge.com", "The Weekly 2% Edge", "https://theweekly2pctedge.com", "Bekijk het live systeem →", False),
        "disclaimer": True,
        "body": """
            <p>Prop firms — bedrijven die je na een betaalde evaluatie een "gefinancierd account" geven — zijn enorm populair geworden. Het idee klinkt aantrekkelijk: bewijs dat je gedisciplineerd kunt handelen, en je handelt daarna met hun kapitaal in plaats van het jouwe. En omdat zo'n evaluatie vooral een test van discipline is, duikt steeds vaker de vraag op: kan een bot dat niet veel beter dan ik?</p>
            <h2>Waarom een algoritme hier in theorie sterk is</h2>
            <p>Een prop-firm-evaluatie is in essentie een risicobeheer-examen: haal een winstdoel zonder de maximale dagverlies- en totaalverliesgrenzen te raken. Dat is precies waar systematisch handelen in uitblinkt. Een algoritme kent geen wraaktrades na een verlies, vergroot zijn positie niet uit frustratie en stopt gewoon met handelen als de dagrisicolimiet in zicht komt. De eigenschappen die mensen door evaluaties laten zakken — ongeduld, overmoed, paniek — heeft een bot simpelweg niet.</p>
            <h2>De grote MAAR: lees de regels</h2>
            <p>Hier moet ik streng zijn, want hier gaat het mis op internet: <strong>veel prop firms verbieden volledig geautomatiseerd handelen</strong>, of staan het alleen toe onder voorwaarden (eigen code wel, gekochte "passing bots" niet — die laatste zijn vrijwel altijd tegen de regels én vaak gewoon oplichterij). Wie betrapt wordt, verliest zijn account en zijn evaluatiegeld. Controleer dus vóór je ook maar iets bouwt de voorwaarden van de specifieke firm, en vraag het bij twijfel schriftelijk na. Een "geheime bot die elke evaluatie haalt" kopen van een onbekende op Telegram is geen strategie, het is een donatie.</p>
            <h2>De zinvolle route</h2>
            <ul>
                <li><strong>Bouw je eigen systeem en begrijp het volledig.</strong> Ik bouwde mijn handelsbot met <a href="https://aibuildermarketplace.com/b2b/replit-trading-bot/" target="_blank">de AI-agent van Replit</a> zonder developer-achtergrond — de drempel is lager dan je denkt.</li>
                <li><strong>Bewijs je edge eerst op eigen (klein) kapitaal.</strong> Een systeem dat op je eigen rekening geen maanden overleeft, gaat een evaluatie ook niet halen. Ik draai zelf live via <a href="https://aibuildermarketplace.com/b2b/bitvavo-trading-bot/" target="_blank">Bitvavo</a>.</li>
                <li><strong>Behandel risicolimieten als heilig.</strong> Codeer de evaluatieregels (max dagverlies, max totaalverlies) hard in je systeem — niet als richtlijn maar als noodstop.</li>
            </ul>
            <div class="crosslink-box">
                <h3>The Edge Perspective</h3>
                <p>Mijn eerlijke kijk: de discipline die je nodig hebt om een evaluatie te halen, is dezelfde discipline die een systeem je oplevert op je eigen rekening — zonder andermans regels en zonder evaluatiekosten. Hoe dat eruitziet, laat ik wekelijks zien op <a href="https://theweekly2pctedge.com" target="_blank">The Weekly 2% Edge</a>.</p>
            </div>"""
    },
    "ai-agent-kopen": {
        "title": "Een AI-agent kopen? Wat je écht nodig hebt (en wat het kost) | The Weekly AI Edge",
        "desc": "Kant-en-klare AI-agents kopen klinkt aantrekkelijk. Maar mijn agent Victor, die mijn sites in 35 talen onderhoudt, bouwde ik zelf — goedkoper en beter. Zo werkt dat.",
        "h1": "Een AI-agent kopen? Wat je écht nodig hebt (en wat het kost)",
        "sidebar": ("hostinger.com", "Hostinger VPS", "https://www.hostinger.com?REFERRALCODE=UZUDGLHAKW67", "Start je eigen VPS →", True),
        "disclaimer": False,
        "body": """
            <p>Er wordt op dit moment veel geld verdiend aan de belofte "koop deze AI-agent en je business draait vanzelf". Ik run zelf een autonome AI-agent — hij heet Victor, hij onderhoudt mijn websites in 35 talen terwijl ik met mijn gezin in Saigon woon — dus je zou verwachten dat ik die belofte onderschrijf. Het tegendeel is waar: Victor is niet gekocht. Hij is gebouwd. En dat is precies waarom hij werkt.</p>
            <h2>Wat een AI-agent eigenlijk is</h2>
            <p>Vergeet de robotplaatjes. Een AI-agent is een programma dat zelfstandig taken uitvoert door een taalmodel te combineren met toegang tot jouw systemen: je server, je git-repository, je content-pijplijn. Victor draait op <a href="https://aibuildermarketplace.com/b2b/hostinger-vps-review/" target="_blank">een Hostinger VPS</a> — denk aan een eigen computer in de cloud die nooit uitgaat — en doet daar via geplande taken zijn werk: artikelen genereren, vertalen, publiceren, fouten zelf herstellen.</p>
            <h2>Waarom "kopen" meestal tegenvalt</h2>
            <ul>
                <li><strong>Een generieke agent kent jouw business niet.</strong> De waarde zit niet in de agent maar in de afspraken: wát hij doet, wanneer, en wat hij moet doen als iets misgaat. Dat is maatwerk per definitie.</li>
                <li><strong>Je betaalt voor een black box.</strong> Als een gekochte agent stukgaat — en alles gaat ooit stuk — kun je hem niet repareren. Mijn eigen scripts kan ik (met hulp van AI) lezen, begrijpen en aanpassen.</li>
                <li><strong>De echte kosten zitten elders.</strong> Een agent draaien kost een VPS-abonnement plus API-kosten voor het taalmodel. Dat betaal je óók als je een "kant-en-klare" agent koopt — alleen dan met marge erbovenop.</li>
            </ul>
            <h2>Hoe je er zelf één bouwt (zonder developer te zijn)</h2>
            <p>Ik heb 23 jaar in de bankenwereld gezeten en kan niet klassiek programmeren. Mijn route: ik beschrijf in gewone taal aan een AI-codeerassistent (Claude Code, of de agent van Replit) wat ik wil, plak de gegenereerde code in de terminal van mijn VPS, en test. Stap voor stap groeit dat uit tot een agent die zelfstandig draait. De bouwstenen: een <a href="https://aibuildermarketplace.com/b2b/hostinger-vps-review/" target="_blank">VPS</a> (een paar euro per maand), een AI-assistent om mee te bouwen, en geduld. Mijn complete setup beschrijf ik in <a href="ai-p-seo.html">het artikel over mijn content-machine</a>.</p>
            <div class="crosslink-box">
                <h3>The Edge Perspective</h3>
                <p>De vraag is niet "waar koop ik een AI-agent" maar "welke taak wil ik nooit meer zelf doen". Begin daar, bouw klein, en laat de agent meegroeien. De tools die ik daarvoor gebruik en eerlijk heb gereviewd, vind je op <a href="https://aibuildermarketplace.com" target="_blank">AI Builder Marketplace</a>.</p>
            </div>"""
    },
    "ai-p-seo": {
        "title": "AI + programmatic SEO: hoe mijn content-machine draait | The Weekly AI Edge",
        "desc": "Mijn AI-agent Victor genereert en onderhoudt honderden reviewpagina's in 35 talen — vanaf een VPS, zonder team. De architectuur, de lessen en de valkuilen van AI-pSEO.",
        "h1": "AI + programmatic SEO: hoe mijn content-machine draait",
        "sidebar": ("hostinger.com", "Hostinger VPS", "https://www.hostinger.com?REFERRALCODE=UZUDGLHAKW67", "Start je eigen VPS →", True),
        "disclaimer": False,
        "body": """
            <p>Programmatic SEO — content op schaal genereren voor long-tail zoekopdrachten — heeft een slechte naam, en vaak terecht: het internet stroomt vol met lege AI-pagina's die niemand helpen. Toch draait mijn eigen pSEO-machine al maanden, in 35 talen, grotendeels zonder dat ik ernaar omkijk. Het verschil zit niet in de techniek maar in de uitgangspunten. Dit is hoe de machine werkt — inclusief de lessen die me tijd en geld hebben gekost.</p>
            <h2>De architectuur in het kort</h2>
            <ul>
                <li><strong>Een VPS als thuisbasis.</strong> Alles draait op <a href="https://aibuildermarketplace.com/b2b/hostinger-vps-review/" target="_blank">een Hostinger VPS</a>: mijn agent Victor, de generators, de geplande taken. Geen laptop die aan moet staan, geen afhankelijkheid van mijn aanwezigheid.</li>
                <li><strong>Generators in plaats van losse pagina's.</strong> Eén template + één databron = honderden consistente pagina's. Pas je het template aan, dan verbetert álles tegelijk.</li>
                <li><strong>GitHub als ruggengraat.</strong> Victor pusht naar een staging-branch; een uurlijkse controle promoot alleen wat door de checks komt naar de live site. Fouten bereiken de bezoeker zelden.</li>
                <li><strong>Zelfherstellende taken.</strong> De belangrijkste les: bouw geen scripts die één keer fixen, maar terugkerende taken die élke run controleren en repareren — dubbele koppen, ontbrekende vertalingen, kapotte metadata. De machine onderhoudt zichzelf.</li>
            </ul>
            <h2>Wat AI-pSEO laat werken (en wat niet)</h2>
            <p>Wat niet werkt: kale AI-tekst zonder eigen ervaring of data erin. Google prikt erdoorheen en je lezer ook. Wat wél werkt: programmatische schaal combineren met echte, eerstehands inhoud — mijn reviews zijn gebaseerd op tools die ik zelf gebruik, geschreven vanuit een herkenbare auteur met een echt verhaal. De machine schaalt de distributie; de geloofwaardigheid moet van jou komen. En vergeet de talen niet: dezelfde review in 35 talen aanbieden (met nette hreflang-clusters) was voor mij de grootste onderschatte hefboom.</p>
            <h2>De eerlijke kosten en valkuilen</h2>
            <p>Reken op: VPS-kosten (een paar euro per maand), API-kosten voor het taalmodel, en vooral leertijd. Mijn duurste lessen: hardcoded API-sleutels in code die per ongeluk publiek werd (roteer je sleutels, gebruik environment-variabelen), en generators die maandenlang een subtiele fout herhaalden op elke pagina voordat ik het zag. Monitor je output — een machine maakt ook fouten op schaal.</p>
            <div class="crosslink-box">
                <h3>The Edge Perspective</h3>
                <p>De machine is geen doel maar een middel: zij doet de digitale corvee, zodat ik mijn middagen kan afsluiten en bij mijn gezin kan zijn. Wil je zien wat zo'n systeem aan output levert? Kijk op <a href="https://aibuildermarketplace.com" target="_blank">AI Builder Marketplace</a> — volledig door Victor onderhouden. Hoe ik hem bouwde lees je in <a href="ai-agent-kopen.html">het artikel over AI-agents</a>.</p>
            </div>"""
    },
}

NL_SLUGS = list(ARTICLES.keys())


def related_grid(current_slug):
    cards = []
    for slug, a in ARTICLES.items():
        if slug == current_slug:
            continue
        naam = a["h1"].split("?")[0].split(":")[0].strip()
        cards.append(
            f'<a href="{slug}.html" class="related-card"><img src="https://www.google.com/s2/favicons?domain=theweeklyaiedge.com&sz=128" class="related-icon" alt="{naam}"><span class="related-name">{naam}</span></a>'
        )
    cards.append('<a href="https://aibuildermarketplace.com/b2b/bitvavo-trading-bot/" target="_blank" class="related-card"><img src="https://www.google.com/s2/favicons?domain=bitvavo.com&sz=128" class="related-icon" alt="Bitvavo"><span class="related-name">Bitvavo Review</span></a>')
    cards.append('<a href="https://aibuildermarketplace.com/b2b/replit-trading-bot/" target="_blank" class="related-card"><img src="https://www.google.com/s2/favicons?domain=replit.com&sz=128" class="related-icon" alt="Replit"><span class="related-name">Replit Review</span></a>')
    return "\n            ".join(cards)


def build():
    root = Path(__file__).parent
    tpl = (root / "runpod.html").read_text(encoding="utf-8")
    css = re.search(r"<style>.*?</style>", tpl, re.S).group(0)
    network = re.search(r'<div class="network-section">.*?</div>\s*</div>', tpl, re.S).group(0)

    for slug, a in ARTICLES.items():
        url = f"{BASE}/{slug}.html"
        dom, naam, cta_url, cta_txt, sponsored = a["sidebar"]
        rel = 'rel="sponsored noopener"' if sponsored else 'rel="noopener"'
        ld = json.dumps({
            "@context": "https://schema.org", "@type": "Article",
            "headline": a["h1"], "inLanguage": "nl", "mainEntityOfPage": url,
            "datePublished": DATE, "dateModified": DATE,
            "author": {"@type": "Person", "name": "Daan", "url": "https://aibuildermarketplace.com/about/"},
            "publisher": {"@type": "Organization", "name": "The Weekly AI Edge"},
        }, ensure_ascii=False)
        disclaimer = DISCLAIMER if a["disclaimer"] else ""
        page = f"""<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{a["title"]}</title>
    {css}
  <link rel="canonical" href="{url}">
  <meta name="description" content="{a["desc"]}">
  <meta property="og:title" content="{a["title"]}">
  <meta property="og:description" content="{a["desc"]}">
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
            <h1>{a["h1"]}</h1>{a["body"]}
            {disclaimer}
        </main>
        <aside class="sticky-sidebar">
            <img src="https://www.google.com/s2/favicons?domain={dom}&sz=128" alt="{naam} logo" class="sidebar-logo">
            <div class="sidebar-title">{naam}</div>
            <a href="{cta_url}" target="_blank" class="btn-sidebar" {rel}>{cta_txt}</a>
            <div style="font-size: 0.75rem; color: #475569;">Affiliate disclosure · Laatst bijgewerkt {DATE}</div>
        </aside>
    </div>

    <div class="related-tools">
        <h3>Meer Nederlandstalige gidsen</h3>
        <div class="related-grid">
            {related_grid(slug)}
        </div>
    </div>

    {network}

    <footer class="footer-strip"><div class="footer-strip-left">© 2026 The Weekly AI Edge.</div><p style="font-size:.75rem;opacity:.6;text-align:center;margin:12px 0">Some links are affiliate links — we may earn a commission at no extra cost to you.</p>
</footer>
</body>
</html>
"""
        (root / f"{slug}.html").write_text(page, encoding="utf-8")
        print(f"geschreven: {slug}.html")


if __name__ == "__main__":
    build()
