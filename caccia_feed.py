"""
SHARDAN - Caccia da FEED Awin - Offerte VERE con foto e prezzo!
Scarica il Datafeed di Awin (450k prodotti) e prende i 10 con sconto più alto!
Uso: python caccia_feed.py voghion
     python caccia_feed.py thun
     python caccia_feed.py bazta
     python caccia_feed.py aliexpress
Secrets:
 AWIN_FEED_VOGHION, AWIN_FEED_THUN, AWIN_FEED_BAZTA, AWIN_FEED_ALIEXPRESS
"""
import os, sys, csv, requests, gzip, io
STORE=(sys.argv[1] if len(sys.argv)>1 else "voghion").lower().strip()
NOMI={"voghion":"Voghion Global","thun":"Thun IT","bazta":"Bazta IT","aliexpress":"AliExpress IT"}
def pulisci(v):
    try:
        s=str(v).replace("€","").replace("EUR","").replace(",",".").strip()
        # Se ha più punti (es. 1.299.99) tieni solo l'ultimo come decimale
        if s.count(".")>1:
            parti=s.split(".")
            s="".join(parti[:-1])+"."+parti[-1]
        f=float(s)
        return f if 0.3 < f < 10000 else None
    except: return None
def main():
    print(f"=== Caccia FEED Awin: {STORE} ===")
    env=f"AWIN_FEED_{STORE.upper()}"
    url=os.environ.get(env,"").strip()
    if not url:
        print(f"Manca {env} nei Secrets! Metti l'URL del Datafeed!")
        return
    print(f"Scarico feed da Awin... (può metterci 20-40 secondi, sono tanti prodotti!)")
    try:
        r=requests.get(url, timeout=120)
        print(f"Download: {r.status_code} - {len(r.content)} byte")
        if r.status_code!=200:
            print(f"Errore download: {r.text[:300]}"); return
        data=r.content
        # Decomprimi gzip se serve
        if data[:2]==b"\x1f\x8b" or "gzip" in url.lower() or True:
            try:
                data=gzip.decompress(data)
                print(f"Decompresso: {len(data)} byte")
            except:
                print("Non era gzip, uso così com'è")
        text=data.decode("utf-8", errors="ignore")
        # Il feed è CSV con delimitatore |
        reader=csv.DictReader(io.StringIO(text), delimiter="|")
        print(f"Colonne: {reader.fieldnames}")
        out=[]
        n=0
        for row in reader:
            n+=1
            if n%100000==0: print(f"Letti {n} prodotti...")
            # Nomi colonne possono variare: prova tutti i nomi possibili
            nome=row.get("product_name") or row.get("productName") or row.get("name") or ""
            link=row.get("aw_deep_link") or row.get("awDeepLink") or row.get("link") or ""
            img=row.get("merchant_image_url") or row.get("imageUrl") or row.get("image") or ""
            prezzo=pulisci(row.get("display_price") or row.get("search_price") or row.get("price") or "")
            vecchio=pulisci(row.get("rrp_price") or row.get("rrp") or row.get("wasPrice") or "")
            sconto_txt=row.get("savings_percent") or row.get("savings") or ""
            try: sconto=float(str(sconto_txt).replace("%","").replace(",","."))
            except: sconto=None
            if not nome or not prezzo or not link: continue
            # SOLO con foto! Se non c'è foto, salta - così non arrivano più messaggi senza immagine!
            if not img or not img.startswith("http"): continue
            # Solo in stock se la colonna c'è
            stock=str(row.get("in_stock") or row.get("stock") or "1").lower()
            if stock in ["0","false","no","out of stock"]: continue
            if vecchio and vecchio<=prezzo: vecchio=None
            if sconto is None and vecchio: sconto=round((1-prezzo/vecchio)*100,1)
            if sconto is None: sconto=0
            # Solo offerte con un po' di sconto o con prezzo buono
            if sconto<10 and not vecchio: continue
            out.append({"nome":str(nome)[:150],"prezzo":prezzo,"vecchio":vecchio or "","sconto":sconto,"link":link,"img":img,"store":NOMI.get(STORE,STORE),"asin":"","stelle":"4.5"})
            if len(out)>2000: break
        print(f"Prodotti validi prima di togliere duplicati: {len(out)} su {n} letti")
        # TOGLI DUPLICATI: stesso prodotto in colori diversi = 1 solo!
        # Usiamo i primi 45 caratteri del nome + immagine per capire se è lo stesso prodotto
        visti=set()
        unici=[]
        for p in out:
            # Pulisci nome: togli colori, taglie, varianti
            nome_pulito=p["nome"].lower()
            for w in ["nero","bianco","rosso","blu","verde","rosa","grigio","argento","oro","beige","marrone","giallo","viola","arancione","colore","taglia","size","s ","m ","l ","xl "]:
                nome_pulito=nome_pulito.replace(w,"")
            chiave=nome_pulito[:45].strip()
            # Se abbiamo già questo prodotto, salta!
            if chiave in visti: continue
            visti.add(chiave)
            unici.append(p)
        out=unici
        print(f"Prodotti unici dopo aver tolto duplicati: {len(out)}")
        out.sort(key=lambda x: float(x["sconto"] or 0), reverse=True)
        top=out[:10]
        fn=f"top10_{STORE}.csv"
        with open(fn,"w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f, fieldnames=["nome","prezzo","vecchio","sconto","link","img","store","asin","stelle"]); w.writeheader()
            for p in top: w.writerow(p)
        print(f"Salvato {fn} - {len(top)} offerte VERE!")
        for p in top: print(f"  - {p['nome'][:60]} | {p['prezzo']}€ sconto {p['sconto']}% | foto={'SI' if p['img'] else 'NO'}")
    except Exception as e:
        print(f"Errore feed: {e}")
        import traceback; traceback.print_exc()
if __name__=="__main__": main()
