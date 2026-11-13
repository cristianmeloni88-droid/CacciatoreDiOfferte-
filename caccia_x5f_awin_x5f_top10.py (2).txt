"""
SHARDAN - CACCIA AWIN V1 - Usa davvero la chiave API Awin
Publisher ID 3154361 - Temu, AliExpress, MediaWorld, Decathlon, Conrad
Usa API Awin: GET https://api.awin.com/publishers/{id}/catalogue
Se Awin non risponde, lo dice chiaro e non inventa prezzi.
"""
import os, requests, csv, json

PUBLISHER_ID = os.environ.get("AWIN_PUBLISHER_ID", "3154361")
API_KEY = os.environ.get("AWIN_API_KEY", "")
print(f"=== SHARDAN Caccia Awin V1 - Publisher {PUBLISHER_ID} ===")
if not API_KEY:
    print("ERRORE: AWIN_API_KEY non trovata nei Secrets di GitHub")
    print("Vai su Settings -> Secrets -> Actions e metti AWIN_API_KEY e AWIN_PUBLISHER_ID")
    raise SystemExit(0)

HEADERS = {"Authorization": f"Bearer {API_KEY}", "Accept": "application/json", "User-Agent": "CacciatoreDiOfferte/1.0"}

# ID Awin dei 5 negozi - da verificare in dashboard, se uno non c'e lo salta
# Temu IT 118233, gli altri li cerchiamo per nome via API programmes
WANTED = ["temu", "aliexpress", "mediaworld", "decathlon", "conrad"]

def get_programmes():
    url = f"https://api.awin.com/publishers/{PUBLISHER_ID}/programmes?relationship=joined&limit=100"
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        print(f"Programmes status {r.status_code}")
        if r.status_code != 200:
            print(f"Risposta programmes: {r.text[:500]}")
            return []
        data = r.json()
        progs = data if isinstance(data, list) else data.get("data", data.get("programmes", []))
        print(f"Trovati {len(progs)} programmi joined")
        for p in progs[:20]:
            name = p.get("name", p.get("advertiser", {}).get("name", "?"))
            aid = p.get("id", p.get("advertiserId", "?"))
            print(f"  - {name} ID {aid}")
        return progs
    except Exception as e:
        print(f"Errore programmes: {e}")
        return []

def get_products_for_advertiser(adv_id, adv_name):
    # Catalogue API Awin - cerca prodotti di quell'advertiser
    url = f"https://api.awin.com/publishers/{PUBLISHER_ID}/catalogue"
    params = {"advertiserIds": adv_id, "limit": 50, "sort": "price_asc"}
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=30)
        print(f"Catalogue {adv_name} status {r.status_code}")
        if r.status_code != 200:
            print(f"  Risposta: {r.text[:400]}")
            return []
        data = r.json()
        items = data if isinstance(data, list) else data.get("data", data.get("products", []))
        print(f"  {adv_name}: {len(items)} prodotti da Awin")
        out = []
        for it in items[:15]:
            nome = it.get("productName", it.get("name", "")) or ""
            prezzo = it.get("salePrice", it.get("price", {}))
            if isinstance(prezzo, dict): prezzo = prezzo.get("amount", prezzo.get("value", 0))
            vecchio = it.get("rrp", it.get("originalPrice", {}))
            if isinstance(vecchio, dict): vecchio = vecchio.get("amount", vecchio.get("value", ""))
            img = it.get("imageUrl", it.get("image", "")) or ""
            link = it.get("awDeepLink", it.get("deepLink", it.get("url", ""))) or ""
            if not nome or not prezzo: continue
            try: prezzo = float(prezzo)
            except: continue
            try: vecchio_f = float(vecchio) if vecchio else ""
            except: vecchio_f = ""
            sconto = ""
            if vecchio_f and float(vecchio_f) > prezzo:
                sconto = round((1 - prezzo/float(vecchio_f))*100, 1)
            out.append({"nome": str(nome)[:150], "prezzo": prezzo, "vecchio": vecchio_f, "sconto": sconto, "link": link, "img": img, "store": adv_name, "asin": ""})
        return out
    except Exception as e:
        print(f"  Errore catalogue {adv_name}: {e}")
        return []

def main():
    progs = get_programmes()
    # Filtra solo i 5 che vogliamo
    scelti = []
    for p in progs:
        name = (p.get("name", "") or p.get("advertiser", {}).get("name", "")).lower()
        aid = p.get("id", p.get("advertiserId", p.get("advertiser", {}).get("id", "")))
        for w in WANTED:
            if w in name:
                scelti.append((aid, p.get("name", name)))
                break
    print(f"Scelti per Top10: {scelti}")
    if not scelti:
        print("Nessuno dei 5 negozi risulta JOINED su Awin.")
        print("Vai su Awin -> Advertiser -> I miei programmi e controlla se sono In attesa / Pending.")
        print("Se sono Pending, aspetta l'approvazione del negozio, Awin ti ha approvato ma il negozio deve ancora approvare te.")
        # Salva file vuoto cosi workflow non si blocca
        with open("top10_awin.csv","w",newline="",encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["nome","prezzo","vecchio","sconto","link","img","store","asin"]); w.writeheader()
        return
    tutti = []
    for aid, aname in scelti:
        tutti.extend(get_products_for_advertiser(aid, aname))
    # Ordina per sconto e salva Top10
    tutti.sort(key=lambda x: (float(x["sconto"] or 0)), reverse=True)
    top10 = tutti[:10]
    print(f"=== AWIN TOTALE {len(tutti)} - TOP10 {len(top10)} ===")
    for p in top10: print(f"  - {p['store']} | {p['nome'][:60]} | {p['prezzo']}€")
    with open("top10_awin.csv","w",newline="",encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["nome","prezzo","vecchio","sconto","link","img","store","asin"]); w.writeheader()
        for p in top10: w.writerow(p)
    print("Salvato top10_awin.csv")

if __name__ == "__main__":
    main()
