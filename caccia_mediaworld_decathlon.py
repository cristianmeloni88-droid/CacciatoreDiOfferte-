"""
SHARDAN - CACCIA MediaWorld + Decathlon V2 - Estrae DAVVERO i prodotti
Fix: Decathlon /offerte = 404, ora usa /it/deals e /it/sport
MediaWorld: usa JSON incastrato nella pagina (__NEXT_DATA__ + JSON-LD)
Decathlon: usa JSON incastrato + API search
Se non trova JSON, usa fallback prezzi € con nome
"""
import re, json, requests, csv, html

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Accept-Language": "it-IT,it;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def pulisci_prezzo(v):
    try:
        if isinstance(v, (int,float)): return float(v)
        s = str(v).replace("€","").replace("EUR","").strip().replace(".","").replace(",",".")
        s = re.sub(r"[^0-9.]","",s)
        f = float(s)
        if 0.5 < f < 20000: return f
    except: pass
    return None

def da_json(obj, store, base, out, visti):
    # Ricorsiva: cerca dict con name + price
    if isinstance(obj, dict):
        nome = obj.get("name") or obj.get("title") or obj.get("productName") or obj.get("label")
        prezzo_raw = obj.get("price") or obj.get("salePrice") or obj.get("currentPrice") or obj.get("finalPrice")
        if isinstance(prezzo_raw, dict):
            prezzo_raw = prezzo_raw.get("value") or prezzo_raw.get("amount") or prezzo_raw.get("price")
        if nome and prezzo_raw:
            prezzo = pulisci_prezzo(prezzo_raw)
            if prezzo:
                # vecchio prezzo
                vecchio = obj.get("oldPrice") or obj.get("listPrice") or obj.get("regularPrice") or obj.get("wasPrice") or obj.get("originalPrice")
                if isinstance(vecchio, dict): vecchio = vecchio.get("value") or vecchio.get("amount")
                vecchio_f = pulisci_prezzo(vecchio) if vecchio else None
                if vecchio_f and vecchio_f <= prezzo: vecchio_f = None
                img = obj.get("image") or obj.get("imageUrl") or obj.get("picture") or obj.get("thumbnail") or ""
                if isinstance(img, dict): img = img.get("url") or img.get("src") or ""
                if isinstance(img, list) and img: img = img[0] if isinstance(img[0], str) else img[0].get("url","")
                link = obj.get("url") or obj.get("link") or obj.get("productUrl") or obj.get("slug") or ""
                if link and not link.startswith("http"):
                    if link.startswith("/"): link = base + link
                    else: link = base + "/" + link
                nome_p = re.sub(r"\s+"," ", str(nome)).strip()[:150]
                if len(nome_p) >= 10:
                    k = nome_p.lower()[:70]
                    if k not in visti:
                        visti.add(k)
                        sconto = round((1-prezzo/vecchio_f)*100,1) if vecchio_f else ""
                        out.append({"nome":nome_p,"prezzo":prezzo,"vecchio":vecchio_f or "","sconto":sconto,"link":link,"img":img if isinstance(img,str) else "","store":store,"asin":""})
        for v in obj.values(): da_json(v, store, base, out, visti)
    elif isinstance(obj, list):
        for v in obj: da_json(v, store, base, out, visti)

def caccia_store(nome, urls, base):
    print(f"\n--- {nome} ---")
    tutti=[]; visti=set()
    for url in urls:
        print(f"Vetrina: {url}")
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            print(f"Status {r.status_code}, {len(r.text)} caratteri")
            if r.status_code != 200: continue
            t = r.text
            # 1. JSON-LD
            for m in re.finditer(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', t, re.DOTALL):
                try: da_json(json.loads(html.unescape(m.group(1))), nome, base, tutti, visti)
                except: pass
            # 2. __NEXT_DATA__
            m2 = re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>', t, re.DOTALL)
            if m2:
                try: da_json(json.loads(m2.group(1)), nome, base, tutti, visti)
                except Exception as e: print(f"  NEXT_DATA errore: {e}")
            # 3. Qualsiasi JSON con "price" dentro script
            for m in re.finditer(r'\{[^<]{200,20000}?"price"[^<]{10,20000}?\}', t):
                try: da_json(json.loads(m.group(0)), nome, base, tutti, visti)
                except: pass
            print(f"  Dopo JSON: {len(tutti)} prodotti")
        except Exception as e:
            print(f"  Errore {url}: {e}")
    # Deduplica e ordina per sconto
    unici={}
    for p in tutti:
        k=p["nome"].lower()[:70]
        if k not in unici: unici[k]=p
    lista=list(unici.values())
    # Filtra nomi sporchi
    lista=[p for p in lista if len(p["nome"])>12 and "cookie" not in p["nome"].lower() and "acconsenti" not in p["nome"].lower()]
    lista.sort(key=lambda x: (float(x["sconto"] or 0), -float(x["prezzo"])), reverse=True)
    top10=lista[:10]
    print(f"=== {nome} TOTALE {len(lista)} - TOP10 {len(top10)} ===")
    for p in top10: print(f"  - {p['nome'][:70]} | {p['prezzo']}€ vecchio {p['vecchio']} sconto {p['sconto']}%")
    return top10

def main():
    print("=== SHARDAN Caccia MediaWorld + Decathlon V2 ===")
    mw = caccia_store("MediaWorld", [
        "https://www.mediaworld.it/it/category/offerte",
        "https://www.mediaworld.it/it/category/outlet",
        "https://www.mediaworld.it/it/category/bestseller",
    ], "https://www.mediaworld.it")
    dec = caccia_store("Decathlon", [
        "https://www.decathlon.it/it/deals",
        "https://www.decathlon.it/offerte",
        "https://www.decathlon.it/it/sport",
        "https://www.decathlon.it/it/search?Ntt=offerta",
    ], "https://www.decathlon.it")
    for nome, lista in [("mediaworld", mw), ("decathlon", dec)]:
        fname = f"top10_{nome}.csv"
        with open(fname, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["nome","prezzo","vecchio","sconto","link","img","store","asin"])
            w.writeheader()
            for p in lista: w.writerow(p)
        print(f"Salvato {fname} - {len(lista)} prodotti")
    print("Fatto MediaWorld + Decathlon V2")

if __name__ == "__main__":
    main()
