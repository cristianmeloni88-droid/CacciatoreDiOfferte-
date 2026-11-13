"""
SHARDAN - Caccia Awin V2 - vede anche PENDING - Publisher 3154361
Usa API Awin ufficiale: niente scraping, niente 403, prezzi veri.
1. GET /publishers/{id}/programmes?relationship=joined -> negozi a cui sei iscritto
2. Per ogni negozio (Temu, AliExpress, MediaWorld, Decathlon, Conrad) -> GET /publishers/{id}/products?advertiser={adv_id}
3. Prende Top10 per sconto, salva top10_awin.csv
Se nessun negozio joined -> scrive 0 righe e dice chiaro che devi aspettare approvazione.
"""
import os, csv, requests

PUB = os.environ.get("AWIN_PUBLISHER_ID","3154361").strip()
TOKEN = os.environ.get("AWIN_API_KEY","").strip()
HEAD = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"}

WANTED = ["temu","aliexpress","mediaworld","decathlon","conrad"]

def pulisci(v):
    try:
        f=float(str(v).replace("€","").replace(",",".").strip())
        return f if 0.3 < f < 10000 else None
    except: return None

def get_programmes_all():
    # Controlla joined + pending + tutti, così capiamo se sei in attesa
    tutti = {}
    for rel in ["joined", "pending", "notjoined"]:
        try:
            r = requests.get(f"https://api.awin.com/publishers/{PUB}/programmes?relationship={rel}&limit=100", headers=HEAD, timeout=30)
            print(f"Programmes {rel} status {r.status_code}")
            if r.status_code == 200:
                d = r.json()
                lst = d if isinstance(d, list) else d.get("programmes", d.get("data", []))
                for p in lst:
                    adv = p.get("advertiser", {}) if isinstance(p, dict) else {}
                    tutti[adv.get("id")] = (adv.get("name"), rel, p.get("id"))
        except Exception as e:
            print(f"Errore programmes {rel}: {e}")
    return tutti

def get_programmes():
    print(f"=== SHARDAN Caccia Awin V2 - Publisher {PUB} ===")
    if not TOKEN:
        print("ERRORE: AWIN_API_KEY mancante nei Secrets")
        return []
    url = f"https://api.awin.com/publishers/{PUB}/programmes?relationship=joined&limit=100"
    try:
        r = requests.get(url, headers=HEAD, timeout=30)
        print(f"Programmes status {r.status_code}")
        if r.status_code != 200:
            print(f"Programmes body: {r.text[:500]}")
            return []
        data = r.json()
        progs = data if isinstance(data, list) else data.get("programmes", data.get("data", []))
        print(f"Trovati {len(progs)} programmi joined")
        for p in progs:
            adv = p.get("advertiser", {}) if isinstance(p, dict) else {}
            print(f"  - JOINED: {adv.get('name')} ID {adv.get('id')} / programme {p.get('id')}")
        return progs
    except Exception as e:
        print(f"Errore programmes: {e}")
        return []

def get_products_for_advertiser(adv_id, adv_name):
    url = f"https://api.awin.com/publishers/{PUB}/products?advertiser={adv_id}&limit=100&sort=discount_desc"
    try:
        r = requests.get(url, headers=HEAD, timeout=30)
        print(f"  {adv_name} products status {r.status_code}")
        if r.status_code != 200:
            print(f"  {adv_name} body: {r.text[:300]}")
            return []
        data = r.json()
        prods = data if isinstance(data, list) else data.get("products", data.get("data", []))
        print(f"  {adv_name}: {len(prods)} prodotti da Awin")
        out=[]
        for p in prods:
            nome = p.get("productName") or p.get("name") or p.get("title") or ""
            prezzo = pulisci(p.get("salePrice", {}).get("amount") if isinstance(p.get("salePrice"), dict) else p.get("salePrice") or p.get("price"))
            vecchio = pulisci(p.get("retailPrice", {}).get("amount") if isinstance(p.get("retailPrice"), dict) else p.get("retailPrice") or p.get("wasPrice") or p.get("rrp"))
            if not nome or not prezzo: continue
            if vecchio and vecchio <= prezzo: vecchio=None
            sconto = round((1-prezzo/vecchio)*100,1) if vecchio else ""
            img = p.get("imageUrl") or p.get("image") or ""
            if isinstance(img, dict): img = img.get("url","")
            link = p.get("awDeepLink") or p.get("merchantDeepLink") or p.get("url") or p.get("productUrl") or ""
            out.append({"nome": str(nome)[:150], "prezzo": prezzo, "vecchio": vecchio or "", "sconto": sconto, "link": link, "img": img, "store": adv_name, "asin": "", "stelle": p.get("rating") or "4.5"})
        return out
    except Exception as e:
        print(f"  {adv_name} errore: {e}")
        return []

def main():
    tutti_stati = get_programmes_all()
    print("=== STATO DEI 5 NEGOZI SU AWIN ===")
    for adv_id, (adv_name, rel, prog_id) in tutti_stati.items():
        if any(w in (adv_name or "").lower() for w in WANTED):
            print(f"  - {adv_name} -> {rel.upper()} (ID {adv_id})")
    progs = get_programmes()
    # Filtra solo i 5 voluti JOINED
    wanted_progs=[]
    for p in progs:
        adv = p.get("advertiser", {}) if isinstance(p, dict) else {}
        name = (adv.get("name") or "").lower()
        if any(w in name for w in WANTED):
            wanted_progs.append((adv.get("id"), adv.get("name"), p.get("id")))
    print(f"Filtrati {len(wanted_progs)} programmi tra i 5 voluti: {[x[1] for x in wanted_progs]}")
    if not wanted_progs:
        print("Nessuno dei 5 negozi risulta JOINED - aspetta l'approvazione del negozio su Awin (Advertiser > Iscriviti ai programmi). Salvo CSV vuoto.")
        with open("top10_awin.csv","w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f, fieldnames=["nome","prezzo","vecchio","sconto","link","img","store","asin","stelle"])
            w.writeheader()
        print("Salvato top10_awin.csv - 0 prodotti")
        return
    tutti=[]
    for adv_id, adv_name, prog_id in wanted_progs:
        tutti.extend(get_products_for_advertiser(adv_id, adv_name))
    # Ordina per sconto desc, poi prezzo
    def keyf(x):
        try: s=float(x["sconto"] or 0)
        except: s=0
        return (s, -float(x["prezzo"]))
    tutti.sort(key=keyf, reverse=True)
    # Deduplica per nome
    visti=set(); top=[]
    for p in tutti:
        k=p["nome"].lower()[:70]
        if k in visti: continue
        visti.add(k); top.append(p)
        if len(top)>=10: break
    print(f"AWIN TOTALE {len(tutti)} - TOP10 {len(top)}")
    for p in top: print(f"  - {p['store']} | {p['nome'][:60]} | {p['prezzo']}€ vecchio {p['vecchio']} sconto {p['sconto']}%")
    with open("top10_awin.csv","w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=["nome","prezzo","vecchio","sconto","link","img","store","asin","stelle"])
        w.writeheader()
        for p in top: w.writerow(p)
    print(f"Salvato top10_awin.csv - {len(top)} prodotti")

if __name__=="__main__": main()
