"""
SHARDAN - CACCIA MediaWorld + Decathlon - Vetrine Offerte
Stesso sistema di Amazon, ma piu facile: MediaWorld e Decathlon non bloccano.
Vetrine:
- MediaWorld: https://www.mediaworld.it/it/category/offerte + bestseller
- Decathlon: https://www.decathlon.it/offerte + bestseller
Prende: nome, prezzo vero, vecchio prezzo, sconto, foto, link
Se prezzo assurdo, NOMI dopo lo cancella, come per Amazon.
"""
import re, requests, csv

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Accept-Language": "it-IT,it;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def pulisci_prezzo(testo):
    if not testo: return None
    testo = testo.replace("€","").replace("EUR","").replace("&euro;","").strip()
    # Togli punti migliaia, metti punto per decimali
    testo = testo.replace(".","").replace(",",".")
    testo = re.sub(r"[^0-9.]", "", testo)
    try:
        v = float(testo)
        if 0.5 < v < 10000: return v
    except: pass
    return None

def estrai_prodotti(html, base_url, store):
    trovati = []
    visti = set()
    # Cerca tutti i blocchi con prezzo € vicino a un nome
    # Metodo generico: trova tutti i prezzi con € e prendi il testo vicino come nome
    # Per MediaWorld/Decathlon, il prezzo e dentro data-price o <span> con €
    # Cerchiamo pattern: <a href="..."> ... nome ... prezzo ... </a>
    # Semplificato: split per href prodotto
    for m in re.finditer(r'href="([^"]*(?:/product/|/p/|/it/|/prodotto/)[^"]*)"[^>]*>(.*?)</a>', html, re.DOTALL | re.IGNORECASE):
        link_parz = m.group(1)
        blocco = m.group(2)[:4000]
        if len(blocco) < 50: continue
        # Nome: togli tag HTML, prendi testo lungo
        testo_pulito = re.sub(r"<[^>]+>", " ", blocco)
        testo_pulito = re.sub(r"\s+", " ", testo_pulito).strip()
        if len(testo_pulito) < 12: continue
        # Prezzo: cerca 12,99 € o 1299,00 € nel blocco
        prezzi = re.findall(r"(\d{1,4}[\.,]\d{2})\s*€", blocco)
        if not prezzi: continue
        prezzo = pulisci_prezzo(prezzi[0])
        if not prezzo: continue
        # Vecchio prezzo: secondo prezzo se c'e e e piu alto
        vecchio = None
        if len(prezzi) > 1:
            cand = pulisci_prezzo(prezzi[1])
            if cand and cand > prezzo: vecchio = cand
        # Immagine
        img = ""
        m_img = re.search(r'<img[^>]+src="([^"]+)"', blocco)
        if m_img: img = m_img.group(1)
        else:
            m_img2 = re.search(r'data-src="([^"]+)"', blocco)
            if m_img2: img = m_img2.group(1)
        if img.startswith("//"): img = "https:" + img
        if img.startswith("/"): img = base_url + img
        # Link completo
        if link_parz.startswith("http"): link = link_parz
        elif link_parz.startswith("//"): link = "https:" + link_parz
        else: link = base_url + link_parz
        # Nome: prendi primi 120 caratteri, togli prezzi
        nome = re.sub(r"\d{1,4}[\.,]\d{2}\s*€", "", testo_pulito).strip()
        nome = re.sub(r"\s+", " ", nome)[:150]
        if len(nome) < 12: continue
        chiave = nome.lower()[:60]
        if chiave in visti: continue
        visti.add(chiave)
        sconto = ""
        if vecchio and vecchio > prezzo:
            sconto = round((1 - prezzo/vecchio)*100, 1)
        trovati.append({"nome": nome, "prezzo": prezzo, "vecchio": vecchio or "", "sconto": sconto, "link": link, "img": img, "store": store, "asin": ""})
    return trovati

def caccia_store(nome_store, urls, base_url):
    print(f"\n--- {nome_store} ---")
    tutti = []
    for url in urls:
        print(f"Vetrina: {url}")
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            print(f"Status {r.status_code}, {len(r.text)} caratteri")
            if r.status_code != 200:
                print(f"  Salto, status {r.status_code}")
                continue
            prods = estrai_prodotti(r.text, base_url, nome_store)
            print(f"  Trovati {len(prods)} prodotti")
            for p in prods[:2]:
                print(f"    - {p['nome'][:60]} | {p['prezzo']}€ vecchio {p['vecchio']}")
            tutti.extend(prods)
        except Exception as e:
            print(f"  Errore {url}: {e}")
    # Deduplica
    unici = {}
    for p in tutti:
        k = p["nome"].lower()[:60]
        if k not in unici: unici[k] = p
    lista = list(unici.values())
    lista.sort(key=lambda x: (float(x["sconto"] or 0), -float(x["prezzo"])), reverse=True)
    top10 = lista[:10]
    print(f"=== {nome_store} TOTALE {len(lista)} - TOP10 {len(top10)} ===")
    return top10

def main():
    print("=== SHARDAN Caccia MediaWorld + Decathlon ===")
    mw = caccia_store("MediaWorld", [
        "https://www.mediaworld.it/it/category/offerte",
        "https://www.mediaworld.it/it/category/bestseller",
    ], "https://www.mediaworld.it")
    dec = caccia_store("Decathlon", [
        "https://www.decathlon.it/offerte",
        "https://www.decathlon.it/sport",
    ], "https://www.decathlon.it")
    # Salva 2 CSV separati, cosi POST puo postarli negli slot 12:00 e 16:00
    for nome, lista in [("mediaworld", mw), ("decathlon", dec)]:
        fname = f"top10_{nome}.csv"
        with open(fname, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["nome","prezzo","vecchio","sconto","link","img","store","asin"])
            w.writeheader()
            for p in lista: w.writerow(p)
        print(f"Salvato {fname} - {len(lista)} prodotti")
    print("Fatto MediaWorld + Decathlon")

if __name__ == "__main__":
    main()
