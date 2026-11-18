"""
SHARDAN - Caccia - VERSIONE 1 MESSAGGIO PULITO PER NEGOZIO
Awin blocca prodotti/promo/voucher (tutti 404). Quindi 1 solo messaggio bello per negozio, con logo, senza duplicati.
"""
import os, sys, csv, requests, re
PUB=os.environ.get("AWIN_PUBLISHER_ID","3154361").strip()
TOKEN=os.environ.get("AWIN_API_KEY","").strip()
HEAD={"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"}
STORE=(sys.argv[1] if len(sys.argv)>1 else "voghion").lower().strip()
LOGHI={
  "44635": "https://www.google.com/s2/favicons?domain=voghion.com&sz=256",
  "43333": "https://www.google.com/s2/favicons?domain=thun.com&sz=256",
  "128403": "https://www.google.com/s2/favicons?domain=bazta.com&sz=256",
  "12251": "https://logo.clearbit.com/aliexpress.com",
}
DESCR={
  "44635": "Moda, casa, elettronica e tanto altro a prezzi bassi. Spedizione veloce e resi facili!",
  "43333": "Bomboniere, idee regalo e ceramiche Thun per decorare ogni ambiente della tua casa!",
  "128403": "Il tuo online department store: alimentari, prodotti per la casa e offerte ogni giorno!",
  "12251": "Milioni di prodotti a prezzi bassissimi! Elettronica, moda, casa e gadget con spedizione in Italia!",
}
def pulisci_nome(s):
    s=(s or "").lower()
    s=re.sub(r"[^a-z0-9]","",s)
    for w in ["spa","srl","srls","ltd","gmbh","global","it","com"]:
        s=s.replace(w,"")
    return s
def tracking_link(adv_id):
    if str(adv_id)=="44635":
        return "https://www.awin1.com/cread.php?s=3618806&v=44635&q=476294&r=3154361"
    return f"https://www.awin1.com/awclick.php?mid={adv_id}&id={PUB}"
def main():
    print(f"=== Caccia SINGOLO negozio: {STORE} ===")
    tutti=[]
    for offset in [0,100,200,300]:
        r=requests.get(f"https://api.awin.com/publishers/{PUB}/programmes?relationship=joined&limit=100&offset={offset}", headers=HEAD, timeout=30)
        if r.status_code!=200: break
        data=r.json()
        progs=data if isinstance(data,list) else data.get("programmes", data.get("data", []))
        if not progs: break
        tutti.extend(progs)
        if len(progs)<100: break
    print(f"Totale JOINED: {len(tutti)}")
    target=None
    want=pulisci_nome(STORE)
    for p in tutti:
        adv=p.get("advertiser",{}) if isinstance(p,dict) else p
        nome=(adv.get("name") if isinstance(adv,dict) else "") or p.get("name","")
        aid=(adv.get("id") if isinstance(adv,dict) else "") or p.get("id","")
        logo=adv.get("logoUrl") or adv.get("logo") or p.get("logoUrl") or ""
        if pulisci_nome(nome)==want or want in pulisci_nome(nome) or STORE in nome.lower():
            target=(aid, nome, logo); break
    if not target:
        print(f"Negozio {STORE} NON trovato!"); return
    adv_id, adv_name, logo = target
    print(f"Trovato: {adv_name} ID {adv_id} Logo: {logo[:80] if logo else 'nessuno'}")
    # Prova promo/voucher (se Awin li sblocca in futuro) - se no, fallback 1 messaggio
    out=[]
    for url in [f"https://api.awin.com/publishers/{PUB}/promotions?advertiser={adv_id}&limit=100"]:
        try:
            r=requests.get(url, headers=HEAD, timeout=20)
            print(f"GET promo -> {r.status_code}")
            if r.status_code==200:
                data=r.json()
                lst=data if isinstance(data,list) else data.get("promotions", data.get("data", []))
                for pr in lst[:5]:
                    nome=pr.get("name") or "Offerta"
                    link=pr.get("clickThroughUrl") or tracking_link(adv_id)
                    out.append({"nome":nome[:120],"prezzo":"Offerta","vecchio":"","sconto":"","link":link,"img":logo or LOGHI.get(str(adv_id),""),"store":adv_name,"asin":"","stelle":"4.5"})
                if out: break
        except: pass
    if not out:
        print("Promo 0 -> 1 messaggio pulito FALLBACK")
        desc=DESCR.get(str(adv_id),"Scopri le offerte di oggi!")
        link=tracking_link(adv_id)
        img=logo or LOGHI.get(str(adv_id),"")
        out.append({"nome":f"Offerte {adv_name} - {desc}","prezzo":"Offerta","vecchio":"","sconto":"","link":link,"img":img,"store":adv_name,"asin":"","stelle":"4.5"})
    fn=f"top10_{STORE}.csv"
    with open(fn,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=["nome","prezzo","vecchio","sconto","link","img","store","asin","stelle"]); w.writeheader()
        for p in out: w.writerow(p)
    print(f"Salvato {fn} - {len(out)} offerta/e - NIENTE DUPLICATI!")
if __name__=="__main__": main()
