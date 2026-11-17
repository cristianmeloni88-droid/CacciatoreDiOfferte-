"""
SHARDAN - Caccia per SINGOLO negozio - VERSIONE PROMOZIONI (Awin blocca Prodotti per nuovi publisher)
NON usa più /products (sempre 404). Usa /promotions + /vouchers + /creatives + fallback link negozio.
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
def tracking_link(adv_id, adv_name):
    # Link Awin generico che funziona per tutti gli store: awclick con mid=advertiser
    # Se è Voghion usiamo il banner che già conosci e funziona al 100%
    if str(adv_id)=="44635":
        return "https://www.awin1.com/cread.php?s=3618806&v=44635&q=476294&r=3154361"
    return f"https://www.awin1.com/awclick.php?mid={adv_id}&id={PUB}"
def main():
    print(f"=== Caccia SINGOLO negozio: {STORE} ===")
    if not TOKEN:
        print("Manca AWIN_API_KEY"); return
    tutti=[]
    for offset in [0,100,200,300]:
        r=requests.get(f"https://api.awin.com/publishers/{PUB}/programmes?relationship=joined&limit=100&offset={offset}", headers=HEAD, timeout=30)
        if r.status_code!=200:
            print(f"Errore programmes: {r.status_code} {r.text[:300]}"); break
        data=r.json()
        progs=data if isinstance(data,list) else data.get("programmes", data.get("data", []))
        if not progs: break
        tutti.extend(progs)
        if len(progs)<100: break
    print(f"Totale JOINED: {len(tutti)}")
    for p in tutti:
        adv=p.get("advertiser",{}) if isinstance(p,dict) else p
        nome=(adv.get("name") if isinstance(adv,dict) else "") or p.get("name","")
        aid=(adv.get("id") if isinstance(adv,dict) else "") or p.get("id","")
        print(f" - JOINED: {nome} | ID={aid}")
    target=None
    want=pulisci_nome(STORE)
    for p in tutti:
        adv=p.get("advertiser",{}) if isinstance(p,dict) else p
        nome=(adv.get("name") if isinstance(adv,dict) else "") or p.get("name","")
        aid=(adv.get("id") if isinstance(adv,dict) else "") or p.get("id","")
        if pulisci_nome(nome)==want or want in pulisci_nome(nome) or STORE in nome.lower():
            target=(aid, nome); break
    if not target:
        print(f"Negozio {STORE} NON trovato!"); return
    adv_id, adv_name=target
    print(f"Trovato: {adv_name} ID {adv_id}")
    out=[]
    # 1. PROMOZIONI - endpoint giusto Awin
    promo_urls=[
        f"https://api.awin.com/publishers/{PUB}/promotions?advertiser={adv_id}&limit=100",
        f"https://api.awin.com/publishers/{PUB}/promotions?limit=100",
    ]
    for url in promo_urls:
        try:
            r=requests.get(url, headers=HEAD, timeout=30)
            print(f"GET promo {url} -> {r.status_code}")
            if r.status_code!=200:
                print(f"  -> {r.text[:200]}"); continue
            data=r.json()
            lst=data if isinstance(data,list) else data.get("promotions", data.get("data", []))
            # Filtra solo per questo negozio se abbiamo preso tutte
            if "advertiser=" not in url:
                lst2=[]
                for pr in lst:
                    a=pr.get("advertiser",{}) if isinstance(pr.get("advertiser"),dict) else {}
                    if str(a.get("id"))==str(adv_id) or str(pr.get("advertiserId"))==str(adv_id):
                        lst2.append(pr)
                lst=lst2
            print(f"Promozioni per {adv_name}: {len(lst)}")
            for pr in lst:
                nome=pr.get("name") or pr.get("title") or "Offerta"
                desc=pr.get("description") or pr.get("terms") or ""
                link=pr.get("clickThroughUrl") or pr.get("url") or pr.get("trackingLink") or tracking_link(adv_id, adv_name)
                code=pr.get("code") or pr.get("voucherCode") or ""
                titolo=nome
                if code: titolo+=f" - Codice: {code}"
                if desc: titolo+=f" - {desc[:90]}"
                out.append({"nome":titolo[:150],"prezzo":"Offerta","vecchio":"","sconto":"","link":link,"img":pr.get("imageUrl","") or "","store":adv_name,"asin":"","stelle":"4.5"})
            if out: break
        except Exception as e:
            print(f"Promo errore: {e}")
    # 2. VOUCHER / CODICI SCONTO
    if not out:
        print("Promo 0 -> provo Voucher!")
        for url in [f"https://api.awin.com/publishers/{PUB}/vouchers?advertiser={adv_id}&limit=100", f"https://api.awin.com/publishers/{PUB}/vouchers?limit=100"]:
            try:
                r=requests.get(url, headers=HEAD, timeout=30)
                print(f"GET voucher {url} -> {r.status_code}")
                if r.status_code!=200: continue
                data=r.json()
                lst=data if isinstance(data,list) else data.get("vouchers", data.get("data", []))
                print(f"Voucher: {len(lst)}")
                for v in lst[:10]:
                    nome=v.get("name") or v.get("title") or "Codice Sconto"
                    code=v.get("code") or ""
                    link=v.get("clickThroughUrl") or tracking_link(adv_id, adv_name)
                    out.append({"nome":f"{nome} - Codice: {code}"[:150],"prezzo":"Codice","vecchio":"","sconto":"","link":link,"img":"","store":adv_name,"asin":"","stelle":"4.5"})
                if out: break
            except Exception as e:
                print(f"Voucher errore: {e}")
    # 3. FALLBACK - Almeno posta il negozio (così Telegram riceve SEMPRE qualcosa!)
    if not out:
        print("Nessuna promozione/voucher - uso FALLBACK link negozio!")
        link=tracking_link(adv_id, adv_name)
        # Crea 3 offerte generiche ma vere per il negozio, così il bot posta comunque
        for i, titolo in enumerate([f"Nuove Offerte {adv_name} - Scopri gli sconti di oggi!", f"Best Seller {adv_name} - I più venduti!", f"Offerte Lampo {adv_name} - Solo per oggi!"]):
            out.append({"nome":titolo[:150],"prezzo":"Offerta","vecchio":"","sconto":"","link":link,"img":"","store":adv_name,"asin":"","stelle":"4.5"})
    top=out[:10]
    fn=f"top10_{STORE}.csv"
    with open(fn,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=["nome","prezzo","vecchio","sconto","link","img","store","asin","stelle"]); w.writeheader()
        for p in top: w.writerow(p)
    print(f"Salvato {fn} - {len(top)} offerte")
    for p in top: print(f"  - {p['nome'][:80]} | link={p['link'][:60]}")
if __name__=="__main__": main()
