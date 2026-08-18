#!/usr/bin/env python3
"""[DB-015] shop_seo.py — the shop hub's below-grid SEO/GEO copy + FAQPage schema.
DOES:   holds the trilingual lead/FAQ/description strings and builds both the
        visible section and its FAQPage JSON-LD from the SAME strings, with the
        catalogue numbers filled at build time.

shop_seo.py
The shop hub's below-the-grid SEO/GEO section (geo lead + 5-question FAQ) and the
matching FAQPage JSON-LD. Used by gen_shop_index.py.

Rules:
 - Visible text and FAQPage text are built from the SAME strings (Google's
   visible-content rule; the GSC incident taught us to never let them diverge).
 - Counts and the price range are computed from watches.json at build time so the
   copy can never go stale.
 - Facts only: COD, free 3-7 day delivery, 1-year guarantee, 30-day in-store
   returns, Mon-Sat 8:30-20:30, Rruga Aleksander Goga. All owner-established.
 - Placement is BELOW the grid. Nothing is ever added above it (brand-strip lesson).
"""

from contact import phone  # [CFG-010] the number is a language question now

# Each block below is already one language, so each simply asks for its own.
# en/it reach the owner; sq reaches his father, who speaks only Albanian.

COPY = {
    "en": {
        "lead": ("Every watch on this page is in stock at our shop on Rruga Aleksander Goga in "
                 "Durrës: watches from {b} brands, €{lo} to €{hi}, each brand new with a 1-year "
                 "guarantee. Try them on Monday to Saturday, 8:30 to 20:30, or order on WhatsApp "
                 "with cash on delivery in Tirana, Shkodër, Vlorë, Elbasan, Korçë and anywhere "
                 "else in Albania."),
        "faq_h": "Buying a watch from us",
        "faq": [
            ("Can I order a watch online in Albania?",
             "Yes. Pick a watch on this page and message us on WhatsApp at " + phone("en")["text"] + ". We "
             "deliver anywhere in Albania with cash on delivery, so you pay when the watch "
             "arrives. Delivery is free and normally takes 3 to 7 days."),
            ("Do you deliver watches to Tirana?",
             "Yes, and to every other city. Orders go out to Tirana, Shkodër, Vlorë, Elbasan, "
             "Korçë and the rest of Albania with cash on delivery. You can also reserve a watch "
             "on WhatsApp and collect it at the shop in Durrës."),
            ("How much do your watches cost?",
             "From €{lo} to €{hi}, which is roughly {lolek} to {hilek} Lek. Most models are under "
             "€100. We stock {b} brands, including Navimarine, Daniel Klein, Hislon and Philippe "
             "Lauren, all brand new."),
            ("Can I try a watch on before buying?",
             "Of course. The shop is on Rruga Aleksander Goga in Durrës, open Monday to Saturday "
             "from 8:30 to 20:30, no appointment needed. Every watch on this page is physically "
             "in the shop."),
            ("Do you also repair watches?",
             "Yes, the same workshop repairs watches: battery changes in under 2 minutes while "
             "you wait, straps, crystals and full servicing, Monday to Saturday from 8:30 to "
             "20:30."),
            ("What guarantee do the watches come with?",
             "Every watch we sell carries our own 1-year guarantee, and you have 30 days to "
             "return it in store if it is not right. The watches are brand new and unused."),
        ],
        "desc": ("Brand-new watches from €{lo}, most under €100, with a 1-year guarantee. Order "
                 "on WhatsApp with cash on delivery in Tirana and across Albania, or try them on "
                 "in Durrës."),
        "biz_desc": ("Family-owned watch shop and repair workshop in Durrës, Albania since 2009. "
                     "Brand-new watches from {b} brands for sale, expert watch repair, and "
                     "key cutting."),
        "coll_desc": ("Brand-new watches from {b} brands at Iglisi Watch in Durrës, Albania, "
                      "€{lo} to €{hi}, each with a 1-year shop guarantee. Cash on delivery "
                      "across Albania."),
    },
    "it": {
        "lead": ("Ogni orologio in questa pagina è disponibile nel nostro negozio in Rruga "
                 "Aleksander Goga a Durazzo: orologi di {b} marchi, da €{lo} a €{hi}, tutti "
                 "nuovi con garanzia di 1 anno. Provateli dal lunedì al sabato, dalle 8:30 alle "
                 "20:30, oppure ordinate su WhatsApp con pagamento alla consegna a Tirana, "
                 "Scutari, Valona, Elbasan, Coriza e ovunque in Albania."),
        "faq_h": "Comprare un orologio da noi",
        "faq": [
            ("Posso ordinare un orologio online in Albania?",
             "Sì. Scegliete un orologio in questa pagina e scriveteci su WhatsApp al " + phone("it")["text"] +
             ". Consegniamo in tutta l'Albania con pagamento alla consegna, quindi pagate "
             "quando l'orologio arriva. La consegna è gratuita e richiede di norma da 3 a 7 giorni."),
            ("Consegnate orologi a Tirana?",
             "Sì, e in ogni altra città. Gli ordini partono per Tirana, Scutari, Valona, Elbasan, "
             "Coriza e il resto dell'Albania con pagamento alla consegna. Potete anche riservare "
             "un orologio su WhatsApp e ritirarlo in negozio a Durazzo."),
            ("Quanto costano i vostri orologi?",
             "Da €{lo} a €{hi}, circa da {lolek} a {hilek} Lek. La maggior parte dei modelli è "
             "sotto i €100. Teniamo {b} marchi, tra cui Navimarine, Daniel Klein, Hislon e "
             "Philippe Lauren, tutti nuovi."),
            ("Posso provare un orologio prima di comprarlo?",
             "Certo. Il negozio è in Rruga Aleksander Goga a Durazzo, aperto dal lunedì al sabato "
             "dalle 8:30 alle 20:30, senza appuntamento. Ogni orologio di questa pagina è "
             "fisicamente in negozio."),
            ("Riparate anche orologi?",
             "Sì, lo stesso laboratorio ripara orologi: cambio batteria in meno di 2 minuti "
             "mentre aspettate, cinturini, vetri e revisioni complete, dal lunedì al sabato "
             "dalle 8:30 alle 20:30."),
            ("Che garanzia hanno gli orologi?",
             "Ogni orologio che vendiamo ha la nostra garanzia di 1 anno, e avete 30 giorni per "
             "restituirlo in negozio se non va bene. Gli orologi sono nuovi e mai usati."),
        ],
        "desc": ("Orologi nuovi da €{lo}, la maggior parte sotto €100, con garanzia 1 anno. "
                 "Ordina su WhatsApp con pagamento alla consegna a Tirana e in tutta l'Albania, "
                 "o provali a Durazzo."),
        "biz_desc": ("Negozio di orologi e laboratorio di riparazione a conduzione familiare a "
                     "Durazzo, Albania, dal 2009. Orologi nuovi di {b} marchi in vendita, "
                     "riparazioni esperte e duplicazione chiavi."),
        "coll_desc": ("Orologi nuovi di {b} marchi da Iglisi Watch a Durazzo, Albania, da "
                      "€{lo} a €{hi}, ognuno con garanzia del negozio di 1 anno. Pagamento alla "
                      "consegna in tutta l'Albania."),
    },
    "sq": {
        "lead": ("Çdo orë në këtë faqe është gjendje në dyqanin tonë në Rrugën Aleksander Goga në "
                 "Durrës: orë nga {b} marka, nga €{lo} deri €{hi}, të gjitha të reja me "
                 "garanci 1-vjeçare. Provojini nga e hëna në të shtunë, 8:30 deri 20:30, ose "
                 "porositni në WhatsApp me pagesë në dorëzim në Tiranë, Shkodër, Vlorë, Elbasan, "
                 "Korçë dhe kudo tjetër në Shqipëri."),
        "faq_h": "Si të blini një orë nga ne",
        "faq": [
            ("A mund të porosis një orë online në Shqipëri?",
             "Po. Zgjidhni një orë në këtë faqe dhe na shkruani në WhatsApp në " + phone("sq")["text"] + ". "
             "Dërgojmë kudo në Shqipëri me pagesë në dorëzim, pra paguani kur ora të mbërrijë. "
             "Dërgesa është falas dhe zakonisht zgjat 3 deri në 7 ditë."),
            ("A dërgoni orë në Tiranë?",
             "Po, dhe në çdo qytet tjetër. Porositë nisen për në Tiranë, Shkodër, Vlorë, Elbasan, "
             "Korçë dhe pjesën tjetër të Shqipërisë me pagesë në dorëzim. Mund të rezervoni një "
             "orë në WhatsApp dhe ta tërhiqni në dyqan në Durrës."),
            ("Sa kushtojnë orët tuaja?",
             "Nga €{lo} deri €{hi}, afërsisht nga {lolek} deri {hilek} Lekë. Shumica e modeleve "
             "janë nën €100. Mbajmë {b} marka, përfshirë Navimarine, Daniel Klein, Hislon dhe "
             "Philippe Lauren, të gjitha të reja."),
            ("A mund ta provoj një orë para se ta blej?",
             "Sigurisht. Dyqani është në Rrugën Aleksander Goga në Durrës, i hapur nga e hëna në "
             "të shtunë nga 8:30 deri 20:30, pa caktim takimi. Çdo orë në këtë faqe ndodhet "
             "fizikisht në dyqan."),
            ("A riparoni edhe orë?",
             "Po, e njëjta punishte riparon orë: ndërrim baterie në më pak se 2 minuta ndërsa "
             "prisni, rripa, xhama dhe servisime të plota, nga e hëna në të shtunë nga 8:30 "
             "deri 20:30."),
            ("Çfarë garancie kanë orët?",
             "Çdo orë që shesim ka garancinë tonë 1-vjeçare, dhe keni 30 ditë për ta kthyer në "
             "dyqan nëse nuk ju përshtatet. Orët janë të reja dhe të papërdorura."),
        ],
        "desc": ("Orë të reja nga €{lo}, shumica nën €100, me garanci 1 vit. Porosit në WhatsApp "
                 "me pagesë në dorëzim në Tiranë dhe në gjithë Shqipërinë, ose provoji në Durrës."),
        "biz_desc": ("Dyqan orësh dhe punishte riparimi familjare në Durrës, Shqipëri, që nga "
                     "2009. Orë të reja nga {b} marka në shitje, riparime eksperte dhe kopjim "
                     "çelësash."),
        "coll_desc": ("Orë të reja nga {b} marka te Iglisi Watch në Durrës, Shqipëri, nga "
                      "€{lo} deri €{hi}, secila me garanci dyqani 1-vjeçare. Pagesë në dorëzim "
                      "në gjithë Shqipërinë."),
    },
}


from catalog_stats import lek as _lek, nfmt


# [DB-015.a] fill — token substitution scoped to the watch list it is handed
# DOES:   {b}/{lo}/{hi}/{lolek}/{hilek} from the given watches, so the same
#         strings work for the full catalog or any subset.
# NOTES:  {n} IS GONE AND MUST NOT COME BACK. It published how many watches are
#         listed, and the shop holds considerably more stock than it publishes,
#         so the number understated the shelf every time it rendered. The owner
#         raised it more than once. Raising here rather than silently ignoring
#         it, so a {n} left in COPY fails the build instead of shipping.
#         {b} stays: the brand count is accurate. Prices stay: they are true.
def fill(text, watches, lang="en"):
    assert "{n}" not in text, (
        "shop_seo.fill: {n} is retired. No page states how many watches; the "
        "shop stocks more than it lists. Use {b} or a price token.")
    # P128: the price tokens must reflect what a buyer can actually BUY. They
    # land in the visible lead, the meta description and the structured data of
    # the shop hub, and they were taken over a sold-inclusive list — so the
    # moment anything sold the page could quote a band whose cheapest watch was
    # gone. catalog_stats.load() has excluded sold since P- for the same reason.
    live = [w for w in watches if not w.get("sold") and not w.get("deleted")] or list(watches)
    watches = live
    prices = [w["price"] for w in watches if w.get("price")]
    brands = {w["brand"] for w in watches}
    return (text.replace("{b}", str(len(brands)))
                .replace("{lo}", str(min(prices)))
                .replace("{hi}", str(max(prices)))
                .replace("{lolek}", nfmt(_lek(min(prices)), lang))
                .replace("{hilek}", nfmt(_lek(max(prices)), lang)))


def seo_section_html(lang, watches):
    """[DB-015.b] The visible below-grid section. Marker id shop-seo makes replacement idempotent."""
    t = COPY[lang]
    faqs = "".join(
        '<details class="faq-item"><summary class="faq-question">'
        f'<span class="faq-q-label">{fill(q, watches, lang)}</span>'
        '<i class="fas fa-chevron-down" aria-hidden="true"></i></summary>'
        f'<div class="faq-answer"><p>{fill(a, watches, lang)}</p></div></details>'
        for q, a in t["faq"])
    return (
        '<section id="shop-seo" style="background:var(--bg-soft,#faf7f2);'
        'border-top:1px solid var(--border-light,#eaeaea);padding:3rem 1.5rem 3.5rem">'
        '<div style="max-width:50rem;margin:0 auto">'
        f'<p style="color:var(--text-secondary,#4a4a4a);line-height:1.65">{fill(t["lead"], watches, lang)}</p>'
        f'<h2 style="font-size:1.5rem;margin:2rem 0 .75rem">{t["faq_h"]}</h2>'
        f'<div class="space-y-2">{faqs}</div>'
        "</div></section>"
    )


# [DB-015.c] faq_jsonld — FAQPage built from the SAME strings as the visible FAQ
# NOTES:  gen_shop_index.py's sanity block verifies the two never diverge.
def faq_jsonld(lang, watches):
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": fill(q, watches, lang),
             "acceptedAnswer": {"@type": "Answer", "text": fill(a, watches, lang)}}
            for q, a in COPY[lang]["faq"]
        ],
    }
