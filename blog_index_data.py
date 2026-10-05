"""[DB-022] blog_index_data.py — the blog's one category authority, data only.
DOES:   holds ARTICLES: one dict per trilingual article family, NEWEST FIRST
        (list position breaks the tie when two families share a date). cat=
        assigns one of the five categories buying/gifts/care/knowledge/keys and
        is the ONLY place a category is decided, so chips, section headings and
        the CollectionPage JSON-LD can no longer drift apart (see [DB-009]).
        card= is optional: leave it off and the card is derived from the
        article's own BlogPosting headline + meta description. icon= must name a
        PROVEN_GLYPHS member.
IN:     nothing. No imports, no I/O, no functions.
OUT:    ARTICLES, read by gen_blog_index.py and scripts/verify-blog-index.py.
NOTES:  No sub-indices below because there is not one def or branch in the file,
        only the literal; a per-entry tag would go stale on the next article.
        The card copy here is what verify-blog-index.py check 9 diffs against git
        HEAD, template by template rather than rendered HTML: rendered cards
        carry price tokens, so comparing HTML made the check fire on every
        repricing. An intentional copy edit therefore reads red until it is
        committed, which is the check working, not failing.
        NO CARD MAY STATE HOW MANY WATCHES. The shop holds considerably more
        stock than it publishes, so a published count understates it; the owner
        has said so more than once. Counting tokens are gone from the vocabulary
        and gen_stats.render refuses them, so this is enforced rather than
        remembered. Prices stay: they are true and they sell.
        `gen_blog_index.py --seed` rebuilds this manifest from the rendered
        indexes, but it asserts the file does not already exist, and it re-emits
        the docstring below VERBATIM from its own source: a re-seed needs this
        file deleted first AND drops this header. Put the header back.
        A glyph outside PROVEN_GLYPHS renders as NOTHING (Font Awesome is
        subsetted in shared.css) and no text-based check can see it.

Taxonomy and hand-tuned card copy for gen_blog_index.py.

One entry per trilingual article family, newest first (list order is the
tie-break for equal dates). cat is the single category authority; the EN
value won every seed conflict, per the owner. card= holds the hand-tuned
index copy verbatim, entities included; omit card= on future entries to
derive from the article headline + meta description. label= overrides the
category card label where the old index carried nuance ("Watch History",
"Brand Comparison"); icon= must be a PROVEN_GLYPHS member.
"""

ARTICLES = [
    dict(
        slug='are-navimarine-watches-good', cat='buying',
        card=dict(
            en=dict(title='Are Navimarine Watches Good? An Honest Answer From the Bench',
                    desc='A watchmaker who sells them and also repairs them answers straight: what Navimarine is and is not, what the money actually buys, and the claims we refuse to make about it.'),
            it=dict(title='Orologi Navimarine: il Parere Onesto di un Orologiaio',
                    desc='Un orologiaio che li vende e li ripara risponde chiaro: cosa &egrave; e cosa non &egrave; Navimarine, cosa comprano davvero i soldi, e le affermazioni che ci rifiutiamo di fare.'),
            sq=dict(title='A Jan&euml; t&euml; Mira Or&euml;t Navimarine? P&euml;rgjigjja e Ndershme',
                    desc='Nj&euml; or&euml;ndreq&euml;s q&euml; i shet dhe i riparon p&euml;rgjigjet drejt: &ccedil;far&euml; &euml;sht&euml; dhe &ccedil;far&euml; nuk &euml;sht&euml; Navimarine, &ccedil;far&euml; blejn&euml; v&euml;rtet parat&euml;, dhe pretendimet q&euml; nuk i b&euml;jm&euml;.'),
        ),
    ),
    dict(
        slug='gold-watches-albania', cat='buying', icon='fa-gem',
        label=dict(en='Buying Guide', it="Guida all'Acquisto", sq='Udh&euml;zues Blerje'),
        card=dict(
            en=dict(title='Gold-Tone Watches in Albania: Every One We Stock, and What the Gold Actually Is',
                    desc='Gold-plated, never solid gold, and we say so first. Full gold-tone, two-tone and rose gold from &euro;58 to &euro;199, which dials suit which, which carry a sapphire crystal, and how to keep the plating looking new.'),
            it=dict(title='Orologi Color Oro in Albania: Tutti Quelli che Teniamo e Che Cosa Sia Quell&rsquo;Oro',
                    desc='Placcati oro, mai oro massiccio, e lo diciamo per primo. Color oro pieno, bicolore e oro rosa da &euro;58 a &euro;199, quali quadranti stanno con cosa, quali hanno vetro zaffiro e come mantenere la placcatura.'),
            sq=dict(title='Or&euml; Ngjyr&euml; Ari n&euml; Shqip&euml;ri: T&euml; Gjitha Ato q&euml; Mbajm&euml; dhe &Ccedil;far&euml; &Euml;sht&euml; Ai Ar',
                    desc='T&euml; praruara me ar, kurr&euml; ar masiv, dhe e themi q&euml; n&euml; fillim. Ngjyr&euml; ari e plot&euml;, dy-ngjyr&euml;sh dhe ar roz&euml; nga &euro;58 n&euml; &euro;199, cil&euml;t ciferblat&euml; shkojn&euml; me &ccedil;far&euml;, cilat kan&euml; xham safiri dhe si ta mbani prarimin.'),
        ),
    ),
    dict(
        slug='christmas-watch-gifts-albania', cat='gifts', icon='fa-gift',
        label=dict(en='Gift Guide', it='Guida Regali', sq='Udhëzues Dhuratash'),
        card=dict(
            en=dict(title='Christmas Watch Gifts in Albania: What to Buy and When to Order',
                    desc='What each budget actually buys, from a steel watch under &euro;60 to the cheapest sapphire we stock, plus the last sensible day to order so it is boxed before the 25th.'),
            it=dict(title='Regalo Orologio per Natale in Albania: Cosa Comprare e Quando Ordinare',
                    desc='Cosa compra davvero ogni budget, da un acciaio sotto i &euro;60 al vetro zaffiro pi&ugrave; economico che teniamo, e l&rsquo;ultimo giorno sensato per ordinare e averlo prima del 25.'),
            sq=dict(title='Dhurata Or&euml; p&euml;r Krishtlindje n&euml; Shqip&euml;ri: &Ccedil;&rsquo;t&euml; Blesh dhe Kur t&euml; Porosis',
                    desc='&Ccedil;far&euml; blen v&euml;rtet secili buxhet, nga nj&euml; or&euml; &ccedil;eliku nën &euro;60 te xhami safir m&euml; i lir&euml; q&euml; mbajm&euml;, dhe dita e fundit e arsyeshme p&euml;r porosi.'),
        ),
    ),
    dict(
        slug='watch-birthday-gift-albania', cat='gifts',
        card=dict(
            en=dict(title='A Watch as a Birthday Gift in Albania',
                    desc='What to spend, which style suits the person, and the three things we do to a watch before you give it. From €{lo} to €{hi}, cash on delivery anywhere in Albania.'),
            it=dict(title='Un Orologio come Regalo di Compleanno in Albania',
                    desc='Quanto spendere, quale stile scegliere e le tre cose che facciamo a un orologio prima che tu lo regali. Da €{lo} a €{hi}, pagamento alla consegna ovunque.'),
            sq=dict(title='Një Orë si Dhuratë për Ditëlindje në Shqipëri',
                    desc='Sa të shpenzoni, cili stil i shkon personit dhe tri gjërat që i bëjmë një ore para se ta dhuroni. Nga €{lo} deri €{hi}, me pagesë në dorëzim kudo.'),
        ),
    ),
    dict(
        slug='watch-for-working-hands', cat='buying',
        card=dict(
            en=dict(title='A Watch for Someone Who Works With Their Hands',
                    desc='Nothing on our counter is a shock-rated tool watch and we will not pretend otherwise. What we do have is a digital with no crown to catch, a resin case and 100 m water resistance.'),
            it=dict(title='Un Orologio per Chi Lavora con le Mani',
                    desc='Sul nostro banco non c&rsquo;è nessun orologio con certificazione antiurto e non facciamo finta del contrario. Quello che abbiamo è un digitale senza corona che sporge, cassa in resina e 100 m.'),
            sq=dict(title='Një Orë për Dikë që Punon me Duar',
                    desc='Asnjë orë në banakun tonë nuk ka certifikim kundër goditjeve dhe nuk bëjmë sikur ka. Ajo që kemi është një dixhitale pa kurorë që del jashtë, kasë rezine dhe 100 m rezistencë ndaj ujit.'),
        ),
    ),
    dict(
        slug='first-job-watch', cat='buying',
        card=dict(
            en=dict(title='A Watch for Your First Job: Buying One With Your Own Money',
                    desc='The first watch nobody gives you. What a first salary can sensibly spend, and what ten years of owning a steel quartz watch really costs once you count the battery.'),
            it=dict(title='Un Orologio per il Primo Lavoro: Comprarlo con i Tuoi Soldi',
                    desc='Il primo orologio che nessuno ti regala. Quanto può spendere con criterio un primo stipendio, e quanto costa davvero tenere dieci anni un orologio in acciaio al quarzo.'),
            sq=dict(title='Një Orë për Punën e Parë: Ta Blini me Paratë Tuaja',
                    desc='Ora e parë që nuk ua fal njeri. Sa mund të shpenzojë me arsye një rrogë e parë, dhe sa kushton vërtet mbajtja e një ore çeliku me kuarc për dhjetë vjet, bateria brenda.'),
        ),
    ),
    dict(
        slug='buy-watch-tirana', cat='buying',
        card=dict(
            en=dict(title='Buying a Watch in Tirana: What Your Options Are',
                    desc='What Tirana sells at each end of the market, and the two ways to buy from a Durr&euml;s watchmaker instead: 40 minutes on the highway, or free courier in 3 to 7 days with cash on delivery.'),
            it=dict(title='Comprare un Orologio a Tirana: Quali Sono le Opzioni',
                    desc='Cosa vende Tirana ai due estremi del mercato, e i due modi per comprare invece da un orologiaio di Durazzo: 40 minuti di autostrada, oppure corriere gratuito dai 3 ai 7 giorni.'),
            sq=dict(title='Blerja e një Ore në Tiranë: Cilat Janë Opsionet',
                    desc='Çfarë shet Tirana në të dy skajet e tregut, dhe dy mënyrat për të blerë te një orëtar në Durrës: 40 minuta autostradë, ose korrier falas brenda 3 deri në 7 ditësh.'),
        ),
    ),
    dict(
        slug='quartz-watch-accuracy', cat='knowledge',
        label=dict(en='Watch Knowledge', it='Conoscenza Orologi', sq='Njohuri Orësh'),
        card=dict(
            en=dict(title='Why a New Quartz Watch Still Gains or Loses a Few Seconds',
                    desc='The crystal is quoted in seconds per year, the watch behaves in seconds per month, and fifteen seconds a day is a fault. All three are true. What separates normal drift from a movement that needs attention.'),
            it=dict(title='Perché un Orologio al Quarzo Nuovo Guadagna o Perde Qualche Secondo',
                    desc='Il cristallo si dichiara in secondi all&rsquo;anno, l&rsquo;orologio si comporta in secondi al mese, e quindici secondi al giorno sono un guasto. Tutti e tre i dati sono veri. Cosa separa lo scarto normale da un movimento da controllare.'),
            sq=dict(title='Pse një Orë Kuarci e Re Fiton apo Humb disa Sekonda',
                    desc='Kristali jepet në sekonda në vit, ora sillet në sekonda në muaj, dhe pesëmbëdhjetë sekonda në ditë janë defekt. Të tria janë të vërteta. Ja çfarë e ndan humbjen normale nga një mekanizëm që kërkon vëmendje.'),
        ),
    ),
    dict(
        slug='bigotti-watches-albania', cat='buying',
        card=dict(
            en=dict(title='Bigotti Watches in Albania: Which One to Buy',
                    desc='Gold and black, a crystal-set square in steel or gold tone, and a steel multifunction with day and date. What each Bigotti on our counter actually is, and which one to buy.'),
            it=dict(title='Orologi Bigotti in Albania: Quale Comprare',
                    desc='Oro e nero, un quadrato con cristalli in acciaio o color oro, e un multifunzione in acciaio con giorno e data. Cos&rsquo;è davvero ogni Bigotti sul nostro banco, e quale comprare.'),
            sq=dict(title='Orë Bigotti në Shqipëri: Cilën të Blesh',
                    desc='Ar dhe e zezë, një katror me kristale në çelik ose ngjyrë ari, dhe një multifunksionale çeliku me ditë e datë. Çfarë është vërtet secila Bigotti në banakun tonë, dhe cilën të blesh.'),
        ),
    ),
    dict(
        slug='daniel-klein-vs-philippe-lauren', cat='buying',
        label=dict(en='Brand Comparison', it='Confronto Marche', sq='Krahasim Markash'),
        card=dict(
            en=dict(title='Daniel Klein or Philippe Lauren: Which One to Buy',
                    desc='Both are fashion watches on the same counter. Philippe Lauren is where the chronographs sit and where the money starts. Daniel Klein is dressier and reaches higher.'),
            it=dict(title='Daniel Klein o Philippe Lauren: Quale Comprare',
                    desc='Due marchi fashion sullo stesso banco. Philippe Lauren è dove stanno i cronografi e dove comincia la spesa. Daniel Klein è più elegante e arriva più in alto.'),
            sq=dict(title='Daniel Klein apo Philippe Lauren: Cilën të Blesh',
                    desc='Dy marka fashion në të njëjtin banak. Philippe Lauren është aty ku rrinë kronografët dhe ku nisin paratë. Daniel Klein është më elegante dhe shkon më lart.'),
        ),
    ),
    dict(
        slug='blue-dial-watches-albania', cat='buying',
        card=dict(
            en=dict(title='Blue Dial Watches in Albania: Which Blue to Buy',
                    desc='Ice blue, navy, and deep blue sunburst that turns almost black indoors. What each blue dial looks like in daylight, what it costs, and which one to buy.'),
            it=dict(title='Orologi con Quadrante Blu in Albania: Quale Blu Comprare',
                    desc='Azzurro ghiaccio, blu notte e il blu intenso sunburst che al chiuso diventa quasi nero. Com&rsquo;è alla luce del giorno ogni quadrante blu, quanto costa e quale comprare.'),
            sq=dict(title='Orë me Ciferblat Blu në Shqipëri: Cilin Blu të Blesh',
                    desc='Blu akulli, blu i errët dhe blu i thellë sunburst që brenda bëhet thuajse i zi. Si duket në dritë dite secili ciferblat blu, sa kushton dhe cilin të blesh.'),
        ),
    ),
    dict(
        slug='cash-on-delivery-watches-albania', cat='buying',
        card=dict(
            en=dict(title='Cash on Delivery in Albania: How Buying a Watch Works',
                    desc='You pay the courier at the door, with the box open and the watch in your hands. Free delivery anywhere in Albania, 3 to 7 days, and refusing it costs you nothing.'),
            it=dict(title='Pagamento alla Consegna in Albania: Come Funziona',
                    desc='Pagate il corriere alla porta, con la scatola aperta e l’orologio nelle vostre mani. Consegna gratuita in tutta l’Albania, dai 3 ai 7 giorni, e potete rifiutarlo senza pagare nulla.'),
            sq=dict(title='Pagesa në Dorëzim për Orët në Shqipëri: Si Funksionon',
                    desc='E paguani korrierin te dera, me kutinë e hapur dhe orën në duart tuaja. Dërgesë falas kudo në Shqipëri, 3 deri në 7 ditë, dhe mund ta refuzoni pa ju kushtuar asgjë.'),
        ),
    ),
    dict(
        slug='watch-returns-exchange-guarantee', cat='buying',
        card=dict(
            en=dict(title='Returns, Exchanges and the 1-Year Guarantee',
                    desc='Refuse it at the door and pay nothing. Thirty days to bring it back to Durrës for an exchange or a refund. A 1-year guarantee on every watch, and what it does not cover.'),
            it=dict(title='Resi, Cambi e la Garanzia di 1 Anno',
                    desc='Rifiutatelo alla porta e non pagate nulla. Trenta giorni per riportarlo a Durazzo per un cambio o un rimborso. Garanzia di 1 anno su ogni orologio, e cosa non copre.'),
            sq=dict(title='Kthimet, Ndërrimet dhe Garancia 1-Vjeçare',
                    desc='Refuzojeni te dera dhe nuk paguani asgjë. Tridhjetë ditë për ta sjellë në Durrës për ndërrim ose rimbursim. Garanci 1-vjeçare për çdo orë, dhe çfarë nuk mbulon.'),
        ),
    ),
    dict(
        slug='why-buy-from-a-watchmaker', cat='buying',
        card=dict(
            en=dict(title='Why Buy Your Watch from a Watchmaker',
                    desc='The same hands that repair a watch in Durrës choose and inspect every watch we list. What that changes about what gets claimed, and who honours the guarantee.'),
            it=dict(title='Perché Comprare l’Orologio da un Orologiaio',
                    desc='Le stesse mani che riparano un orologio a Durazzo scelgono e controllano ogni orologio che mettiamo in vendita. Cosa cambia in quello che si dichiara e in chi onora la garanzia.'),
            sq=dict(title='Pse ta Blesh Orën te Orëndreqësi',
                    desc='Të njëjtat duar që riparojnë një orë në Durrës zgjedhin dhe inspektojnë çdo orë që listojmë. Çfarë ndryshon te ajo që pretendohet dhe te ai që e nderon garancinë.'),
        ),
    ),
    dict(
        slug='philippe-lauren-watches-albania', cat='buying',
        label=dict(en='Buying Guide', it='Guida all’Acquisto', sq='Guidë Blerjeje'),
        card=dict(
            en=dict(title='Philippe Lauren Watches in Albania: Which One to Buy',
                    desc='From {lolek:philippe-lauren} L to {hilek:philippe-lauren} L: real chronographs, plain steel dress watches, steel sport and gold-tone dress. Which one to buy, and why.'),
            it=dict(title='Orologi Philippe Lauren in Albania: Quale Comprare',
                    desc='Da {lolek:philippe-lauren} L a {hilek:philippe-lauren} L: cronografi veri, essenziali da abito in acciaio, sportivi e da abito color oro. Quale comprare, e perché.'),
            sq=dict(title='Orë Philippe Lauren në Shqipëri: Cilën të Blesh',
                    desc='Nga {lolek:philippe-lauren} L deri {hilek:philippe-lauren} L: kronografë të vërtetë, veshjeje çeliku të thjeshta, sportive dhe veshjeje ngjyrë ari. Cilën të blesh, dhe pse.'),
        ),
    ),
    dict(
        slug='chronograph-vs-three-hand-watch', cat='buying',
        card=dict(
            en=dict(title='Chronograph or Three Hands? What Those Subdials Actually Do',
                    desc='Some of our watches time something and the rest only look like they do. How to tell in five seconds, what the pushers cost in battery life, and which one to buy.'),
            it=dict(title='Cronografo o Tre Sfere? Cosa Fanno Davvero Quei Contatori',
                    desc='Alcuni dei nostri orologi cronometrano davvero, gli altri sembrano solo farlo. Come capirlo in cinque secondi, quanto costano in batteria e quale comprare.'),
            sq=dict(title='Kronograf apo Tre Akrepa? &Ccedil;far&euml; B&euml;jn&euml; V&euml;rtet N&euml;n-ciferblat&euml;t',
                    desc='Disa nga or&euml;t tona e matin koh&euml;n, t&euml; tjerat vet&euml;m duken sikur e b&euml;jn&euml;. Si dallohen p&euml;r pes&euml; sekonda, sa kushtojn&euml; n&euml; bateri dhe cil&euml;n t&euml; blesh.'),
        ),
    ),
    dict(
        slug='gold-or-steel-watch', cat='knowledge',
        label=dict(en='Watch Knowledge', it='Cultura Orologio', sq='Njohuri Orësh'),
        card=dict(
            en=dict(title='Gold or Steel? What Plated Gold Really Means at This Price',
                    desc='No watch at this price is solid gold. How long plating lasts, why it cannot be repaired, the rules that extend it, and when steel is simply the better buy.'),
            it=dict(title='Oro o Acciaio? Cosa Significa Davvero la Placcatura a Questo Prezzo',
                    desc="Nessun orologio a questo prezzo è in oro massiccio. Quanto dura la placcatura, perché non si ripara, le regole che la fanno durare e quando conviene l'acciaio."),
            sq=dict(title='Ar apo &Ccedil;elik? &Ccedil;far&euml; Do t&euml; Thot&euml; V&euml;rtet Veshja me Ar n&euml; K&euml;t&euml; &Ccedil;mim',
                    desc='Asnj&euml; or&euml; n&euml; k&euml;t&euml; &ccedil;mim nuk &euml;sht&euml; prej ari masiv. Sa zgjat veshja, pse nuk riparohet, rregullat q&euml; e zgjasin dhe kur &ccedil;eliku &euml;sht&euml; m&euml; i mir&euml;.'),
        ),
    ),
    dict(
        slug='how-long-does-a-cheap-watch-last', cat='knowledge',
        label=dict(en='Watch Knowledge', it='Cultura Orologio', sq='Njohuri Orësh'),
        card=dict(
            en=dict(title='How Long Does a 70 Euro Watch Last? What We See on the Bench',
                    desc='Five to ten years, and the movement is almost never what fails. The real failure order, the seasonal damage we see every year, and what a decade of ownership actually costs.'),
            it=dict(title='Quanto Dura un Orologio da 70 Euro? Quello Che Vediamo al Banco',
                    desc='Da cinque a dieci anni, e il movimento non è quasi mai ciò che cede. Il vero ordine dei guasti, i danni stagionali e quanto costa davvero un decennio di possesso.'),
            sq=dict(title='Sa Zgjat nj&euml; Or&euml; 70 Euro? &Ccedil;far&euml; Shohim n&euml; Banak',
                    desc='Nga pes&euml; n&euml; dhjet&euml; vjet, dhe mekanizmi nuk &euml;sht&euml; thuajse kurr&euml; ai q&euml; dor&euml;zohet. Radha e v&euml;rtet&euml; e prishjeve dhe sa kushton vërtet nj&euml; dekad&euml; pron&euml;sie.'),
        ),
    ),
    dict(
        slug='what-makes-a-watch-look-expensive', cat='knowledge',
        label=dict(en='Watch Knowledge', it='Cultura Orologio', sq='Njohuri Orësh'),
        card=dict(
            en=dict(title='What Makes a Watch Look Expensive: Six Details That Do the Work',
                    desc='Fluted bezels, jubilee bracelets, sunburst dials. Six design details that read as costly, where each one came from, and what they cost in Durres from {lolek} Lek.'),
            it=dict(title='Cosa Rende un Orologio Elegante: Sei Dettagli Che Fanno il Lavoro',
                    desc='Lunette zigrinate, bracciali jubilee, quadranti sunburst. Sei dettagli che sembrano costosi, da dove viene ciascuno e quanto costano a Durazzo, da {lolek} lek.'),
            sq=dict(title='&Ccedil;far&euml; e B&euml;n nj&euml; Or&euml; t&euml; Duket e Shtrenjt&euml;: Gjasht&euml; Detaje Q&euml; B&euml;jn&euml; Pun&euml;n',
                    desc='Luneta t&euml; val&euml;zuara, bracelete jubilee, ciferblate sunburst. Gjasht&euml; detaje q&euml; duken t&euml; shtrenjta, nga vjen secili dhe sa kushtojn&euml; n&euml; Durr&euml;s, nga {lolek} lek&euml;.'),
        ),
    ),
    dict(
        slug='new-year-watch-gifts-albania', cat='gifts',
        label=dict(en='Gift Guide', it='Guida Regali', sq='Udhëzues Dhuratash'),
        card=dict(
            en=dict(title='New Year Watch Gifts in Albania: What to Buy and When to Order',
                    desc='What each budget actually buys, from a steel watch they can wear every day to a dress piece that feels like a real gift, and the last day you can order and still have it arrive. Cash on delivery anywhere in Albania, or walk into Durres until 20:30.'),
            it=dict(title='Regalo Orologio per Capodanno in Albania: Cosa Comprare e Quando Ordinare',
                    desc="Cosa compra davvero ogni budget, da un acciaio da portare tutti i giorni a un orologio da abito che sembra un vero regalo, e l'ultimo giorno utile per ordinare e riceverlo in tempo. Pagamento alla consegna in tutta l'Albania, o venite a Durazzo fino alle 20:30."),
            sq=dict(title='Dhurata Ore p&euml;r Vitin e Ri n&euml; Shqip&euml;ri: &Ccedil;far&euml; t&euml; Blesh dhe Kur t&euml; Porosis&euml;sh',
                    desc='&Ccedil;far&euml; blen v&euml;rtet secili buxhet, nga nj&euml; or&euml; &ccedil;eliku p&euml;r &ccedil;do dit&euml; te nj&euml; or&euml; veshjeje q&euml; duket dhurat&euml; e v&euml;rtet&euml;, dhe dita e fundit q&euml; mund t&euml; porosisni e t&euml; mb&euml;rrij&euml; n&euml; koh&euml;. Pages&euml; n&euml; dor&euml;zim kudo n&euml; Shqip&euml;ri, ose ejani n&euml; Durr&euml;s deri n&euml; 20:30.'),
        ),
    ),
    dict(
        slug='womens-watches-albania', cat='buying',
        label=dict(en='Buying Guide', it='Guida all’Acquisto', sq='Guidë Blerjeje'),
        card=dict(
            en=dict(title="Women's Watches in Albania: What We Stock and What It Costs",
                    desc='Gold-tone dress watches, slim steel and mother-of-pearl Hislon Queens from 59 to 189 euro, in stock in Durres with cash on delivery anywhere in Albania.'),
            it=dict(title='Orologi da Donna in Albania: Cosa Teniamo e Quanto Costa',
                    desc='Orologi da abito color oro, acciaio sottile e Hislon Queen in madreperla da 59 a 189 euro, disponibili a Durazzo con pagamento alla consegna ovunque.'),
            sq=dict(title='Orë për Femra në Shqipëri: Çfarë Mbajmë dhe Sa Kushton',
                    desc='Orë veshjeje ngjyrë ari, çelik i hollë dhe Hislon Queen me sedef nga 59 deri 189 euro, gjendje në Durrës me pagesë në dorëzim kudo në Shqipëri.'),
        ),
    ),
    dict(
        slug='watches-under-10000-lek', cat='buying', featured=True,
        label=dict(en='Buying Guide', it='Guida all’Acquisto', sq='Guidë Blerjeje'),
        card=dict(
            en=dict(title='Watches Under 10,000 Lek: What Your Money Actually Buys',
                    desc='Most of the watches we list cost under 10,000 Leke, starting at {lolek} L. The counter priced in Lek, band by band, with cash on delivery anywhere in Albania.'),
            it=dict(title='Orologi Sotto i 10.000 Lek: Cosa Compra Davvero il Vostro Denaro',
                    desc='Gran parte degli orologi che proponiamo costa meno di 10.000 Leke, da {lolek} L. Il banco prezzato in Lek, fascia per fascia, con pagamento alla consegna ovunque.'),
            sq=dict(title='Orë Nën 10.000 Lekë: Çfarë Blejnë Vërtet Paratë Tuaja',
                    desc='Pjesa më e madhe e orëve që listojmë kushton nën 10.000 Lekë, duke filluar nga {lolek} L. Banaku me çmime në lekë, fashë pas fashe, me pagesë në dorëzim kudo.'),
        ),
    ),
    dict(
        slug='mens-watches-albania', cat='buying',
        label=dict(en='Buying Guide', it='Guida all’Acquisto', sq='Guidë Blerjeje'),
        card=dict(
            en=dict(title="Men's Watches in Albania: What We Stock and What It Costs",
                    desc='Sport steel, chronographs and dress watches from €{lo} to €{hi}, all in stock in Durrës. What each style is for and how to order anywhere in Albania.'),
            it=dict(title='Orologi da Uomo in Albania: Cosa Teniamo e Quanto Costa',
                    desc='Sportivi in acciaio, cronografi e orologi da abito da €{lo} a €{hi}, tutti disponibili a Durazzo. A cosa serve ogni stile e come ordinare ovunque.'),
            sq=dict(title='Orë për Burra në Shqipëri: Çfarë Mbajmë dhe Sa Kushton',
                    desc='Sportive çeliku, kronografë dhe orë veshjeje nga €{lo} deri €{hi}, të gjitha gjendje në Durrës. Për çfarë shërben çdo stil dhe si të porosisni kudo.'),
        ),
    ),
    dict(
        slug='watches-i-would-buy-myself', cat='buying',
        card=dict(
            en=dict(title='The 5 Watches I Would Buy From My Own Shop',
                    desc="A watchmaker's honest personal picks: the five watches I would spend my own money on. Two Navimarines, a gold-tone Daniel Klein, a Hislon chronograph and a Hislon Classic, and why each one is on the list."),
            it=dict(title='I 5 Orologi che Comprerei dal Mio Stesso Negozio',
                    desc='Le scelte personali oneste di un orologiaio: i cinque orologi su cui spenderei i miei soldi. Due Navimarine, un Daniel Klein color oro, un cronografo Hislon e un Hislon Classic, e perch&eacute; ognuno &egrave; in lista.'),
            sq=dict(title='5 Or&euml;t q&euml; Do t&euml; Blija Vet&euml; nga Dyqani Im',
                    desc='Zgjedhjet personale t&euml; ndershme t&euml; nj&euml; or&euml;ndreq&euml;si: pes&euml; or&euml;t p&euml;r t&euml; cilat do t&euml; shpenzoja parat&euml; e mia. Dy Navimarine, nj&euml; Daniel Klein ngjyr&euml; ari, nj&euml; kronograf Hislon dhe nj&euml; Hislon Classic, dhe pse secila &euml;sht&euml; n&euml; list&euml;.'),
        ),
    ),
    dict(
        slug='watch-price-tiers-60-190', cat='buying',
        card=dict(
            en=dict(title='60 vs 90 vs 190 Euro: What More Money Actually Buys in a Watch',
                    desc='Daniel Klein, Navimarine, Hislon compared honestly. More money buys dress design and finishing, not a better crystal, movement or water resistance.'),
            it=dict(title='60 vs 90 vs 190 Euro: Cosa Compri Davvero con un Orologio Pi&ugrave; Caro',
                    desc='Daniel Klein, Navimarine, Hislon a confronto onesto. I soldi in pi&ugrave; comprano design da abito e finitura, non un vetro, un movimento o un&rsquo;impermeabilit&agrave; migliori.'),
            sq=dict(title='60 vs 90 vs 190 Euro: Çfar&euml; Blen V&euml;rtet me nj&euml; Or&euml; M&euml; t&euml; Shtrenjt&euml;',
                    desc='Daniel Klein, Navimarine, Hislon krahasuar ndershm&euml;risht. Parat&euml; shtes&euml; blejn&euml; dizajn elegant dhe p&euml;rfundim, jo xham, l&euml;vizje apo rezistenc&euml; ndaj ujit m&euml; t&euml; mir&euml;.'),
        ),
    ),
    dict(
        slug='are-daniel-klein-watches-good', cat='buying',
        card=dict(
            en=dict(title="Are Daniel Klein Watches Any Good? A Watchmaker's Honest Answer",
                    desc='Turkish fashion brand, quartz, gold-tone looks for {lo:daniel-klein} to {hi:daniel-klein}. Where the money is well spent and where it is not, plus the models we stock.'),
            it=dict(title='Gli Orologi Daniel Klein Sono Buoni? La Risposta Onesta di un Orologiaio',
                    desc='Marchio di moda turco, quarzo, look dorato per {lo:daniel-klein} a {hi:daniel-klein}. Dove i soldi sono ben spesi e dove no, con i modelli in stock.'),
            sq=dict(title='A Vlejn&euml; Or&euml;t Daniel Klein? P&euml;rgjigjja e Ndershme e nj&euml; Or&euml;ndreq&euml;si',
                    desc='Mark&euml; mode turke, kuarc, pamje ari p&euml;r {lo:daniel-klein} deri {hi:daniel-klein}. Ku shkojn&euml; mir&euml; parat&euml; dhe ku jo, me modelet q&euml; kemi n&euml; stok.'),
        ),
    ),
    dict(
        slug='summer-sea-watch-guide', cat='buying',
        card=dict(
            en=dict(title='Watches for the Albanian Summer: Beach, Sweat and Sea',
                    desc='What salt, sand and sunscreen do to a watch, which ratings actually allow swimming, and the 5 ATM steel model we recommend at &euro;75.'),
            it=dict(title='Che Orologio Portare al Mare: l&rsquo;Estate Albanese',
                    desc='Cosa fanno sale, sabbia e crema solare a un orologio, quali rating permettono davvero di nuotare, e l&rsquo;acciaio 5 ATM che consigliamo a &euro;75.'),
            sq=dict(title='Ora p&euml;r Plazh e Det: Vera Shqiptare',
                    desc='Çfar&euml; i b&euml;jn&euml; kripa, r&euml;ra dhe kremi i diellit nj&euml; ore, cilat vler&euml;sime lejojn&euml; vërtet notin, dhe çeliku 5 ATM q&euml; rekomandojm&euml; me &euro;75.'),
        ),
    ),
    dict(
        slug='g-shock-history', cat='knowledge',
        label=dict(en='Watch History', it='Storia dell’Orologeria', sq='Historia e Orëve'),
        card=dict(
            en=dict(title='The G-Shock Story: How a Broken Watch Built an Unbreakable One',
                    desc='One engineer, a broken gift and 200 failed prototypes. How Casio built the watch that would not die, and the Casio value you can buy from us today.'),
            it=dict(title='La Storia del G-Shock: Come un Orologio Rotto ne Cre&ograve; uno Indistruttibile',
                    desc='Un ingegnere, un regalo rotto e 200 prototipi falliti. Come Casio costru&igrave; l&rsquo;orologio che non muore, e il valore Casio che puoi comprare da noi oggi.'),
            sq=dict(title='Historia e G-Shock: Si nj&euml; Or&euml; e Thyer Krijoi nj&euml; t&euml; Pathyeshme',
                    desc='Nj&euml; inxhinier, nj&euml; dhurat&euml; e thyer dhe 200 prototipe t&euml; d&euml;shtuar. Si Casio nd&euml;rtoi or&euml;n q&euml; nuk vdes, dhe vlera Casio q&euml; mund ta blesh nga ne sot.'),
        ),
    ),
    dict(
        slug='casio-a159wa-legend', cat='knowledge',
        label=dict(en='Watch Knowledge', it='Cultura Orologiera', sq='Njohuri për Orët'),
        card=dict(
            en=dict(title='The Casio A159WA: a 40-Year Legend You Can Buy in Durr&euml;s',
                    desc='The digital watch that has not changed since the early 1980s: 7-year battery, steel bracelet, alarm and stopwatch. In stock at Iglisi Watch for &euro;61.'),
            it=dict(title='Casio A159WA: la Leggenda di 40 Anni in Vendita a Durr&euml;s',
                    desc='L&rsquo;orologio digitale immutato dai primi anni &rsquo;80: batteria da 7 anni, bracciale in acciaio, sveglia e cronometro. Da Iglisi Watch a &euro;61.'),
            sq=dict(title='Casio A159WA: Legjenda 40-Vje&ccedil;are q&euml; Blihet n&euml; Durr&euml;s',
                    desc='Ora dixhitale e pandryshuar q&euml; nga fillimi i viteve &rsquo;80: bateri 7-vje&ccedil;are, byzylyk &ccedil;eliku, alarm dhe kronomet&euml;r. Te Iglisi Watch p&euml;r &euro;61.'),
        ),
    ),
    dict(
        slug='watch-strap-lug-width-guide', cat='care',
        label=dict(en='Watch Care', it='Cura Orologio', sq='Kujdesi i Orës'),
        card=dict(
            en=dict(title='Watch Strap Lug Width: How to Measure and Find the Right Size',
                    desc='Buying a strap that doesn&rsquo;t fit is the most common strap-shopping mistake. Learn how to measure lug width, what sizes common watches use, and what to do when you&rsquo;re not sure.'),
            it=dict(title='Larghezza Anse Orologio: Come Misurare e Trovare il Cinturino Giusto',
                    desc='Acquistare un cinturino della misura sbagliata &egrave; l&rsquo;errore pi&ugrave; comune. Scoprite come misurare la larghezza delle anse, le misure dei modelli pi&ugrave; comuni e cosa fare in caso di dubbio.'),
            sq=dict(title='Gjer&euml;sia e Ansave t&euml; Or&euml;s: Si t&euml; Matni dhe t&euml; Gjeni Brezin e Duhur',
                    desc='Blerja e brezit me madh&euml;si t&euml; gabuar &euml;sht&euml; gabimi m&euml; i zakonsh&euml;m. M&euml;soni si t&euml; matni gjer&euml;sin&euml; e ansave, cilat madh&euml;si p&euml;rdorin modelet m&euml; t&euml; zakonshme dhe &ccedil;far&euml; t&euml; b&euml;ni n&euml; rast dyshimi.'),
        ),
    ),
    dict(
        slug='watch-crown-repair', cat='care',
        label=dict(en='Watch Repair', it='Riparazione Orologi', sq='Riparim Orash'),
        card=dict(
            en=dict(title='Watch Crown Repair: When to Fix and When to Replace',
                    desc='Crown fell off or spinning with no result? We explain the four most common crown problems, what repair involves, and what it costs in Durr&euml;s.'),
            it=dict(title='Riparazione della Corona dell&rsquo;Orologio: Quando Riparare e Quando Sostituire',
                    desc='La corona &egrave; caduta o gira senza risultato? Spieghiamo i quattro problemi pi&ugrave; comuni, cosa comporta la riparazione e quanto costa a Durr&euml;s.'),
            sq=dict(title='Riparimi i Kuror&euml;s s&euml; Or&euml;s: Kur t&euml; Riparohet dhe Kur t&euml; Z&euml;vend&euml;sohet',
                    desc='Kurora ra apo rrotullohet pa rezultat? Shpjegojm&euml; kat&euml;r problemet m&euml; t&euml; zakonshme, &ccedil;far&euml; p&euml;rfshin riparimi dhe sa kushton n&euml; Durr&euml;s.'),
        ),
    ),
    dict(
        slug='casio-service-albania', cat='care',
        card=dict(
            en=dict(title='Where to Service a Casio, Seiko or Citizen in Albania',
                    desc='Albania has no official service centres for Japanese watch brands. Here&rsquo;s where to go in Durr&euml;s, what these watches need, and what it costs.'),
            it=dict(title='Dove Portare un Casio, Seiko o Citizen in Albania',
                    desc='In Albania non esistono centri di assistenza autorizzati per i marchi giapponesi. Ecco dove andare a Durr&euml;s, cosa richiedono questi orologi e quanto costa.'),
            sq=dict(title='Ku t&euml; Servisoni nj&euml; Casio, Seiko ose Citizen n&euml; Shqip&euml;ri',
                    desc='Shqip&euml;ria nuk ka qendra t&euml; autorizuara sh&euml;rbimi p&euml;r markat japoneze t&euml; or&euml;ve. Ja ku t&euml; shkoni n&euml; Durr&euml;s, &ccedil;far&euml; kan&euml; nevoj&euml; k&euml;to or&euml; dhe sa kushton.'),
        ),
    ),
    dict(
        slug='watch-heat-humidity-damage', cat='care',
        card=dict(
            en=dict(title='Can Heat and Humidity Damage Your Watch?',
                    desc='Heat degrades lubricants, warps gaskets, and causes battery leakage. Humidity forces moisture past seals. Learn the danger zones, warning signs, and 5 ways to protect your watch.'),
            it=dict(title='Il Caldo e l&rsquo;Umidit&agrave; Possono Danneggiare il Tuo Orologio?',
                    desc='Il caldo degrada i lubrificanti, deforma le guarnizioni e causa perdite dalla batteria. L&rsquo;umidit&agrave; forza l&rsquo;umidità oltre le guarnizioni. Scopri le zone di pericolo, i segnali d&rsquo;allarme e 5 modi per proteggere il tuo orologio.'),
            sq=dict(title='A Mund t&euml; D&euml;mtohet Ora nga Nxeht&euml;sia dhe Lag&euml;shtia?',
                    desc='Nxehtësia dëmton lubrifikantët, deformon garniturat dhe shkakton rrjedhje bateri. Lagështia detyron ujin të kalojë garniturat. Mëso zonat e rrezikut, shenjat dhe 5 mënyra për ta mbrojtur orën.'),
        ),
    ),
    dict(
        slug='watch-pressure-test-explained', cat='care',
        card=dict(
            en=dict(title='Watch Pressure Testing Explained: What It Is and When You Need It',
                    desc='Your water resistance rating was accurate when new. A pressure test tells you if it still is. Learn what the test involves, when you need one, and why a battery change voids your seal.'),
            it=dict(title='Test di Pressione dell&rsquo;Orologio: Cos&rsquo;&Egrave; e Quando Serve',
                    desc='Il valore di resistenza all&rsquo;acqua era accurato quando era nuovo. Un test di pressione ti dice se lo è ancora. Scopri cosa verifica, quando farlo e perché la sostituzione della batteria annulla la guarnizione.'),
            sq=dict(title='Testi i Presionit t&euml; Or&euml;s: &Ccedil;far&euml; &Euml;sht&euml; dhe Kur Nevojitet',
                    desc='Vlerësimi i rezistencës ndaj ujit ishte i saktë kur ishte e re. Testi i presionit ju tregon nëse është ende. Mësoni çfarë teston, kur ta bëni dhe pse ndërrimi i baterisë anullon guarnizën.'),
        ),
    ),
    # CONFLICT seeded en=care it=repair -> using care
    dict(
        slug='watch-service-durres', cat='care',
        label=dict(en='Watch Care', it='Riparazione Orologi', sq='Kujdesi i Orës'),
        card=dict(
            en=dict(title='Complete Watch Service &amp; Overhaul in Durr&euml;s',
                    desc='Full quartz and mechanical watch service in Durr&euml;s - disassembly, ultrasonic cleaning, lubrication and regulation. Free quote and WhatsApp advice before you visit.'),
            it=dict(title='Revisione Completa dell&rsquo;Orologio a Durrës - Iglisi Watch',
                    desc='Revisione completa orologi al quarzo e meccanici a Durrës da Iglisi Watch. Smontaggio, pulizia ultrasonica, lubrificazione e regolazione. Preventivo gratuito, pronto in 1-5 giorni.'),
            sq=dict(title='Revizionim i Plot&euml; i Or&euml;s n&euml; Durr&euml;s',
                    desc='Revizionim i plot&euml; p&euml;r or&euml; me kuarc dhe mekanike n&euml; Durr&euml;s - &ccedil;montim, pastrim ultrasonik, lubrifikim dhe rregullim. Vler&euml;sim falas dhe k&euml;shill&euml; n&euml; WhatsApp para se t&euml; vish.'),
        ),
    ),
    dict(
        slug='buy-watches-albania', cat='buying',
        label=dict(en='Buying Guide', it='Guida all’Acquisto', sq='Blerje Orësh'),
        card=dict(
            en=dict(title='How to Buy New Watches in Albania',
                    desc='Daniel Klein from {lo:daniel-klein}, Navimarine from {lo:navimarine}, Hislon from {lo:hislon}, all with a 1-year guarantee. Buy in-store in Durr&euml;s or order on WhatsApp with delivery anywhere in Albania.'),
            it=dict(title='Come Comprare Orologi Nuovi in Albania',
                    desc='Daniel Klein da {lo:daniel-klein}, Navimarine da {lo:navimarine}, Hislon da {lo:hislon}, tutti con garanzia di 1 anno. Acquista in negozio a Durr&euml;s o ordina via WhatsApp con consegna in tutta l&rsquo;Albania.'),
            sq=dict(title='Si t&euml; Blesh Or&euml; t&euml; Reja n&euml; Shqip&euml;ri - Hislon dhe Navimarine',
                    desc='Udhëzues për blerjen e orëve të reja në Shqipëri. Daniel Klein nga {lo:daniel-klein}, Navimarine nga {lo:navimarine} dhe Hislon nga {lo:hislon} te Iglisi Watch Durrës, garanci 1-vjeçare dhe dërgim kudo nëpërmjet WhatsApp.'),
        ),
    ),
    dict(
        slug='seiko-vs-citizen-vs-casio', cat='buying',
        label=dict(en='Brand Comparison', it='Confronto Marchi', sq='Krahasim Markash'),
        card=dict(
            en=dict(title='Seiko vs Citizen vs Casio: Which Japanese Watch Is Worth Buying?',
                    desc='Three Japanese giants compared honestly - Seiko&rsquo;s automatic movements, Citizen&rsquo;s Eco-Drive and Casio&rsquo;s durability. Which one is right for you?'),
            it=dict(title='Seiko vs Citizen vs Casio: Quale Marchio Giapponese Vale la Pena Comprare?',
                    desc='Tre giganti giapponesi a confronto - i movimenti automatici Seiko, l&rsquo;Eco-Drive Citizen e la durata Casio. Qual &egrave; quello giusto per te?'),
            sq=dict(title='Seiko vs Citizen vs Casio: Cil&euml; Mark&euml; Japoneze Ia Vlen t&euml; Blesh?',
                    desc='Tre gjigant&euml; japonez&euml; t&euml; krahasuar nd&euml;rshmërisht - l&euml;vizjet automatike t&euml; Seiko, Eco-Drive t&euml; Citizen dhe qëndrueshmëria e Casio. Cili &euml;sht&euml; i duhuri p&euml;r ty?'),
        ),
    ),
    dict(
        slug='casio-vs-citizen', cat='buying',
        label=dict(en='Brand Comparison', it='Confronto Marchi', sq='Krahasim Markash'),
        card=dict(
            en=dict(title='Casio vs Citizen Watch: Which Is Worth Buying?',
                    desc='Two Japanese brands, two philosophies: Casio&rsquo;s rugged value against Citizen&rsquo;s Eco-Drive refinement. An honest head-to-head from the repair bench.'),
            it=dict(title='Casio vs Citizen: Quale Scegliere?',
                    desc='Due marchi giapponesi, due filosofie: il valore robusto di Casio contro la raffinatezza Eco-Drive di Citizen. Un confronto onesto dal banco di riparazione.'),
            sq=dict(title='Casio vs Citizen: Cil&euml;n Or&euml; t&euml; Blini?',
                    desc='Dy marka japoneze, dy filozofi: vlera e fort&euml; e Casio p&euml;rball&euml; rafinimit Eco-Drive t&euml; Citizen. Nj&euml; krahasim i nd&euml;rsh&euml;m nga banaku i riparimit.'),
        ),
    ),
    dict(
        slug='watch-battery-size-guide', cat='care',
        label=dict(en='Watch Care', it='Manutenzione Orologio', sq='Mirëmbajtja e Orës'),
        card=dict(
            en=dict(title='Watch Battery Size Guide: SR626SW, SR920SW, CR2032 Explained',
                    desc='How to read battery codes, which battery fits your watch, and when to replace it. Covers all common silver oxide and lithium sizes.'),
            it=dict(title='Guida Misure Batterie Orologi: SR626SW, SR920SW, CR2032 Spiegati',
                    desc='Come leggere i codici delle batterie, quale si adatta al tuo orologio e quando sostituirla. Copre tutte le misure comuni a ossido d&rsquo;argento e litio.'),
            sq=dict(title='Madhësitë e Baterive t&euml; Or&euml;ve: SR626SW, SR920SW, CR2032 t&euml; Shpjegun',
                    desc='Si t&euml; lexoni kodet e baterive, cila madhësi i p&euml;rshtatet or&euml;s tuaj dhe kur t&euml; ndërroni baterinë.'),
        ),
    ),
    dict(
        slug='watch-gift-durres-same-day', cat='gifts',
        card=dict(
            en=dict(title='Need a Watch Gift in Durr&euml;s Today? Open Until 20:30',
                    desc='Walk in, choose from Daniel Klein from {lo:daniel-klein}, Navimarine from {lo:navimarine} or Hislon from {lo:hislon}, leave with a gift-ready watch the same day. Open Monday to Saturday until 20:30. No appointment needed.'),
            it=dict(title='Hai Bisogno di un Orologio Come Regalo a Durazzo Oggi?',
                    desc='Iglisi Watch &egrave; aperto luned&igrave;-sabato fino alle 20:30. Entra, scegli dallo stock e parti con un orologio pronto da regalare. Daniel Klein da {lo:daniel-klein} e Navimarine da {lo:navimarine}.'),
            sq=dict(title='Keni Nevoj&euml; p&euml;r Dhurat&euml; Or&euml; n&euml; Durr&euml;s Sot?',
                    desc='Iglisi Watch &euml;sht&euml; hapur e h&euml;n&euml;-shtun&euml; deri n&euml; 20:30. Hyni, zgjidhni nga gjend&euml;ja dhe largohuni me or&euml; gati p&euml;r t&rsquo;u dh&euml;n&euml;. Daniel Klein nga {lo:daniel-klein} dhe Navimarine nga {lo:navimarine}.'),
        ),
    ),
    dict(
        slug='repair-or-buy-new-watch-durres', cat='care',
        card=dict(
            en=dict(title='Should I Repair My Watch or Buy a New One? An Honest Guide',
                    desc='An honest framework based on repair cost, watch type, age, and sentimental value. Free assessment at Iglisi Watch in Durr&euml;s, no obligation to proceed.'),
            it=dict(title='Devo Riparare il Mio Orologio o Comprarne Uno Nuovo?',
                    desc='Vale la pena ripararlo o &egrave; meglio comprarne uno nuovo? Guida pratica da Iglisi Watch a Durazzo basata su costo di riparazione, tipo, et&agrave; e valore sentimentale.'),
            sq=dict(title='Duhet Riparoj apo Blej Or&euml; t&euml; Re? Nj&euml; Udhëzues i Sinqert&euml;',
                    desc='Ia vlen t&euml; riparohet apo &euml;sht&euml; m&euml; mir&euml; ta z&euml;vend&euml;soni? Udhëzues praktik nga Iglisi Watch n&euml; Durr&euml;s bazuar n&euml; koston e riparimit, llojin dhe vler&euml;n sentimentale.'),
        ),
    ),
    dict(
        slug='watch-battery-replacement-durres', cat='care',
        card=dict(
            en=dict(title='Watch Battery Replacement in Durr&euml;s: Done While You Wait',
                    desc='Walk in with a dead watch, walk out with a working one. Battery replacements take a few minutes. No appointment needed, any brand welcome.'),
            it=dict(title='Sostituzione Batteria Orologio a Durr&euml;s - Pronto Mentre Aspetti',
                    desc='Portate il vostro orologio da Iglisi Watch a Durr&euml;s. Nessun appuntamento, pronto in pochi minuti, ispezione della guarnizione inclusa. Qualsiasi marca.'),
            sq=dict(title='Z&euml;vend&euml;simi i Bateris&euml; s&euml; Or&euml;s n&euml; Durr&euml;s - Gati Nd&euml;rkoh&euml; q&euml; Prisni',
                    desc='Ejani tek Iglisi Watch n&euml; Durr&euml;s. Gati n&euml; pak minuta, pa takim paraprak, inspektim i garnitur&euml;s i p&euml;rfshir&euml;. &Ccedil;do mark&euml; e mirëpritur.'),
        ),
    ),
    dict(
        slug='watch-strap-replacement-durres', cat='care',
        card=dict(
            en=dict(title='Watch Strap Replacement in Durr&euml;s: Same-Day Fitting',
                    desc='Leather, rubber, metal, and NATO options in stock. Fitted while you wait. Bracelet sizing and clasp repair done on the spot. Any brand, no appointment needed.'),
            it=dict(title='Sostituzione Cinturino Orologio a Durazzo - Montaggio in Giornata',
                    desc='Sostituzione cinturino o bracciale da Iglisi Watch a Durazzo. Pelle, gomma e metallo disponibili. Montato mentre aspettate, senza appuntamento. Qualsiasi marca.'),
            sq=dict(title='Z&euml;vend&euml;simi i Brezit t&euml; Or&euml;s n&euml; Durr&euml;s - Montim n&euml; T&euml; Nj&euml;jt&euml;n Dit&euml;',
                    desc='Z&euml;vend&euml;so brezin ose g&euml;rmaxhen tek Iglisi Watch n&euml; Durr&euml;s. L&euml;kur&euml;, gom&euml; dhe metal n&euml; magazin&euml;. Montohet nd&euml;rkoh&euml; q&euml; prisni, pa takim. &Ccedil;do mark&euml;.'),
        ),
    ),
    dict(
        slug='watch-crystal-replacement-durres', cat='care',
        card=dict(
            en=dict(title='Cracked Watch Glass? Crystal Replacement in Durr&euml;s',
                    desc='A cracked crystal removes the water seal entirely. Iglisi Watch replaces mineral and sapphire crystals same day if we have your size in stock. Any brand, no appointment.'),
            it=dict(title='Vetro Rotto? Sostituzione del Cristallo a Durazzo',
                    desc='Cristallo rotto o crepato a Durazzo? Iglisi Watch sostituisce cristalli minerali e zaffiro il giorno stesso se abbiamo la misura. Senza appuntamento, qualsiasi marca.'),
            sq=dict(title='Xhami i Thyer? Z&euml;vend&euml;simi i Kristalt&euml; n&euml; Durr&euml;s',
                    desc='Kristal i &ccedil;ar ose i thyer n&euml; Durr&euml;s? Iglisi Watch z&euml;vend&euml;son kristale minerale dhe safiri t&euml; nj&euml;jt&euml;n dit&euml; n&euml;se kemi m&euml;simin tuaj. Pa takim, &ccedil;do mark&euml;.'),
        ),
    ),
    dict(
        slug='hislon-classic-review', cat='buying',
        label=dict(en='Watch Review', it='Recensione Orologio', sq='Recensim Orësh'),
        card=dict(
            en=dict(title='Hislon Classic Review: Is It Worth It?',
                    desc='An honest assessment from the people who sell and service these watches daily. Build quality, real-world durability, and who it actually suits.'),
            it=dict(title='Recensione Hislon Classic: Vale la Pena?',
                    desc='Movimento al quarzo affidabile, vetro zaffiro, cassa in acciaio da 38&nbsp;mm. Una recensione onesta da chi lo revisiona ogni giorno in laboratorio.'),
            sq=dict(title='Recensim Hislon Classic: Ia Vlen?',
                    desc='L&euml;vizje kuarci e besueshme, xham safiri, kas&euml; &ccedil;eliku 38&nbsp;mm. Nj&euml; recensim i nd&euml;rsh&euml;m nga ai q&euml; e revisioni&ccedil;on &ccedil;do dit&euml; n&euml; punëtori.'),
        ),
    ),
    dict(
        slug='which-navimarine-to-buy', cat='buying',
        card=dict(
            en=dict(title='Which Navimarine Should You Buy?',
                    desc='Sport, classic, or chronograph: a guide to matching the right Navimarine model to your lifestyle and your budget.'),
            it=dict(title='Quale Navimarine Comprare: Sport, Classic o Chronograph?',
                    desc='Tre linee Navimarine, tre usi diversi. Come capire quale modello si adatta al tuo stile, al tuo budget e all&rsquo;occasione.'),
            sq=dict(title='Cilin Navimarine t&euml; Blesh: Sport, Classic apo Chronograph?',
                    desc='Tre linja Navimarine, tre p&euml;rdorime t&euml; ndryshme. Si t&euml; kuptoni cili model i p&euml;rshtatet stilit tuaj, buxhetit tuaj dhe rastit.'),
        ),
    ),
    # CONFLICT seeded en=buying it=gifts sq=gifts -> using buying
    dict(
        slug='first-watch-teenager', cat='buying',
        card=dict(
            en=dict(title='Best First Watch for a Teenager',
                    desc="What to look for, what to spend, and which watches actually survive daily life on a young person's wrist. A guide for parents and family."),
            it=dict(title='Il Primo Orologio per un Adolescente: Cosa Cercare',
                    desc='Il primo vero orologio &egrave; un regalo che ricordano per anni. Come scegliere il modello giusto - resistente, della giusta taglia e nel budget corretto.'),
            sq=dict(title='Ora e Par&euml; p&euml;r Adoleshentin: &Ccedil;far&euml; t&euml; K&euml;rkoni',
                    desc='Ora e par&euml; e v&euml;rtet&euml; &euml;sht&euml; nj&euml; dhuratë q&euml; e kujtojn&euml; vite me radh&euml;. Si t&euml; zgjidhni modelin e duhur - t&euml; qëndruesh&euml;m, t&euml; p&euml;rshtatsh&euml;m dhe brenda buxhetit.'),
        ),
    ),
    dict(
        slug='buy-watch-without-trying-on', cat='buying',
        card=dict(
            en=dict(title='Is It Safe to Buy a Watch Without Trying It On?',
                    desc='You pay at the door with the watch in your hands, you can refuse it for nothing, and we size the bracelet free at the counter. Why you do not need to measure anything first.'),
            it=dict(title='&Egrave; Sicuro Comprare un Orologio Senza Provarlo?',
                    desc='Pagate alla porta con l&rsquo;orologio in mano, potete rifiutarlo senza spendere nulla, e il bracciale lo adattiamo gratis al banco. Perch&eacute; non serve misurare niente.'),
            sq=dict(title='A &euml;sht&euml; e Sigurt&euml; t&euml; Blesh Or&euml; pa e Provuar?',
                    desc='E paguani te dera me or&euml;n n&euml; dor&euml;, mund ta refuzoni pa ju kushtuar asgj&euml;, dhe braceletin ua p&euml;rshtatim falas te banaku. Pse nuk ju duhet t&euml; matni asgj&euml;.'),
        ),
    ),
    dict(
        slug='best-watch-gifts-men-albania', cat='gifts',
        card=dict(
            en=dict(title='Best Watch Gifts for Men in Albania',
                    desc='Which watches make good gifts, which budgets make sense, and how to order anywhere in Albania without leaving home.'),
            it=dict(title='I Migliori Regali Orologio per Uomo in Albania',
                    desc='Idee regalo pratiche per gli uomini che gi&agrave; hanno tutto - orologi che durano, che si indossano ogni giorno e che si ricordano.'),
            sq=dict(title='Dhuratat m&euml; t&euml; Mira Or&euml; p&euml;r Burra n&euml; Shqip&euml;ri',
                    desc='Ide dhuratash praktike p&euml;r burrat q&euml; kan&euml; gjithka - or&euml; q&euml; zgjasin, q&euml; vishen &ccedil;do dit&euml; dhe q&euml; kujtohen.'),
        ),
    ),
    dict(
        slug='best-watch-gifts-women-albania', cat='gifts',
        card=dict(
            en=dict(title='Best Watch Gifts for Women in Albania',
                    desc="What to look for in a women's watch gift, which styles work for different occasions, and how to order with delivery anywhere in Albania."),
            it=dict(title='I Migliori Regali Orologio per Donna in Albania',
                    desc='Come scegliere un orologio per una donna - stile, dimensioni e budget - con suggerimenti concreti dalla nostra selezione in Albania.'),
            sq=dict(title='Dhuratat m&euml; t&euml; Mira Or&euml; p&euml;r Gra n&euml; Shqip&euml;ri',
                    desc='Si t&euml; zgjidhni or&euml; si dhuratë p&euml;r nj&euml; grua - stil, p&euml;rmasa dhe buxhet - me sugjerime konkrete nga selekcioni yn&euml; n&euml; Shqip&euml;ri.'),
        ),
    ),
    dict(
        slug='graduation-watch-ideas', cat='gifts',
        card=dict(
            en=dict(title='Graduation Watch Ideas Under &euro;200',
                    desc='The right watch for a new graduate entering work. Which brands suit which fields, and how to order with cash on delivery anywhere in Albania.'),
            it=dict(title='Idee Orologio per la Laurea: Come Scegliere il Regalo Giusto',
                    desc='Il regalo di laurea perfetto &egrave; uno che dura anni. Come scegliere un orologio che il laureato indosser&agrave; davvero - stile, budget e occasione.'),
            sq=dict(title='Ide Or&euml;sh p&euml;r Diplomim: Si t&euml; Zgjidhni Dhuratën e Duhur',
                    desc='Dhurata e duhur e diplomimit &euml;sht&euml; ajo q&euml; zgjat vite. Si t&euml; zgjidhni or&euml;n q&euml; diplomuari do ta veshë vërtet - stil, buxhet dhe rasti.'),
        ),
    ),
    dict(
        slug='watch-wedding-gift-albania', cat='gifts',
        card=dict(
            en=dict(title='Watch as a Wedding Gift in Albania',
                    desc='Why a watch makes a lasting wedding gift, which models are appropriate for groom and bride, and how to present it well.'),
            it=dict(title='Orologio come Regalo di Matrimonio in Albania: Guida Completa',
                    desc='Perch&eacute; un orologio &egrave; il regalo di nozze ideale, quali modelli funzionano per uomo e donna e come scegliere senza sbagliare.'),
            sq=dict(title='Or&euml; si Dhuratë Dasme n&euml; Shqip&euml;ri: Udhëzues i Plot&euml;',
                    desc='Pse ora &euml;sht&euml; dhurata ideale e dasmës, cil&euml;t modele funksionojn&euml; p&euml;r burrë dhe grua dhe si t&euml; zgjidhni pa gabuar.'),
        ),
    ),
    dict(
        slug='what-watch-service-includes', cat='care',
        card=dict(
            en=dict(title='What Does a Watch Service Actually Include?',
                    desc='From a battery change to a full movement overhaul: a plain-language guide to what each level of watch service involves and when each is needed.'),
            it=dict(title='Cosa Include Davvero una Revisione dell&rsquo;Orologio?',
                    desc='Smontaggio completo, pulizia, lubrificazione, verifica dell&rsquo;impermeabilit&agrave; - quello che succede realmente durante una revisione di livello&nbsp;4 in laboratorio.'),
            sq=dict(title='&Ccedil;far&euml; P&euml;rfshine Sh&euml;rbimi i Or&euml;s?',
                    desc='Çmontim i plot&euml;, pastrim, lubrifikim, kontroll i rezistenc&euml;s ndaj ujit - &ccedil;far&euml; ndodh realisht gjat&euml; nj&euml; sh&euml;rbimi t&euml; nivelit&nbsp;4 n&euml; punëtori.'),
        ),
    ),
    dict(
        slug='watch-repair-durres', cat='care',
        label=dict(en='Watch Care', it='Riparazione', sq='Riparim'),
        card=dict(
            en=dict(title='Watch Repair in Durr&euml;s: What to Expect',
                    desc='What happens when you bring a watch to our workshop: the assessment process, common repairs, how pricing works, and what we can fix in-house.'),
            it=dict(title='Riparazione Orologi a Durazzo: Cosa Aspettarsi',
                    desc='Cambio batteria, sostituzione cinturino, nuovo vetro, revisione completa - una guida onesta su tempi, costi e come funziona il nostro laboratorio a Durr&euml;s.'),
            sq=dict(title='Riparim Orash n&euml; Durr&euml;s: &Ccedil;far&euml; t&euml; Prisni',
                    desc='Ndërrimi i baterisë, z&euml;v&euml;nd&euml;simi i rripit, xhami i ri, revisioni i plot&euml; - nj&euml; udhëzues i nd&euml;rsh&euml;m mbi kohën, &ccedil;mimin dhe si funksionon punëtoria jon&euml; n&euml; Durrës.'),
        ),
    ),
    dict(
        slug='watch-warranty-guide', cat='care',
        card=dict(
            en=dict(title='What Warranty Do New Watches Come With?',
                    desc='A plain-language guide to what a new watch warranty covers, what voids it, and how to make a claim if something goes wrong.'),
            it=dict(title='Che Garanzia Viene con un Orologio Nuovo?',
                    desc='Cosa copre davvero la garanzia, cosa non copre, cosa la annulla e come presentare un reclamo - una guida chiara per chi acquista un orologio nuovo.'),
            sq=dict(title='&Ccedil;far&euml; Garanci Vijnë me Or&euml;t e Reja?',
                    desc='&Ccedil;far&euml; mbulon realisht garancia, &ccedil;far&euml; jo, &ccedil;far&euml; e anullon dhe si t&euml; paraqisësh nj&euml; k&euml;rkes&euml; - nj&euml; udhëzues i qart&euml; p&euml;r bler&euml;sin e or&euml;ve t&euml; reja.'),
        ),
    ),
    dict(
        slug='buy-watch-instagram-albania', cat='buying',
        label=dict(en='Watch Buying Guide', it='Guida all’Acquisto', sq='Udhëzues Blerje'),
        card=dict(
            en=dict(title='Is It Safe to Buy a Watch on Instagram in Albania?',
                    desc='Instagram watch sellers in Albania are everywhere - but is it safe? Real risks, red flags, and when a physical shop is always the better choice.'),
            it=dict(title='È Sicuro Comprare un Orologio su Instagram in Albania?',
                    desc='I venditori di orologi su Instagram in Albania sono ovunque - ma è sicuro? Rischi reali, segnali d&rsquo;allarme e quando fidarsi di un negozio fisico.'),
            sq=dict(title='A është e Sigurt të Blesh Orë në Instagram në Shqipëri?',
                    desc='Shitësit e orëve në Instagram në Shqipëri janë kudo - por a është e sigurt? Rreziqet reale, shenjat paralajmëruese dhe kur të zgjidhni dyqanin fizik.'),
        ),
    ),
    dict(
        slug='where-to-buy-watch-durres', cat='buying',
        label=dict(en='Local Guide', it='Guida Locale', sq='Udhëzues Lokal'),
        card=dict(
            en=dict(title='Where to Buy a Watch in Durr&euml;s: An Honest Guide',
                    desc='Street markets, jewellery shops, or specialist watchmakers - a straight-talking look at the Durrës watch market, what to trust, and what to walk away from.'),
            it=dict(title='Dove Comprare un Orologio a Durazzo: Una Guida Onesta',
                    desc='Mercati di strada, gioiellerie o orologiai specializzati - una panoramica diretta del mercato degli orologi di Durr&euml;s, cosa fidarsi e cosa evitare.'),
            sq=dict(title='Ku të Blesh një Orë në Durrës: Udhëzues i Sinqertë',
                    desc='Tregjet e rrugës, argjendaria ose orëtarët specialistë - vështrim i drejtpërdrejtë mbi tregun e orëve të Durrësit, çfarë të besohet dhe çfarë të shmanget.'),
        ),
    ),
    dict(
        slug='hislon-vs-navimarine', cat='buying',
        label=dict(en='Brand Comparison', it='Confronto Marchi', sq='Krahasim Markash'),
        card=dict(
            en=dict(title='Hislon vs Navimarine: Which Watch Brand Is Right for You?',
                    desc='Both sit in the same price range and are built for daily wear - but they appeal to very different tastes. A clear-headed comparison to help you choose.'),
            it=dict(title='Hislon vs Navimarine: Quale Marchio di Orologi fa per Te?',
                    desc='Entrambi nella stessa fascia di prezzo, costruiti per l&rsquo;uso quotidiano - ma si rivolgono a gusti molto diversi. Un confronto obiettivo per aiutarti a scegliere.'),
            sq=dict(title='Hislon vs Navimarine: Cilën Markë Orësh të Zgjidhni?',
                    desc='Të dyja në të njëjtën gamë çmimesh, ndërtuar për veshje të përditshme - por i drejtohen shijeve shumë të ndryshme. Krahasim objektiv për t&rsquo;ju ndihmuar të zgjidhni.'),
        ),
    ),
    dict(
        slug='watch-magnetisation', cat='care',
        card=dict(
            en=dict(title="Watch Magnetisation: What It Is, What Causes It, and How It's Fixed",
                    desc="A magnetised watch can lose minutes per day with no visible damage. Here's what causes it, how to test for it with a compass, and how demagnetisation works."),
            it=dict(title='Magnetizzazione dell&rsquo;Orologio: Cause, Sintomi e Come Smagnetizzarlo',
                    desc='Telefono, chiusura magnetica della borsa, altoparlante - bastano pochi secondi per magnetizzare il bilanciere. Scopri i sintomi e come risolvere il problema.'),
            sq=dict(title='Pse Ora Magnetizohet - dhe Si ta Rregulloni',
                    desc='Ora fiton minuta &ccedil;do dit&euml; pa asnjë arsye? Ka shumë mundësi t&euml; jet&euml; magnetizuar. Diagnoza kërkon sekonda. Rregullimi kërkon n&euml;n nj&euml; minut&euml;.'),
        ),
    ),
    dict(
        slug='watch-winding-guide', cat='care',
        label=dict(en='Watch Maintenance', it='Manutenzione Orologio', sq='Mirëmbajtja e Orës'),
        card=dict(
            en=dict(title='How to Wind Your Watch: Manual, Automatic &amp; Setting the Crown',
                    desc='Winding incorrectly is one of the most common causes of premature movement wear. The right technique, the three crown positions explained, and 5 mistakes to avoid.'),
            it=dict(title='Come Caricare il Tuo Orologio: Manuale, Automatico &amp; Posizioni della Corona',
                    desc='La tecnica di carica corretta per orologi manuali e automatici, le tre posizioni della corona spiegate e 5 errori comuni che danneggiano i movimenti.'),
            sq=dict(title='Si t&euml; Mbushni Or&euml;n: Manual, Automatike &amp; Pozicionet e Kuror&euml;s',
                    desc='Teknika e duhur e mbushjes p&euml;r or&euml;t manuale dhe automatike, tre pozicionet e kuror&euml;s t&euml; shpjeguara dhe 5 gabime t&euml; zakonshme q&euml; d&euml;mtojn&euml; l&euml;vizjet.'),
        ),
    ),
    dict(
        slug='spot-fake-watch', cat='knowledge',
        card=dict(
            en=dict(title='How to Spot a Fake Watch: 8 Things Experts Check First',
                    desc='Buying second-hand or unsure about an inherited piece? These are the 8 physical checks that reveal a counterfeit - no specialist equipment needed.'),
            it=dict(title='Come Riconoscere un Orologio Falso: 8 Controlli degli Esperti',
                    desc='Dal peso della cassa alla sensazione della corona - gli 8 controlli fisici che rivelano un falso senza attrezzatura specializzata.'),
            sq=dict(title='Si t&euml; Dalloni Or&euml;n Falsifikuar: 8 Kontrolle t&euml; Ekspert&euml;ve',
                    desc='Nga pesha e kas&euml;s te ndjesja e kuror&euml;s - 8 kontrollet fizike q&euml; zbulojn&euml; nj&euml; falsifikim pa pajisje t&euml; specializuara.'),
        ),
    ),
    dict(
        slug='watch-storage-guide', cat='care',
        label=dict(en='Watch Care', it='Cura Orologio', sq='Kujdesi i Orës'),
        card=dict(
            en=dict(title='How to Store Your Watch Properly: A Complete Guide',
                    desc='Wrong storage degrades lubricants, magnetises movements, and cracks straps. Learn the optimal conditions - temperature, humidity, and what should never sit next to a watch.'),
            it=dict(title='Come Conservare il Tuo Orologio Correttamente: Guida Completa',
                    desc='La conservazione sbagliata danneggia i lubrificanti, magn&eacute;tizza i movimenti e fa spellare i cinturini. Scopri le condizioni ottimali - temperatura, umidit&agrave; e cosa evitare.'),
            sq=dict(title='Si t&euml; Ruani Or&euml;n Tuaj Si&ccedil; Duhet: Udhëzues i Plot&euml;',
                    desc='Ruajtja gabim d&euml;mton lubrifikant&euml;t, magnetizon mekanizmin dhe bën t&euml; rrec&euml;jë rripin. M&euml;soni kushtet optimale - temperatura, lagështia dhe &ccedil;far&euml; t&euml; shmangni.'),
        ),
    ),
    dict(
        slug='watch-crystal-guide', cat='care',
        label=dict(en='Watch Care', it='Cura Orologio', sq='Kujdesi i Orës'),
        card=dict(
            en=dict(title='Watch Crystals Explained: Acrylic, Mineral, and Sapphire - What&rsquo;s the Difference?',
                    desc='Three materials, three levels of protection. Learn which scratch easily, which shatter, and what to do when your watch crystal is damaged.'),
            it=dict(title='Cristalli per Orologi: Acrilico, Minerale e Zaffiro - Qual &egrave; la Differenza?',
                    desc='Tre materiali, tre livelli di protezione. Scopri quali si graffiano facilmente, quali si rompono e cosa fare quando il vetro del tuo orologio &egrave; danneggiato.'),
            sq=dict(title='Xhami i Or&euml;s: Akrilik, Mineral dhe Safir - Cili &euml;sht&euml; Ndryshimi?',
                    desc='Tre materiale, tre nivele mbrojtjeje. M&euml;so cilat g&euml;rvishten leht&euml;, cilat thyhen dhe &ccedil;far&euml; t&euml; b&euml;sh kur xhami i or&euml;s d&euml;mtohet.'),
        ),
    ),
    dict(
        slug='watch-battery-guide', cat='care',
        label=dict(en='Watch Care', it='Cura Orologio', sq='Kujdesi i Orës'),
        card=dict(
            en=dict(title='How Long Does a Watch Battery Last? Signs It&rsquo;s Dying &amp; What To Do',
                    desc='Most quartz watch batteries last 1&ndash;3 years. Learn the 5 warning signs your battery is failing, whether you should replace it yourself, and what a professional swap involves.'),
            it=dict(title='Quanto Dura la Batteria di un Orologio? Segnali di Scarica e Cosa Fare',
                    desc='Le batterie degli orologi al quarzo durano 1&ndash;3 anni. Scopri i 5 segnali d&rsquo;allarme, se conviene sostituirla da soli e cosa comporta una sostituzione professionale.'),
            sq=dict(title='Sa Zgjat Bateria e Or&euml;s? Shenjat q&euml; Po D&euml;shtron &amp; &Ccedil;far&euml; t&euml; B&euml;ni',
                    desc='Baterit&euml; e oreve kuarc zgjasin 1&ndash;3 vjet. M&euml;so 5 shenjat paralajm&euml;ruese, n&euml;se duhet ta ndërrosh vet&euml; dhe &ccedil;far&euml; p&euml;rfshine nd&euml;rrimi profesional.'),
        ),
    ),
    dict(
        slug='watch-service-signs', cat='care',
        label=dict(en='Watch Maintenance', it='Manutenzione', sq='Mirëmbajtja'),
        card=dict(
            en=dict(title='5 Signs Your Watch Needs a Service, Not Just a New Battery',
                    desc='If your watch loses time after a fresh battery, feels gritty when wound, or has had moisture inside - it needs a service. Learn the 5 signs and what a professional overhaul involves.'),
            it=dict(title='5 Segnali che il Tuo Orologio ha Bisogno di una Revisione, Non Solo di una Batteria Nuova',
                    desc='Se il tuo orologio perde tempo con una batteria appena installata, la corona &egrave; grattante o ha avuto umidit&agrave; - ha bisogno di una revisione. Scopri i 5 segnali.'),
            sq=dict(title='5 Shenja q&euml; Ora Juaj Ka Nevoj&euml; p&euml;r Riparim, Jo Vetëm Bateri t&euml; Re',
                    desc='N&euml;se ora juaj humb koh&euml; pas bateris&euml; s&euml; re, kurora &euml;sht&euml; e vrazhd&euml; ose ka pasur lag&euml;shti - ka nevoj&euml; p&euml;r riparim. M&euml;soni 5 shenjat.'),
        ),
    ),
    dict(
        slug='watch-strap-care', cat='care',
        label=dict(en='Watch Care', it='Cura Orologio', sq='Kujdesi i Orës'),
        card=dict(
            en=dict(title='How to Care for Your Watch Strap: Leather, Metal &amp; Rubber Guide',
                    desc='The strap is the most worn part of any watch. Learn how to clean and condition leather, maintain metal bracelets, and when it&rsquo;s time to replace - for any material.'),
            it=dict(title='Come Prendersi Cura del Cinturino dell&rsquo;Orologio: Guida per Pelle, Metallo e Gomma',
                    desc='Il cinturino &egrave; la parte pi&ugrave; usurata di qualsiasi orologio. Scopri come pulire e nutrire la pelle, mantenere il bracciale in metallo e quando &egrave; il momento di sostituirlo.'),
            sq=dict(title='Si t&euml; Kujdeseni p&euml;r Brezin e Or&euml;s: L&euml;kur&euml;, Metal dhe Gom&euml;',
                    desc='Brezi &euml;sht&euml; pjesa m&euml; e p&euml;rdorur e &ccedil;do ore. M&euml;soni si t&euml; pastroni dhe kushtoni l&euml;kur&euml;n, si t&euml; mir&euml;mbani byzylykun metalik dhe kur duhet ta z&euml;v&euml;nd&euml;soni.'),
        ),
    ),
    dict(
        slug='key-duplication-guide', cat='keys',
        card=dict(
            en=dict(title='How Key Duplication Works: Types, What to Bring &amp; What to Expect',
                    desc='Getting a spare key cut takes under 5 minutes - if you know what to bring. Learn which keys we can duplicate, how the cutting process works, and how many copies you should make.'),
            it=dict(title='Come Funziona il Duplicato di Chiavi: Tipi, Cosa Portare e Cosa Aspettarsi',
                    desc='Fare un duplicato richiede meno di 5 minuti - se sai cosa portare. Scopri quali chiavi possiamo duplicare, come funziona il processo di taglio e quante copie dovresti fare.'),
            sq=dict(title='Si Funksionon Kopjimi i &Ccedil;elësave: Llojet, &Ccedil;far&euml; t&euml; Sillni &amp; &Ccedil;far&euml; t&euml; Prisni',
                    desc='B&euml;rja e nj&euml; kopje k&euml;rkon m&euml; pak se 5 minuta - n&euml;se dini &ccedil;far&euml; t&euml; sillni. M&euml;soni cil&euml;t &ccedil;elësa mund t&euml; kopjohen dhe sa kopje duhet t&euml; b&euml;ni.'),
        ),
    ),
    dict(
        slug='watch-water-resistance', cat='care',
        label=dict(en='Watch Care', it='Cura Orologio', sq='Kujdesi i Orës'),
        card=dict(
            en=dict(title='Watch Water Resistance Ratings Explained: ATM, BAR &amp; What They Really Mean',
                    desc='Your watch says &ldquo;water resistant&rdquo; - but does that mean you can swim, shower, or dive with it? Most people misread these ratings and damage their watch as a result.'),
            it=dict(title='Impermeabilit&agrave; degli Orologi: Cosa Significano Davvero ATM, BAR e Metri',
                    desc='Il tuo orologio dice &ldquo;impermeabile&rdquo; - ma puoi nuotarci o farci la doccia? La maggior parte delle persone fraintende queste classificazioni e rovina il proprio orologio.'),
            sq=dict(title='Rezistenca ndaj Ujit e Or&euml;ve: Kuptoni ATM, BAR dhe Metrat',
                    desc='Ora juaj thot&euml; &ldquo;rezistente ndaj ujit&rdquo; - por a mund t&euml; notoni apo laheni me t&euml;? Shumica keqkuptojn&euml; k&euml;to klasifikime dhe d&euml;mtojn&euml; or&euml;n e tyre.'),
        ),
    ),
    dict(
        slug='watch-cleaning-guide', cat='care',
        label=dict(en='Watch Care', it='Cura Orologio', sq='Kujdesi i Orës'),
        card=dict(
            en=dict(title='How to Clean Your Watch at Home: Safe Methods for Every Material',
                    desc='Dirt, sweat, and grime build up on every watch - even expensive ones. Regular cleaning takes under five minutes and keeps your watch looking new.'),
            it=dict(title='Come Pulire il Tuo Orologio in Casa: Metodi Sicuri per Ogni Materiale',
                    desc='Lo sporco, il sudore e il grasso si accumulano su ogni orologio - anche su quelli costosi. La pulizia regolare richiede meno di cinque minuti. Guida passo per passo.'),
            sq=dict(title='Si t&euml; Pastroni Or&euml;n Tuaj n&euml; Shtp&euml;i: Metoda t&euml; Sigurta p&euml;r &Ccedil;do Material',
                    desc='Papastërtia, djers&euml; dhe lyra grumbullohen n&euml; &ccedil;do or&euml;. Pastrimi i rregullt k&euml;rkon m&euml; pak se pes&euml; minuta dhe e mban or&euml;n tuaj si e re.'),
        ),
    ),
]
