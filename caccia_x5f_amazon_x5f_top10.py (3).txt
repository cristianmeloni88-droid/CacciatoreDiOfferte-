"""
SHARDAN Amazon Top 10 - FIX V3 SENZA bs4
Usa SOLO requests + re (che hai gia), niente BeautifulSoup.
Cosi non da piu ModuleNotFoundError.
"""
import re, requests, csv

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Accept-Language": "it-IT,it;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

VETRINE = [
    ("deals", "https://www.amazon.it/deals"),
    ("bestsellers", "https://www.amazon.it/gp/bestsellers"),
    ("movers", "https://www.amazon.it/gp/movers-and-shakers"),
]

def pulisci_prezzo(testo):
    if not testo: return None
    testo = testo.replace("€","").replace("EUR","").replace("&euro;","").strip()
    testo = testo.replace(".","").replace(",",".")
    testo = re.sub(r"[^0-9.]", "", testo)
    try:
        v = float(testo)
        if 0.5 < v < 10000: return v
    except: pass
    return None

def estrai(html):
    trovati = []
    visti = set()
    # Split per ogni card data-asin="B0..."
    # Ogni card finisce alla prossima data-asin
    parti = re.split(r'data-asin="([A-Z0-9]{10})"', html)
    # parti = [prima, asin1, blocco1, asin2, blocco2, ...]
    for i in range(1, len(parti)-1, 2):
        asin = parti[i]
        blocco = parti[i+1][:8000]  # solo i primi 8000 caratteri della card, per non prendere la card dopo
        if asin in visti: continue
        # NOME V4: salta le stelle, prendi il vero titolo prodotto
        # Amazon mette prima "4,5 su 5 stelle" - quello NON e un nome, va scartato
        nome = ""
        # 1) Cerca tutti gli alt e gli span lunghi, prendi il primo che NON e stelle/prezzo
        candidati = []
        for m in re.finditer(r'alt="([^"]{10,200})"', blocco):
            candidati.append(m.group(1).strip())
        for m in re.finditer(r'<span[^>]*>([^<]{15,200})</span>', blocco):
            candidati.append(m.group(1).strip())
        for c in candidati:
            cl = c.lower()
            if "su 5 stelle" in cl: continue
            if "stelle" in cl and len(c) < 30: continue
            if "recension" in cl: continue
            if re.match(r'^[0-9,\.\s€]+$', c): continue
            if "€" in c and len(c) < 25: continue
            if len(c) >= 15:
                nome = c
                break
        if not nome or len(nome) < 12: continue
        if "a-price" not in blocco and "a-offscreen" not in blocco: continue
        # PREZZO: cerca a-price-whole + fraction, oppure a-offscreen con €
        prezzo = None
        m_whole = re.search(r'a-price-whole[^>]*>([^<]+)</span>.*?a-price-fraction[^>]*>([^<]+)</span>', blocco, re.DOTALL)
        if m_whole:
            prezzo = pulisci_prezzo(m_whole.group(1) + "." + m_whole.group(2))
        if not prezzo:
            m_off = re.search(r'a-offscreen[^>]*>([^<]*?\d[\d\.,]*\s*€?[^<]*?)</span>', blocco)
            if m_off: prezzo = pulisci_prezzo(m_off.group(1))
        if not prezzo:
            # ultimo tentativo: primo prezzo € nel blocco
            m_euro = re.search(r'(\d{1,3}[\.,]\d{2})\s*€', blocco)
            if m_euro: prezzo = pulisci_prezzo(m_euro.group(1))
        # VECCHIO PREZZO: a-text-price
        vecchio = None
        m_old = re.search(r'a-text-price.*?a-offscreen[^>]*>([^<]+)</span>', blocco, re.DOTALL)
        if m_old: vecchio = pulisci_prezzo(m_old.group(1))
        # LINK
        link = ""
        m_link = re.search(r'href="(/[^"]*?/dp/[^"]*?)"', blocco)
        if m_link: link = "https://www.amazon.it" + m_link.group(1).split("?")[0]
        else:
            m_link2 = re.search(r'href="(/[^"]*?)"', blocco)
            if m_link2 and "/dp/" in m_link2.group(1): link = "https://www.amazon.it" + m_link2.group(1).split("?")[0]
        # IMG
        img = ""
        m_img = re.search(r'<img[^>]+src="([^"]+)"', blocco)
        if m_img: img = m_img.group(1)
        if prezzo:
            visti.add(asin)
            sconto = ""
            try:
                if vecchio and vecchio > prezzo: sconto = round((1 - prezzo/vecchio)*100, 1)
            except: pass
            trovati.append({"nome": nome[:150], "prezzo": prezzo, "vecchio": vecchio or "", "sconto": sconto, "link": link, "img": img, "asin": asin})
    return trovati

def main():
    print("=== SHARDAN Amazon Top 10 - Vetrine Amazon - FIX V4 nome vero - salta stelle ===")
    tutti = []
    for nome_vetrina, url in VETRINE:
        print(f"\n--- Amazon vetrina: {nome_vetrina} -> {url} ---")
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            print(f"Status: {r.status_code}, {len(r.text)} caratteri")
            if "Robot Check" in r.text or "Enter the characters" in r.text:
                print("⚠️ Amazon Robot Check - vetrina saltata")
                continue
            prodotti = estrai(r.text)
            print(f"Trovati {len(prodotti)} prodotti con prezzo letto in questa vetrina")
            for p in prodotti[:3]:
                print(f"  - {p['nome'][:60]} | {p['prezzo']} | vecchio {p['vecchio']} | {p['link'][:70]}")
            for p in prodotti:
                p["vetrina"] = nome_vetrina
                tutti.append(p)
        except Exception as e:
            print(f"Errore vetrina {nome_vetrina}: {e}")
    # Deduplica
    unici = {}
    for p in tutti:
        k = p.get("asin") or p["nome"].lower()[:60]
        if k not in unici: unici[k] = p
    lista = list(unici.values())
    lista.sort(key=lambda x: (float(x["sconto"] or 0), -float(x["prezzo"])), reverse=True)
    top10 = lista[:10]
    print(f"\n=== TOTALE unici: {len(lista)} - TOP10: {len(top10)} ===")
    for i, p in enumerate(top10, 1):
        print(f"{i}. {p['nome'][:70]} - {p['prezzo']}€ vecchio {p['vecchio']} sconto {p['sconto']}%")
    with open("top10_amazon.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["nome","prezzo","vecchio","sconto","link","img","asin","vetrina"])
        w.writeheader()
        for p in top10: w.writerow(p)
    print("Salvato top10_amazon.csv")
    if len(top10) == 0:
        print("⚠️ ANCORA 0: Amazon manda pagina vuota a IP Render. Prossimo passo: prendere prodotti Amazon via Awin API.")

if __name__ == "__main__":
    main()
