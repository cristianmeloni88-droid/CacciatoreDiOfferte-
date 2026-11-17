"""
SHARDAN - Caccia per SINGOLO negozio - VERSIONE FIX AWIN - Voghion / Thun / Bazta
FIX: Awin ritorna advertiserId/advertiserName, non advertiser dict!
"""
import os, sys, csv, requests, re
PUB=os.environ.get("AWIN_PUBLISHER_ID","3154361").strip()
TOKEN=os.environ.get("AWIN_API_KEY","").strip()
HEAD={"Authorization": "Bearer " + TOKEN, "Accept": "application/json"}
STORE=(sys.argv[1] if len(sys.argv)>1 else "voghion").lower().strip()

def pulisci_nome(s):
    s=(s or "").lower()
    s=re.sub(r"[^a-z0-9]","",s)
    for w in ["spa","srl","srls","ltd","gmbh","global","it","com"]:
        s=s.replace(w,"")
    return s

def get_nome_id(p):
    # Prova TUTTI i formati possibili di Awin
    if not isinstance(p, dict):
        return "", ""
    adv = p.get("advertiser")
    if isinstance(adv, dict):
        nome = adv.get("name") or adv.get("advertiserName") or ""
        nid = adv.get("id") or adv.get("advertiserId") or ""
        if nome or nid:
            return str(nome), str(nid)
    # Formato reale Awin: advertiserName / advertiserId
    nome = p.get("advertiserName") or p.get("advertiser") or p.get("name") or p.get("programmeName") or ""
    nid = p.get("advertiserId") or p.get("advertiser_id") or p.get("id") or p.get("programmeId") or ""
    # Se advertiser è stringa
    if isinstance(p.get("advertiser"), str):
        nome = p.get("advertiser")
    return str(nome), str(nid)

def pulisci(v):
    try:
        f=float(str(v).replace("€","").replace(",",".").strip())
        return f if 0.3 < f < 10000 else None
    except:
        return None

def main():
    print("=== Caccia SINGOLO negozio: " + STORE + " ===")
    if not TOKEN:
        print("Manca AWIN_API_KEY"); return
    tutti=[]
    for offset in [0,100,200,300]:
        r=requests.get("https://api.awin.com/publishers/" + PUB + "/programmes?relationship=joined&limit=100&offset=" + str(offset), headers=HEAD, timeout=30)
        if r.status_code!=200:
            print("Errore programmes offset " + str(offset) + ": " + str(r.status_code) + " " + r.text[:500]); break
        data=r.json()
        progs=data if isinstance(data,list) else data.get("programmes", data.get("data", []))
        if not progs:
            break
        tutti.extend(progs)
        if len(progs)<100:
            break
    print("Totale JOINED: " + str(len(tutti)))
    # Debug: mostra chiavi del primo
    if tutti and isinstance(tutti[0], dict):
        print("Chiavi primo programme: " + str(list(tutti[0].keys())[:10]))
    for p in tutti:
        nome, nid = get_nome_id(p)
        print(" - JOINED: " + str(nome) + " | ID=" + str(nid))
    target=None
    want=pulisci_nome(STORE)
    for p in tutti:
        nome, nid = get_nome_id(p)
        if not nome:
            continue
        pn = pulisci_nome(nome)
        if pn==want or want in pn or pn in want or STORE in nome.lower():
            target=(nid, nome)
            break
    if not target:
        print("Negozio " + STORE + " NON trovato tra i JOINED!")
        return
    adv_id, adv_name = target
    print("Trovato: " + str(adv_name) + " ID " + str(adv_id))
    # Prova products con advertiser + anche con programme
    prods=[]
    for url in ["https://api.awin.com/publishers/" + PUB + "/products?advertiser=" + str(adv_id) + "&limit=100", "https://api.awin.com/publishers/" + PUB + "/products?advertiser=" + str(adv_id) + "&limit=100&sort=discount_desc"]:
        r2=requests.get(url, headers=HEAD, timeout=30)
        print("GET products -> " + str(r2.status_code))
        if r2.status_code==200:
            data=r2.json() if r2.text else {}
            prods=data if isinstance(data,list) else data.get("products", data.get("data", []))
            if prods:
                break
    print("Prodotti: " + str(len(prods)))
    out=[]
    for p in prods:
        if not isinstance(p, dict):
            continue
        nome=p.get("productName") or p.get("name") or p.get("title") or ""
        # Prezzo: prova tutti i formati
        prezzo_raw=None
        sp=p.get("salePrice") or p.get("price") or p.get("sale_price")
        if isinstance(sp, dict):
            prezzo_raw=sp.get("amount") or sp.get("value")
        else:
            prezzo_raw=sp
        vecchio_raw=None
        rp=p.get("retailPrice") or p.get("wasPrice") or p.get("rrp") or p.get("originalPrice")
        if isinstance(rp, dict):
            vecchio_raw=rp.get("amount") or rp.get("value")
        else:
            vecchio_raw=rp
        prezzo=pulisci(prezzo_raw)
        vecchio=pulisci(vecchio_raw)
        if not nome or not prezzo:
            continue
        if vecchio and vecchio<=prezzo:
            vecchio=None
        sconto=round((1-prezzo/vecchio)*100,1) if vecchio else ""
        img=p.get("imageUrl") or p.get("image") or ""
        if isinstance(img, dict):
            img=img.get("url","")
        link=p.get("awDeepLink") or p.get("merchantDeepLink") or p.get("url") or p.get("deeplink") or ""
        out.append({"nome":str(nome)[:150],"prezzo":prezzo,"vecchio":vecchio or "","sconto":sconto,"link":link,"img":img,"store":adv_name,"asin":"","stelle":"4.5"})
    out.sort(key=lambda x: float(x["sconto"] or 0), reverse=True)
    top=out[:10]
    fn="top10_" + STORE + ".csv"
    with open(fn,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=["nome","prezzo","vecchio","sconto","link","img","store","asin","stelle"]); w.writeheader()
        for p in top:
            w.writerow(p)
    print("Salvato " + fn + " - " + str(len(top)) + " prodotti")
    for p in top:
        print("  - " + p["nome"][:60] + " | " + str(p["prezzo"]) + " euro sconto " + str(p["sconto"]) + "%")
if __name__=="__main__":
    main()
