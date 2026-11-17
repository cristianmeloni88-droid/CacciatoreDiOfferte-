"""
SHARDAN - Caccia per SINGOLO negozio - VERSIONE PRODOTTI FIX
Prova TUTTI gli indirizzi Awin per i prodotti + fallback Promozioni
Se i prodotti non ci sono, posta le Promozioni (codici sconto / offerte)
Uso: python caccia_store.py voghion / thun / bazta
"""
import os, sys, csv, requests, re
PUB=os.environ.get("AWIN_PUBLISHER_ID","3154361").strip()
TOKEN=os.environ.get("AWIN_API_KEY","").strip()
HEAD={"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"}
STORE=(sys.argv[1] if len(sys.argv)>1 else "voghion").lower().strip()
def pulisci_nome(s):
    s=(s or "").lower()
    s=re.sub(r"[^a-z0-9]","",s)
    for w in ["spa","srl","srls","ltd","gmbh","global","it","com"]:
        s=s.replace(w,"")
    return s
def pulisci(v):
    try:
        f=float(str(v).replace("€","").replace(",",".").strip())
        return f if 0.3 < f < 10000 else None
    except: return None
def main():
    print(f"=== Caccia SINGOLO negozio: {STORE} ===")
    if not TOKEN:
        print("Manca AWIN_API_KEY"); return
    tutti=[]
    for offset in [0,100,200,300]:
        r=requests.get(f"https://api.awin.com/publishers/{PUB}/programmes?relationship=joined&limit=100&offset={offset}", headers=HEAD, timeout=30)
        if r.status_code!=200:
            print(f"Errore programmes offset {offset}: {r.status_code} {r.text[:300]}"); break
        data=r.json()
        progs=data if isinstance(data,list) else data.get("programmes", data.get("data", []))
        if not progs: break
        tutti.extend(progs)
        if len(progs)<100: break
    print(f"Totale JOINED: {len(tutti)}")
    for p in tutti:
        adv=p.get("advertiser",{}) if isinstance(p,dict) else p
        # Awin a volte mette name diretto, a volte dentro advertiser
        nome=adv.get("name") if isinstance(adv,dict) else ""
        aid=adv.get("id") if isinstance(adv,dict) else ""
        if not nome:
            nome=p.get("name","")
            aid=p.get("id","")
        print(f" - JOINED: {nome} | ID={aid}")
    target=None
    want=pulisci_nome(STORE)
    for p in tutti:
        adv=p.get("advertiser",{}) if isinstance(p,dict) else p
        nome=(adv.get("name") if isinstance(adv,dict) else "") or p.get("name","")
        aid=(adv.get("id") if isinstance(adv,dict) else "") or p.get("id","")
        if pulisci_nome(nome)==want or want in pulisci_nome(nome) or pulisci_nome(nome) in want or STORE in nome.lower():
            target=(aid, nome); break
    if not target:
        print(f"Negozio {STORE} NON trovato!"); return
    adv_id, adv_name=target
    print(f"Trovato: {adv_name} ID {adv_id}")
    # --- PROVA TUTTI GLI INDIRIZZI PRODOTTI ---
    prods=[]
    urls=[
        f"https://api.awin.com/publishers/{PUB}/programmes/{adv_id}/products?limit=100",
        f"https://api.awin.com/publishers/{PUB}/products?advertiser={adv_id}&limit=100",
        f"https://api.awin.com/publishers/{PUB}/products?advertiserId={adv_id}&limit=100",
        f"https://api.awin.com/publishers/{PUB}/products?programme={adv_id}&limit=100",
        f"https://api.awin.com/publishers/{PUB}/programmes/{adv_id}/products",
    ]
    for url in urls:
        try:
            r=requests.get(url, headers=HEAD, timeout=30)
            print(f"GET products {url} -> {r.status_code}")
            if r.status_code==200:
                data=r.json()
                lst=data if isinstance(data,list) else data.get("products", data.get("data", []))
                if lst:
                    prods=lst
                    print(f"✅ Trovati {len(prods)} prodotti con {url}")
                    break
                else:
                    print(f"  -> 200 ma lista vuota, provo prossimo")
            else:
                print(f"  -> {r.text[:200]}")
        except Exception as e:
            print(f"GET errore {url}: {e}")
    print(f"Prodotti: {len(prods)}")
    out=[]
    for p in prods:
        nome=p.get("productName") or p.get("name") or p.get("title") or ""
        prezzo=pulisci(p.get("salePrice",{}).get("amount") if isinstance(p.get("salePrice"),dict) else p.get("salePrice") or p.get("price") or p.get("sale_price"))
        vecchio=pulisci(p.get("retailPrice",{}).get("amount") if isinstance(p.get("retailPrice"),dict) else p.get("retailPrice") or p.get("wasPrice") or p.get("rrp") or p.get("originalPrice"))
        if not nome or not prezzo: continue
        if vecchio and vecchio<=prezzo: vecchio=None
        sconto=round((1-prezzo/vecchio)*100,1) if vecchio else ""
        img=p.get("imageUrl") or p.get("image") or p.get("imageUrlLarge") or ""
        if isinstance(img,dict): img=img.get("url","")
        link=p.get("awDeepLink") or p.get("merchantDeepLink") or p.get("url") or p.get("deepLink") or ""
        out.append({"nome":str(nome)[:150],"prezzo":prezzo,"vecchio":vecchio or "","sconto":sconto,"link":link,"img":img,"store":adv_name,"asin":"","stelle":"4.5"})
    # --- FALLBACK: PROMOZIONI (se prodotti = 0) ---
    if not out:
        print("Prodotti 0 -> provo PROMOZIONI Awin!")
        for url in [f"https://api.awin.com/publishers/{PUB}/promotions?advertiser={adv_id}&limit=100", f"https://api.awin.com/publishers/{PUB}/programmes/{adv_id}/promotions?limit=100"]:
            try:
                r=requests.get(url, headers=HEAD, timeout=30)
                print(f"GET promo {url} -> {r.status_code}")
                if r.status_code!=200: continue
                data=r.json()
                lst=data if isinstance(data,list) else data.get("promotions", data.get("data", []))
                print(f"Promozioni: {len(lst)}")
                for pr in lst[:10]:
                    nome=pr.get("name") or pr.get("title") or "Offerta"
                    desc=pr.get("description") or ""
                    link=pr.get("clickThroughUrl") or pr.get("url") or pr.get("awDeepLink") or ""
                    code=pr.get("code") or pr.get("voucherCode") or ""
                    titolo=f"{nome} {code}".strip()
                    if desc: titolo+=f" - {desc[:80]}"
                    out.append({"nome":titolo[:150],"prezzo":"Offerta","vecchio":"","sconto":"","link":link,"img":pr.get("imageUrl","") or "","store":adv_name,"asin":"","stelle":"4.5"})
                if out: break
            except Exception as e:
                print(f"Promo errore: {e}")
    out.sort(key=lambda x: float(x["sconto"] or 0) if str(x["sconto"]).replace(".","").isdigit() else 0, reverse=True)
    top=out[:10]
    fn=f"top10_{STORE}.csv"
    with open(fn,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=["nome","prezzo","vecchio","sconto","link","img","store","asin","stelle"]); w.writeheader()
        for p in top: w.writerow(p)
    print(f"Salvato {fn} - {len(top)} prodotti")
    for p in top: print(f"  - {p['nome'][:70]} | {p['prezzo']}")
if __name__=="__main__": main()
