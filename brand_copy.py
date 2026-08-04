#!/usr/bin/env python3
"""
brand_copy.py
Localized brand-page copy for gen_brand_pages.py, kept separate so the generator
stays readable.

RULE: only owner-verified facts appear here.
  Daniel Klein  Turkish brand, quartz, 3-5 BAR (state as a range, tell readers to ask
                per model), gold-tone is plated. NEVER claim a crystal type.
  Navimarine    quartz, solid steel cases and bracelets. CRYSTAL TYPE IS NOT VERIFIED:
                do not claim one until the owner confirms it on the bench. Two models
                state 5 ATM: the Steel 5ATM Blue and the NT0021-1 (watch-27).
  Hislon        sapphire crystal, marked Swiss, dress category. A higher price buys the
                dress design and finish, not a better movement or more water resistance.
  Philippe Lauren  visible facts only: chronograph layouts, steel and black ion-plated
                steel, one square cushion case, one gold-tone dress model.
  Bigotti       visible facts only. NOTHING about the company is owner-verified: no country
                of origin, no history, no crystal type, no water resistance, no diameter.
                Quartz is stated ONLY on the two BG.1.10616 squares, so never write that the
                whole line is quartz. The crystal-set bezels are SET STONES, never diamonds
                and never the glass. The BG1.10154.1 is multifunction in a three-pusher
                chronograph case: it is not a chronograph, and the site says so already.
                The owner stocks more Bigotti than is published, so every number here is a
                placeholder and never a literal.

Placeholders filled at build time: {n} models, {lo}/{hi} price range, {lolek}/{hilek}.
"""

COPY = {
    "daniel-klein": {
        "en": {
            "paras": [
                "Daniel Klein is a Turkish watch brand and one of the best value lines we carry. We keep {n} models in Durrës, from €{lo} to €{hi}, covering steel sport watches, chronographs and slim dress pieces for men and women.",
                "Every Daniel Klein we sell runs on a quartz movement, so it keeps time without winding and needs only a battery every couple of years. Water resistance across the range is 3 to 5 BAR: fine for rain and hand washing, and the 5 BAR models are fine for a swim, but none of them is a diving watch. Ask us about the exact model you are looking at and we will tell you what it is rated for.",
                "The gold-tone models are plated rather than solid gold, so keep them out of salt water to protect the finish. Every watch comes with our 1-year guarantee.",
            ],
            "faq": [
                ("Are Daniel Klein watches good for the money?",
                 "For €{lo} to €{hi} you get a steel case, a reliable quartz movement and a 1-year guarantee from us. They are not luxury watches and they are not Swiss, but for an everyday watch that looks smart and keeps accurate time they are one of the best value options we stock."),
                ("Can I swim with a Daniel Klein watch?",
                 "It depends on the model. The range is rated 3 to 5 BAR. A 3 BAR watch handles rain and hand washing, a 5 BAR watch is fine for a swim at the surface. None of them is a diving watch. Message us with the model and we will confirm its rating."),
                ("Where can I buy Daniel Klein watches in Albania?",
                 "At Iglisi Watch on Rruga Aleksander Goga in Durrës. We keep {n} models in stock, you can try them on in the shop, or order on WhatsApp with cash on delivery anywhere in Albania including Tirana."),
            ],
        },
        "it": {
            "paras": [
                "Daniel Klein è un marchio di orologi turco e una delle linee col miglior rapporto qualità prezzo che trattiamo. Teniamo {n} modelli a Durazzo, da €{lo} a €{hi}, tra orologi sportivi in acciaio, cronografi e pezzi da abito sottili per uomo e donna.",
                "Ogni Daniel Klein che vendiamo monta un movimento al quarzo, quindi tiene l’ora senza carica manuale e richiede solo una batteria ogni paio d’anni. La resistenza all’acqua della gamma va da 3 a 5 BAR: bene per pioggia e lavaggio delle mani, e i modelli 5 BAR vanno bene per una nuotata, ma nessuno è un orologio subacqueo. Chiedeteci del modello preciso e vi diremo per cosa è certificato.",
                "I modelli color oro sono placcati e non in oro massiccio, quindi teneteli lontani dall’acqua salata per proteggere la finitura. Ogni orologio ha la nostra garanzia di 1 anno.",
            ],
            "faq": [
                ("Gli orologi Daniel Klein valgono il prezzo?",
                 "Per €{lo} a €{hi} avete una cassa in acciaio, un movimento al quarzo affidabile e una garanzia di 1 anno da parte nostra. Non sono orologi di lusso e non sono svizzeri, ma per un orologio quotidiano curato e preciso sono una delle scelte col miglior rapporto qualità prezzo che teniamo."),
                ("Posso nuotare con un Daniel Klein?",
                 "Dipende dal modello. La gamma è certificata da 3 a 5 BAR. Un 3 BAR regge pioggia e lavaggio delle mani, un 5 BAR va bene per una nuotata in superficie. Nessuno è un orologio subacqueo. Scriveteci indicando il modello e vi confermiamo la certificazione."),
                ("Dove posso comprare orologi Daniel Klein in Albania?",
                 "Da Iglisi Watch in Rruga Aleksander Goga a Durazzo. Teniamo {n} modelli disponibili, potete provarli in negozio oppure ordinare su WhatsApp con pagamento alla consegna in tutta l’Albania, Tirana inclusa."),
            ],
        },
        "sq": {
            "paras": [
                "Daniel Klein është një markë turke orësh dhe një nga linjat me raportin më të mirë çmim vlerë që mbajmë. Kemi {n} modele në Durrës, nga €{lo} deri €{hi}, mes orësh sportive çeliku, kronografësh dhe copash të holla veshjeje për burra dhe gra.",
                "Çdo Daniel Klein që shesim punon me lëvizje kuarci, ndaj mban orarin pa u kurdisur dhe kërkon vetëm një bateri çdo dy vjet. Rezistenca ndaj ujit në gjithë gamën është 3 deri 5 BAR: e përshtatshme për shi dhe larje duarsh, dhe modelet 5 BAR janë në rregull për një not, por asnjë prej tyre nuk është orë zhytjeje. Na pyesni për modelin e saktë dhe ju themi për çfarë është certifikuar.",
                "Modelet në ngjyrë ari janë të veshura dhe jo ar masiv, ndaj mbajini larg ujit të kripur për të mbrojtur finiturën. Çdo orë vjen me garancinë tonë 1-vjeçare.",
            ],
            "faq": [
                ("A ia vlejnë orët Daniel Klein për çmimin?",
                 "Për €{lo} deri €{hi} merrni një kasë çeliku, një lëvizje kuarci të besueshme dhe një garanci 1-vjeçare nga ne. Nuk janë orë luksi dhe nuk janë zvicerane, por për një orë të përditshme që duket e kujdesshme dhe mban kohën saktë, janë ndër opsionet më të mira që kemi në gjendje."),
                ("A mund të notoj me një Daniel Klein?",
                 "Varet nga modeli. Gama është e certifikuar 3 deri 5 BAR. Një orë 3 BAR përballon shiun dhe larjen e duarve, një 5 BAR është në rregull për not në sipërfaqe. Asnjë nuk është orë zhytjeje. Na shkruani modelin dhe jua konfirmojmë certifikimin."),
                ("Ku mund të blej orë Daniel Klein në Shqipëri?",
                 "Te Iglisi Watch në Rrugën Aleksander Goga në Durrës. Mbajmë {n} modele në gjendje, mund t’i provoni në dyqan ose të porosisni në WhatsApp me pagesë në dorëzim kudo në Shqipëri, përfshirë Tiranën."),
            ],
        },
    },

    "navimarine": {
        "en": {
            "paras": [
                "Navimarine is the brand we stock most deeply: {n} models in Durrës, from €{lo} to €{hi}. It covers everyday steel watches, colourful marine-styled pieces and classic dress designs for men and women.",
                "What makes Navimarine good value is the build for the money: solid stainless steel cases and bracelets, and shapes you normally pay a good deal more for, from a dive-style bezel to an integrated bracelet to gold-tone dress models. The movements are quartz, so they are accurate and only need an occasional battery.",
                "Water resistance is only officially stated on two models. The Steel 5ATM Blue and the NT0021-1 are both rated 5 ATM, which is fine for swimming at the surface. For any other model, ask us before you take it near water and we will tell you what we know.",
            ],
            "faq": [
                ("Is Navimarine a good watch brand?",
                 "For the price it is the best value we stock. You get a solid steel case and bracelet, a quartz movement that is accurate and cheap to maintain, and our 1-year guarantee. We do not publish a crystal type for Navimarine, so ask us about the exact model and we will tell you what we know."),
                ("Which Navimarine can I swim with?",
                 "The Steel 5ATM Blue and the NT0021-1 both carry a stated 5 ATM rating, which is fine for swimming at the surface. Water resistance is not officially stated on any other model, so message us with the one you like and we will tell you what we know before you buy."),
                ("Where can I buy a Navimarine watch in Albania?",
                 "Iglisi Watch in Durrës is a specialist Navimarine dealer with {n} models in stock from €{lo}. Come and try them on at Rruga Aleksander Goga, or order on WhatsApp with cash on delivery anywhere in Albania."),
            ],
        },
        "it": {
            "paras": [
                "Navimarine è il marchio di cui teniamo più scelta: {n} modelli a Durazzo, da €{lo} a €{hi}. Comprende orologi quotidiani in acciaio, pezzi colorati in stile marino e design classici da abito per uomo e donna.",
                "Il vero punto di forza di Navimarine è quanto costruito offre per il prezzo: casse e bracciali in acciaio inossidabile solido e forme per cui di solito si paga molto di più, dalla lunetta in stile subacqueo al bracciale integrato ai modelli da abito color oro. I movimenti sono al quarzo, quindi precisi e con la sola necessità di una batteria ogni tanto.",
                "La resistenza all’acqua è dichiarata ufficialmente solo su due modelli. Lo Steel 5ATM Blue e il NT0021-1 sono entrambi certificati 5 ATM, adatti al nuoto in superficie. Per ogni altro modello chiedeteci prima di avvicinarlo all’acqua e vi diremo quello che sappiamo.",
            ],
            "faq": [
                ("Navimarine è un buon marchio di orologi?",
                 "Per il prezzo è il miglior rapporto qualità prezzo che teniamo. Avete una cassa e un bracciale in acciaio solido, un movimento al quarzo preciso ed economico da mantenere e la nostra garanzia di 1 anno. Non pubblichiamo il tipo di vetro per Navimarine, quindi chiedeteci del modello esatto e vi diremo quello che sappiamo."),
                ("Con quale Navimarine posso nuotare?",
                 "Lo Steel 5ATM Blue e il NT0021-1 hanno entrambi una certificazione dichiarata di 5 ATM, adatta al nuoto in superficie. La resistenza all’acqua non è dichiarata ufficialmente su nessun altro modello, quindi scriveteci indicando quello che vi piace e vi diremo quello che sappiamo prima dell’acquisto."),
                ("Dove posso comprare un orologio Navimarine in Albania?",
                 "Iglisi Watch a Durazzo è rivenditore specializzato Navimarine con {n} modelli disponibili da €{lo}. Venite a provarli in Rruga Aleksander Goga oppure ordinate su WhatsApp con pagamento alla consegna in tutta l’Albania."),
            ],
        },
        "sq": {
            "paras": [
                "Navimarine është marka për të cilën mbajmë më shumë zgjedhje: {n} modele në Durrës, nga €{lo} deri €{hi}. Përfshin orë të përditshme çeliku, copa me ngjyra në stil detar dhe dizajne klasike veshjeje për burra dhe gra.",
                "Ajo që e bën Navimarine vlerë të mirë është sa ndërtim merrni për çmimin: kasa dhe byzylykë çeliku inoks solid, dhe forma për të cilat zakonisht paguani shumë më shumë, nga luneta në stil zhytjeje te byzylyku i integruar e te modelet e veshjes ngjyrë ari. Lëvizjet janë kuarci, ndaj janë të sakta dhe kërkojnë vetëm ndonjë bateri herë pas here.",
                "Rezistenca ndaj ujit deklarohet zyrtarisht vetëm në dy modele. Steel 5ATM Blue dhe NT0021-1 janë të dyja të certifikuara 5 ATM, të përshtatshme për not në sipërfaqe. Për çdo model tjetër na pyesni para se ta afroni te uji dhe ju themi atë që dimë.",
            ],
            "faq": [
                ("A është Navimarine një markë e mirë orësh?",
                 "Për çmimin është vlera më e mirë që mbajmë. Merrni kasë dhe byzylyk çeliku solid, një mekanizëm kuarci të saktë dhe të lirë për mirëmbajtje, dhe garancinë tonë 1-vjeçare. Ne nuk publikojmë llojin e xhamit për Navimarine, ndaj na pyesni për modelin e saktë dhe ju themi atë që dimë."),
                ("Me cilin Navimarine mund të notoj?",
                 "Steel 5ATM Blue dhe NT0021-1 kanë të dyja një certifikim të deklaruar 5 ATM, të përshtatshëm për not në sipërfaqe. Rezistenca ndaj ujit nuk është deklaruar zyrtarisht në asnjë model tjetër, ndaj na shkruani për atë që ju pëlqen dhe ju themi atë që dimë para se ta blini."),
                ("Ku mund të blej një orë Navimarine në Shqipëri?",
                 "Iglisi Watch në Durrës është shitës specialist i Navimarine me {n} modele në gjendje nga €{lo}. Ejani t’i provoni në Rrugën Aleksander Goga ose porositni në WhatsApp me pagesë në dorëzim kudo në Shqipëri."),
            ],
        },
    },

    "hislon": {
        "en": {
            "paras": [
                "Hislon is the dress end of what we sell: {n} models in Durrës from €{lo} to €{hi}. These are the watches people buy for a wedding, a graduation or an anniversary, and they are marked as Swiss.",
                "Every Hislon we stock uses a sapphire crystal, so the glass resists the scratches that make an older watch look tired. The finishing is what you are paying for: mother-of-pearl dials with crystal indices on the ladies' models, applied markers, polished gold-tone and steel bracelets, and chronograph layouts on the sport pieces.",
                "Worth being straight about: a higher price here does not buy a better movement or more water resistance than our cheaper brands. It buys the dress design and the finish. Every watch carries our 1-year guarantee.",
            ],
            "faq": [
                ("Are Hislon watches Swiss?",
                 "They are marked as Swiss. What we can tell you for certain from the watches themselves is that they use sapphire crystals, they are dress-focused in design and finish, and they are the most refined watches we carry at €{lo} to €{hi}."),
                ("Why is Hislon more expensive than your other brands?",
                 "You are paying for the dress category and the finishing, not for a better movement. Mother-of-pearl dials, crystal indices, applied markers and polished bracelets cost more to make. A €{lo} Hislon and a cheaper watch from us both use quartz movements and both carry the same 1-year guarantee."),
                ("Is a Hislon a good wedding or graduation gift?",
                 "It is the range we sell most often as a gift. The dress designs suit a formal occasion, the sapphire crystal keeps it looking new, and we can show you {n} models side by side in Durrës before you decide."),
            ],
        },
        "it": {
            "paras": [
                "Hislon è la fascia da abito di ciò che vendiamo: {n} modelli a Durazzo da €{lo} a €{hi}. Sono gli orologi che si comprano per un matrimonio, una laurea o un anniversario, e sono marcati come svizzeri.",
                "Ogni Hislon che teniamo usa un cristallo zaffiro, quindi il vetro resiste ai graffi che fanno sembrare stanco un orologio con gli anni. Quello che pagate è la finitura: quadranti in madreperla con indici in cristallo sui modelli da donna, indici applicati, bracciali lucidi color oro e acciaio e layout cronografici sui pezzi sportivi.",
                "Vale la pena essere chiari: un prezzo più alto qui non compra un movimento migliore né più resistenza all’acqua rispetto ai nostri marchi più economici. Compra il design da abito e la finitura. Ogni orologio ha la nostra garanzia di 1 anno.",
            ],
            "faq": [
                ("Gli orologi Hislon sono svizzeri?",
                 "Sono marcati come svizzeri. Quello che possiamo dirvi con certezza dagli orologi stessi è che usano cristalli zaffiro, che il design e la finitura sono orientati all’abito e che sono gli orologi più raffinati che trattiamo tra €{lo} e €{hi}."),
                ("Perché Hislon costa più degli altri vostri marchi?",
                 "Pagate la categoria da abito e la finitura, non un movimento migliore. Quadranti in madreperla, indici in cristallo, indici applicati e bracciali lucidi costano di più da produrre. Un Hislon da €{lo} e un nostro orologio più economico usano entrambi movimenti al quarzo e hanno entrambi la stessa garanzia di 1 anno."),
                ("Un Hislon è un buon regalo di matrimonio o laurea?",
                 "È la gamma che vendiamo più spesso come regalo. I design da abito si adattano a un’occasione formale, il cristallo zaffiro lo mantiene come nuovo e possiamo mostrarvi {n} modelli affiancati a Durazzo prima che decidiate."),
            ],
        },
        "sq": {
            "paras": [
                "Hislon është skaji i veshjes i asaj që shesim: {n} modele në Durrës nga €{lo} deri €{hi}. Këto janë orët që njerëzit blejnë për një dasmë, një diplomim ose një përvjetor, dhe janë të markuara si zvicerane.",
                "Çdo Hislon që mbajmë përdor xham safir, ndaj xhami u reziston gërvishtjeve që e bëjnë një orë të duket e lodhur me vitet. Ajo që paguani është finitura: ciferblatë sedefi me tregues kristali në modelet për femra, tregues të aplikuar, byzylykë të lëmuar në ngjyrë ari dhe çeliku, dhe skema kronografi në copat sportive.",
                "Ia vlen ta themi troç: një çmim më i lartë këtu nuk blen një lëvizje më të mirë as më shumë rezistencë ndaj ujit se markat tona më të lira. Blen dizajnin e veshjes dhe finiturën. Çdo orë ka garancinë tonë 1-vjeçare.",
            ],
            "faq": [
                ("A janë orët Hislon zvicerane?",
                 "Ato janë të markuara si zvicerane. Ajo që mund t’ju themi me siguri nga vetë orët është se përdorin xhama safiri, se dizajni dhe finitura janë të orientuara nga veshja, dhe se janë orët më të rafinuara që mbajmë mes €{lo} dhe €{hi}."),
                ("Pse Hislon kushton më shumë se markat tuaja të tjera?",
                 "Paguani kategorinë e veshjes dhe finiturën, jo një lëvizje më të mirë. Ciferblatët sedefi, treguesit prej kristali, treguesit e aplikuar dhe byzylykët e lëmuar kushtojnë më shumë për t’u prodhuar. Një Hislon €{lo} dhe një orë më e lirë nga ne përdorin të dyja lëvizje kuarci dhe kanë të njëjtën garanci 1-vjeçare."),
                ("A është Hislon një dhuratë e mirë dasme apo diplomimi?",
                 "Është gama që shesim më shpesh si dhuratë. Dizajnet e veshjes i përshtaten një rasti formal, xhami safir e mban si të re, dhe mund t’ju tregojmë {n} modele krah për krah në Durrës para se të vendosni."),
            ],
        },
    },

    "philippe-lauren": {
        "en": {
            "paras": [
                "Philippe Lauren is our chronograph line: {n} models in Durrës from €{lo} to €{hi}. The range runs from all-black ion-plated steel to polished steel and gold-tone dress pieces, for men and women.",
                "Most of the line is built around a chronograph layout, with three sub-dials and pushers on the case side, plus a date window. The cases and bracelets are stainless steel, with black ion plating on the darker models, and there is a square cushion case in the range for anyone who wants something other than a round watch.",
                "These are among the sharpest looking watches we sell for the money. Every one comes with our 1-year guarantee, cash on delivery across Albania.",
            ],
            "faq": [
                ("What kind of watches is Philippe Lauren?",
                 "It is the chronograph line we stock: {n} models from €{lo} to €{hi}, mostly three-counter chronograph layouts with a date window, in stainless steel and black ion-plated steel, plus a gold-tone dress model."),
                ("How much does a Philippe Lauren watch cost in Albania?",
                 "Our Philippe Lauren models run from €{lo} to €{hi}, which is roughly {lolek} to {hilek} Lek. That includes a 1-year guarantee, and cash on delivery anywhere in Albania."),
                ("Where can I see Philippe Lauren watches in person?",
                 "At our workshop on Rruga Aleksander Goga in Durrës, open Monday to Saturday 8:30 to 20:30. We have {n} models in stock and you are welcome to try them on before you buy."),
            ],
        },
        "it": {
            "paras": [
                "Philippe Lauren è la nostra linea di cronografi: {n} modelli a Durazzo da €{lo} a €{hi}. La gamma va dall’acciaio placcato nero total black all’acciaio lucido e ai pezzi da abito color oro, per uomo e donna.",
                "Gran parte della linea è costruita attorno a un layout cronografico, con tre contatori e pulsanti sul lato della cassa, più una finestrella data. Casse e bracciali sono in acciaio inossidabile, con placcatura nera sui modelli più scuri, e nella gamma c’è una cassa quadrata a cuscino per chi vuole qualcosa di diverso da un orologio rotondo.",
                "Sono tra gli orologi più belli che vendiamo per la cifra. Ognuno ha la nostra garanzia di 1 anno, con pagamento alla consegna in tutta l’Albania.",
            ],
            "faq": [
                ("Che tipo di orologi è Philippe Lauren?",
                 "È la linea di cronografi che teniamo: {n} modelli da €{lo} a €{hi}, in gran parte con layout cronografico a tre contatori e finestrella data, in acciaio inossidabile e acciaio placcato nero, più un modello da abito color oro."),
                ("Quanto costa un orologio Philippe Lauren in Albania?",
                 "I nostri modelli Philippe Lauren vanno da €{lo} a €{hi}, che sono circa {lolek} a {hilek} Lek. Sono inclusi la garanzia di 1 anno e il pagamento alla consegna in tutta l’Albania."),
                ("Dove posso vedere gli orologi Philippe Lauren di persona?",
                 "Nel nostro laboratorio in Rruga Aleksander Goga a Durazzo, aperto dal lunedì al sabato dalle 8:30 alle 20:30. Abbiamo {n} modelli disponibili e potete provarli prima di acquistare."),
            ],
        },
        "sq": {
            "paras": [
                "Philippe Lauren është linja jonë e kronografëve: {n} modele në Durrës nga €{lo} deri €{hi}. Gama shkon nga çeliku i veshur me jon të zi tërësisht i zi te çeliku i lëmuar dhe copat e veshjes në ngjyrë ari, për burra dhe gra.",
                "Pjesa më e madhe e linjës është ndërtuar rreth një skeme kronografi, me tre nën-ciferblatë dhe butona në anën e kasës, plus një dritare date. Kasat dhe byzylykët janë çelik inoks, me veshje të zezë në modelet më të errëta, dhe në gamë ka një kasë katrore në formë jastëku për ata që duan diçka tjetër nga një orë e rrumbullakët.",
                "Këto janë ndër orët më të bukura që shesim për paratë. Secila vjen me garancinë tonë 1-vjeçare, me pagesë në dorëzim kudo në Shqipëri.",
            ],
            "faq": [
                ("Çfarë lloj orësh është Philippe Lauren?",
                 "Është linja e kronografëve që mbajmë: {n} modele nga €{lo} deri €{hi}, kryesisht me skema kronografi me tre nën-ciferblatë dhe dritare date, në çelik inoks dhe çelik të veshur me jon të zi, plus një model veshjeje në ngjyrë ari."),
                ("Sa kushton një orë Philippe Lauren në Shqipëri?",
                 "Modelet tona Philippe Lauren shkojnë nga €{lo} deri €{hi}, që janë afërsisht {lolek} deri {hilek} Lekë. Kjo përfshin një garanci 1-vjeçare dhe pagesë në dorëzim kudo në Shqipëri."),
                ("Ku mund t’i shoh orët Philippe Lauren nga afër?",
                 "Në punishten tonë në Rrugën Aleksander Goga në Durrës, e hapur nga e hëna në të shtunë 8:30 deri 20:30. Kemi {n} modele në gjendje dhe jeni të mirëseardhur t’i provoni para se të blini."),
            ],
        },
    },
    "bigotti": {
        "en": {
            "paras": [
                "Bigotti is our square and dress line: {n} models in Durrës from €{lo} to €{hi}. Most of what we keep is women's dress watches, with one multifunction in the range for a larger wrist.",
                "The two square models have a crystal-set bezel on all four sides, one in polished steel with a silver sunburst dial and one in gold-tone with a glossy black one, both on a five-link bracelet with no date window. Alongside them sit a slim round gold-tone piece and a steel multifunction with a day-date display. The set stones are crystals, not diamonds, and we would rather say so than let you assume otherwise.",
                "Water resistance is not stated on these models, so ask us before you take one near water and we will tell you what we know. Every one comes with our 1-year guarantee, cash on delivery across Albania.",
            ],
            "faq": [
                ("What kind of watches is Bigotti?",
                 "It is the square and dress line we stock: {n} models from €{lo} to €{hi}, mostly women's dress watches in stainless steel and gold-tone, two of them with a crystal-set bezel on a square case, plus a steel multifunction with a day-date display."),
                ("How much does a Bigotti watch cost in Albania?",
                 "Our Bigotti models run from €{lo} to €{hi}, which is roughly {lolek} to {hilek} Lek. That includes a 1-year guarantee, and cash on delivery anywhere in Albania."),
                ("Where can I see Bigotti watches in person?",
                 "At our workshop on Rruga Aleksander Goga in Durrës, open Monday to Saturday 8:30 to 20:30. We have {n} models in stock and you are welcome to try them on before you buy."),
            ],
        },
        "it": {
            "paras": [
                "Bigotti è la nostra linea quadrata e da abito: {n} modelli a Durazzo da €{lo} a €{hi}. Gran parte di ciò che teniamo sono orologi da donna, con un multifunzione nella gamma per un polso più grande.",
                "I due modelli quadrati hanno una lunetta con cristalli su tutti e quattro i lati, uno in acciaio lucido con quadrante argentato sunburst e uno color oro con quadrante nero lucido, entrambi su bracciale a cinque maglie e senza finestrella data. Accanto a loro ci sono un pezzo rotondo sottile color oro e un multifunzione in acciaio con display giorno-data. Le pietre applicate sono cristalli, non diamanti, e preferiamo dirlo piuttosto che lasciarvelo supporre.",
                "L'impermeabilità non è dichiarata su questi modelli, quindi chiedeteci prima di avvicinarne uno all'acqua e vi diremo quello che sappiamo. Ognuno ha la nostra garanzia di 1 anno, con pagamento alla consegna in tutta l'Albania.",
            ],
            "faq": [
                ("Che tipo di orologi è Bigotti?",
                 "È la linea quadrata e da abito che teniamo: {n} modelli da €{lo} a €{hi}, in gran parte orologi da donna in acciaio inossidabile e color oro, due con lunetta con cristalli su cassa quadrata, più un multifunzione in acciaio con display giorno-data."),
                ("Quanto costa un orologio Bigotti in Albania?",
                 "I nostri modelli Bigotti vanno da €{lo} a €{hi}, che sono circa {lolek} a {hilek} Lek. Sono inclusi la garanzia di 1 anno e il pagamento alla consegna in tutta l'Albania."),
                ("Dove posso vedere gli orologi Bigotti di persona?",
                 "Nel nostro laboratorio in Rruga Aleksander Goga a Durazzo, aperto dal lunedì al sabato dalle 8:30 alle 20:30. Abbiamo {n} modelli disponibili e potete provarli prima di acquistare."),
            ],
        },
        "sq": {
            "paras": [
                "Bigotti është linja jonë katrore dhe e veshjes: {n} modele në Durrës nga €{lo} deri €{hi}. Pjesa më e madhe e asaj që mbajmë janë orë veshjeje për femra, me një multifunksion në gamë për një dorë më të madhe.",
                "Dy modelet katrore kanë lunetë me kristale në të katër anët, njëri në çelik të lëmuar me ciferblat argjendi sunburst dhe tjetri në ngjyrë ari me ciferblat të zi të shndritshëm, të dyja me byzylyk me pesë hallka dhe pa dritare date. Pranë tyre janë një copë e rrumbullakët e hollë në ngjyrë ari dhe një multifunksion çeliku me tregues dite-date. Gurët e vendosur janë kristale, jo diamante, dhe preferojmë ta themi sesa t'ju lëmë ta merrni me mend.",
                "Rezistenca ndaj ujit nuk është e deklaruar te këto modele, ndaj na pyesni para se ta afroni njërën te uji dhe ju themi çfarë dimë. Secila vjen me garancinë tonë 1-vjeçare, me pagesë në dorëzim kudo në Shqipëri.",
            ],
            "faq": [
                ("Çfarë lloj orësh është Bigotti?",
                 "Është linja katrore dhe e veshjes që mbajmë: {n} modele nga €{lo} deri €{hi}, kryesisht orë veshjeje për femra në çelik inoks dhe ngjyrë ari, dy prej tyre me lunetë me kristale mbi kasë katrore, plus një multifunksion çeliku me tregues dite-date."),
                ("Sa kushton një orë Bigotti në Shqipëri?",
                 "Modelet tona Bigotti shkojnë nga €{lo} deri €{hi}, që janë afërsisht {lolek} deri {hilek} Lekë. Kjo përfshin një garanci 1-vjeçare dhe pagesë në dorëzim kudo në Shqipëri."),
                ("Ku mund t'i shoh orët Bigotti nga afër?",
                 "Në punishten tonë në Rrugën Aleksander Goga në Durrës, e hapur nga e hëna në të shtunë 8:30 deri 20:30. Kemi {n} modele në gjendje dhe jeni të mirëseardhur t'i provoni para se të blini."),
            ],
        },
    },
}
