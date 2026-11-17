"""
SHARDAN - Caccia per SINGOLO negozio - Voghion / Thun / Bazta
Uso: python caccia_store.py voghion  -> crea top10_voghion.csv
Uso: python caccia_store.py thun     -> crea top10_thun.csv
Uso: python caccia_store.py bazta    -> crea top10_bazta.csv
Usa API Awin, prende i 10 prodotti con sconto più alto di QUEL negozio.
"""
import os, sys, csv, requests

PUB = os.environ.get("AWIN_PUBLISHER_ID","3154361").strip()
TOKEN = os.environ.get("AWIN_API_KEY","").strip()
HEAD = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"}
STORE = (sys.argv[1] if len(sys.argv)>1 else "voghion").lower().strip()

def pulisci(v):
    try:
        f=float(str(v).replace("€","").replace(",",".").strip())
        return f if 0.3 < f < 10000 else None
    except: return None

def main():
    print(f"=== Caccia SINGOLO negozio: {STORE} ===")
    if not TOKEN:
        print("Manca AWIN_API_KEY"); return
    # Trova il negozio JOINED
    r = requests.get(f"https://api.awin.com/publishers/{PUB}/programmes?relationship=joined&limit=100", headers=HEAD, timeout=30)
    progs = r.json() if r.status_code==200 else []
    progs = progs if isinstance(progs, list) else progs.get("programmes", progs.get("data", []))
    target = None
    for p in progs:
        adv = p.get("advertiser", {}) if isinstance(p, dict) else {}
        name = (adv.get("name") or "").lower()
        if STORE in name:
            target = (adv.get("id"), adv.get("name"))
            break
    if not target:
        print(f"Negozio {STORE} NON trovato tra i JOINED - forse non ancora approvato!")
        return
    adv_id, adv_name = target
    print(f"Trovato: {adv_name} ID {adv_id}")
    r2 = requests.get(f"https://api.awin.com/publishers/{PUB}/products?advertiser={adv_id}&limit=100&sort=discount_desc", headers=HEAD, timeout=30)
    data = r2.json() if r2.status_code==200 else {}
    prods = data if isinstance(data, list) else data.get("products", data.get("data", []))
    print(f"Prodotti: {len(prods)}")
    out=[]
    for p in prods:
        nome = p.get("productName") or p.get("name") or ""
        prezzo = pulisci(p.get("salePrice", {}).get("amount") if isinstance(p.get("salePrice"), dict) else p.get("salePrice") or p.get("price"))
        vecchio = pulisci(p.get("retailPrice", {}).get("amount") if isinstance(p.get("retailPrice"), dict) else p.get("retailPrice") or p.get("wasPrice") or p.get("rrp"))
        if not nome or not prezzo: continue
        if vecchio and vecchio <= prezzo: vecchio=None
        sconto = round((1-prezzo/vecchio)*100,1) if vecchio else ""
        img = p.get("imageUrl") or p.get("image") or ""
        if isinstance(img, dict): img = img.get("url","")
        link = p.get("awDeepLink") or p.get("merchantDeepLink") or p.get("url") or ""
        out.append({"nome": str(nome)[:150], "prezzo": prezzo, "vecchio": vecchio or "", "sconto": sconto, "link": link, "img": img, "store": adv_name, "asin": "", "stelle": "4.5"})
    out.sort(key=lambda x: float(x["sconto"] or 0), reverse=True)
    top = out[:10]
    fn = f"top10_{STORE}.csv"
    with open(fn,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=["nome","prezzo","vecchio","sconto","link","img","store","asin","stelle"]); w.writeheader()
        for p in top: w.writerow(p)
    print(f"Salvato {fn} - {len(top)} prodotti")
    for p in top: print(f"  - {p['nome'][:60]} | {p['prezzo']}€ sconto {p['sconto']}%")

if __name__=="__main__": main()
