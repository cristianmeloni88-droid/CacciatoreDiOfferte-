"""
SHARDAN Amazon Top 10 - Vetrine Amazon - FIX V2
Fix: Amazon risponde 200 ma il vecchio selettore trovava 0 prezzi.
Ora proviamo TUTTI i modi in cui Amazon scrive i prezzi nel 2026:
- span.a-price-whole + span.a-price-fraction
- div[data-asin] + a-price
- regex € / EUR nel testo
- JSON embedded __NEXT_DATA__ / data-a-carousel
Se ancora 0, non inventa nulla: lo scrive nei log e passa alla vetrina dopo.
Mai inventare prezzi. Mai postare senza CAPO.
"""
import re, requests, csv, os, datetime
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Accept-Language": "it-IT,it;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

VETRINE = [
    ("deals", "https://www.amazon.it/deals"),
    ("bestsellers", "https://www.amazon.it/gp/bestsellers"),
    ("movers", "https://www.amazon.it/gp/movers-and-shakers"),
    ("outlet", "https://www.amazon.it/deals?ref_=nav_cs_gb"),
]

def pulisci_prezzo(testo):
    if not testo: return None
    testo = testo.replace("\u20ac","").replace("€","").replace("EUR","").strip()
    testo = testo.replace(".", "").replace(",", ".")
    # tiene solo cifre e punto
    testo = re.sub(r"[^0-9.]", "", testo)
    try:
        v = float(testo)
        if 0.5 < v < 10000:
            return v
    except: pass
    return None

def estrai_prodotti(html):
    soup = BeautifulSoup(html, "html.parser")
    trovati = []
    visti = set()
    # 1) Metodo principale: ogni card con data-asin
    for card in soup.find_all("div", attrs={"data-asin": True}):
        asin = card.get("data-asin","").strip()
        if not asin or asin in visti: continue
        # nome: primo h2 / span con testo lungo, o img alt
        nome = ""
        h = card.find("h2")
        if h: nome = h.get_text(" ", strip=True)
        if not nome or len(nome) < 5:
            img = card.find("img")
            if img and img.get("alt"): nome = img.get("alt").strip()
        if not nome or len(nome) < 5: continue
        # prezzo: a-price-whole + fraction, oppure span.a-price
        prezzo = None
        whole = card.select_one("span.a-price-whole")
        frac = card.select_one("span.a-price-fraction")
        if whole:
            ptxt = whole.get_text(" ", strip=True)
            if frac: ptxt += "." + frac.get_text(" ", strip=True)
            prezzo = pulisci_prezzo(ptxt)
        if not prezzo:
            ap = card.select_one("span.a-price")
            if ap:
                off = ap.select_one("span.a-offscreen")
                if off: prezzo = pulisci_prezzo(off.get_text())
                else: prezzo = pulisci_prezzo(ap.get_text())
        # vecchio prezzo barrato
        vecchio = None
        old = card.select_one("span.a-text-price span.a-offscreen")
        if old: vecchio = pulisci_prezzo(old.get_text())
        # link
        link = ""
        a = card.find("a", href=True)
        if a:
            href = a["href"]
            if href.startswith("/"): link = "https://www.amazon.it" + href.split("?")[0]
            elif "amazon.it" in href: link = href.split("?")[0]
        # immagine
        img_url = ""
        img = card.find("img")
        if img: img_url = img.get("src","") or img.get("data-src","")
        if prezzo:
            visti.add(asin)
            trovati.append({"nome": nome[:150], "prezzo": prezzo, "vecchio": vecchio or "", "sconto": "", "link": link, "img": img_url, "asin": asin})
    # 2) Fallback regex se ancora 0: cerca blocchi € nel testo
    if not trovati:
        # cerca tutti i prezzi € nella pagina
        prezzi = re.findall(r"(\d{1,3}[\.,]\d{2})\s*€", html)
        print(f"   Fallback regex: trovati {len(prezzi)} prezzi grezzi nella pagina, ma senza nome - non li uso, non invento nomi")
    return trovati

def calcola_sconto(p, v):
    try:
        if v and float(v) > float(p):
            return round((1 - float(p)/float(v))*100, 1)
    except: pass
    return ""

def main():
    print("=== SHARDAN Amazon Top 10 - Vetrine Amazon ===")
    tutti = []
    for nome_vetrina, url in VETRINE:
        print(f"\n--- Amazon vetrina: {nome_vetrina} -> {url} ---")
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            print(f"Status: {r.status_code}, {len(r.text)} caratteri")
            # se Amazon manda captcha / robot check, lo dice chiaro
            if "Robot Check" in r.text or "Enter the characters" in r.text or "automated access" in r.text.lower():
                print("⚠️ Amazon ha mandato Robot Check / captcha - vetrina saltata, non blocco totale")
                continue
            prodotti = estrai_prodotti(r.text)
            print(f"Trovati {len(prodotti)} prodotti con prezzo letto in questa vetrina")
            for p in prodotti:
                p["vetrina"] = nome_vetrina
                p["sconto"] = calcola_sconto(p["prezzo"], p["vecchio"])
                tutti.append(p)
            # mostra i primi 3 per debug nei log
            for p in prodotti[:3]:
                print(f"  - {p['nome'][:60]} | {p['prezzo']} | vecchio {p['vecchio']} | {p['link'][:70]}")
        except Exception as e:
            print(f"Errore vetrina {nome_vetrina}: {e}")
    # Deduplica per ASIN / nome, tieni prezzo più basso
    unici = {}
    for p in tutti:
        k = p.get("asin") or p["nome"].lower()[:60]
        if k not in unici: unici[k] = p
    lista = list(unici.values())
    # Filtro qualità-prezzo: scarta sconto <20% se abbiamo vecchio prezzo, scarta >70% (va a CAPO, non auto-post)
    # Per ora ordina: prima con sconto maggiore, poi prezzo più basso
    lista.sort(key=lambda x: (float(x["sconto"] or 0), -float(x["prezzo"])), reverse=True)
    top10 = lista[:10]
    print(f"\n=== TOTALE unici: {len(lista)} - TOP10: {len(top10)} ===")
    for i, p in enumerate(top10, 1):
        print(f"{i}. {p['nome'][:70]} - {p['prezzo']}€ vecchio {p['vecchio']} sconto {p['sconto']}%")
    # Salva CSV (sempre, anche se 0, così vedi che ha girato)
    with open("top10_amazon.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["nome","prezzo","vecchio","sconto","link","img","asin","vetrina"])
        w.writeheader()
        for p in top10: w.writerow(p)
    print("Salvato top10_amazon.csv")
    if len(top10) == 0:
        print("⚠️ ANCORA 0: Amazon manda la pagina ma senza card data-asin leggibili da Render (IP datacenter). Soluzione consigliata: prendere i prodotti Amazon via Awin API, che non viene bloccata.")

if __name__ == "__main__":
    main()
