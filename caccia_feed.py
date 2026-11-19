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
NOMI={"voghion":"Voghion Global","thun":"Thun IT","bazta":"Bazta IT","aliexpress":"AliExpress IT","doctorquality":"DoctorQuality IT"}
# OFFSET: ogni negozio prende prodotti diversi per NON ripetere gli stessi!
# Voghion prende i primi 10, AliExpress dal 10 al 20, Bazta dal 20 al 30!
OFFSET={"voghion":0,"thun":0,"doctorquality":0,"aliexpress":10,"bazta":20}
def base_prodotto(s):
    # Base aggressiva: toglie varianti "con farfalla/cuore/fiore/sole", numeri, colori
    s=str(s).lower()
    s=re.sub(r"\bcon\b.*$","",s)  # toglie tutto dopo "con"
    s=re.sub(r"\b(colore|color|variant|variante|modello|tipo)\b.*$","",s)
    s=re.sub(r"[^a-z0-9]+"," ",s)
    parole=[w for w in s.split() if w not in ("di","a","per","da","con","il","la","le","in","e","cm","mm","pezzi","set","da")]
    # Prendi solo le prime 4 parole significative = la base del prodotto!
    return " ".join(parole[:4])

def norm_nome(s):
    import re
    s=str(s).lower()
    s=re.sub(r"[^a-z0-9]+"," ",s)
    s=re.sub(r"\s+"," ",s).strip()
    return s[:60]

def base_prodotto(s):
    import re
    s=str(s).lower()
    # Taglia tutto dopo "con" (varianti colore, ecc.)
    s=re.sub(r"\bcon\b.*$","",s)
    s=re.sub(r"[^a-z0-9]+"," ",s)
    parole=[w for w in s.split() if w not in ("di","a","per","da","con","il","la","le","in","e","cm","mm","pezzi","set","da","fetta","torta","nuovissimo","nuovo","nuova")]
    # Solo prime 2 parole = marca + modello! OLEVS 2856 = stesso prodotto anche se descrizione diversa!
    return " ".join(parole[:2])

def img_brutta(img):
    img=str(img).lower()
    return any(x in img for x in ["no-image","noimage","no_image","placeholder","nophoto","no-photo","not-available","noavailable","missing","default-image","coming-soon"])

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
            img=row.get("merchant_image_url") or row.get("aw_image_url") or row.get("imageUrl") or row.get("image") or ""
            prezzo=pulisci(row.get("display_price") or row.get("search_price") or row.get("price") or row.get("product_price") or row.get("base_price_amount") or "")
            vecchio=pulisci(row.get("product_price_old") or row.get("rrp_price") or row.get("rrp") or row.get("wasPrice") or row.get("base_price") or row.get("product_price") or "")
            sconto_txt=row.get("savings_percent") or row.get("savings") or ""
            try: sconto=float(str(sconto_txt).replace("%","").replace(",","."))
            except: sconto=None
            if not nome or not prezzo or not link: continue
            # SALTA righe spazzatura: descrizioni negozio, non prodotti!
            if nome.lower().startswith("offerte "): continue
            if "bomboniere, idee regalo" in nome.lower(): continue
            if len(nome)<10: continue
            # Solo in stock se la colonna c'è
            stock=str(row.get("in_stock") or row.get("stock") or "1").lower()
            if stock in ["0","false","no","out of stock"]: continue
            if vecchio and vecchio<=prezzo: vecchio=None
            if sconto is None and vecchio: sconto=round((1-prezzo/vecchio)*100,1)
            if sconto is None: sconto=0
            # FIX Thun/Bazta: il loro feed NON ha colonna sconto/vecchio!
            # Non scartare niente, se ha nome+prezzo+link+foto è buono!
            # Scarta solo se non ha foto (altrimenti Telegram non manda niente)
            # SOLO prodotti CON vecchio prezzo e sconto! Se no, salta - cosi tutti hanno vecchio+nuovo!
            # Eccezione Thun: Thun non fa sconti, se filtriamo tutto resta vuoto, quindi Thun puo' passare anche senza vecchio
            if STORE != "thun":
                if not vecchio or sconto is None or sconto < 5: continue
            if not img: continue
            if img_brutta(img): continue
            # DEDUP: stesso prodotto in 2 feed diversi (Bazta ha 2 fid!) -> salta se nome o foto già visti
            chiave_nome=norm_nome(nome)
            chiave_base=base_prodotto(nome)
            if any(base_prodotto(x["nome"])==chiave_base for x in out): continue
            if any(norm_nome(x["nome"])==chiave_nome for x in out): continue
            if any(x["img"]==img for x in out): continue
            bb=base_prodotto(nome)
            if any(base_prodotto(x["nome"])==bb for x in out): continue
            out.append({"nome":str(nome)[:150],"prezzo":prezzo,"vecchio":vecchio or "","sconto":sconto,"link":link,"img":img,"store":NOMI.get(STORE,STORE),"asin":"","stelle":"4.5"})
            if len(out)>2000: break
        print(f"Prodotti validi: {len(out)} su {n} letti")
        # Se tutti hanno sconto 0 (feed senza colonna sconto), ordina per prezzo basso
        if out and all(float(x["sconto"] or 0)==0 for x in out):
            out.sort(key=lambda x: float(x["prezzo"] or 999))
        else:
            out.sort(key=lambda x: float(x["sconto"] or 0), reverse=True)
        # ANTI-RIPETIZIONE: se i primi 10 sono tutti simili, salta e prendi prodotti più vari!
        # Prendi 1 ogni N per mescolare: così non escono 5 scatoline di fila!
        # OFFSET per negozio: Voghion 0, AliExpress 10, Bazta 20 - prodotti diversi!
        off=OFFSET.get(STORE,0)
        out_offset = out[off:] if len(out)>off else out
        if len(out_offset) > 30:
            top=[]
            step=max(1, len(out_offset)//30)
            i=0
            while len(top)<10 and i < len(out_offset):
                top.append(out_offset[i])
                i+=step+3
            # Se non bastano, riempi con i primi
            for x in out:
                if len(top)>=10: break
                if x not in top: top.append(x)
        else:
            off=OFFSET.get(STORE,0)
            top=out[off:off+10] if len(out)>off else out[:10]
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
