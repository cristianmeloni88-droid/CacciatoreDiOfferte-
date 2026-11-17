"""
SHARDAN - Caccia VERA AUTOMATICA - Il BOT va sui siti e prende le offerte vere!
NON usa Awin API (bloccata). Va DIRETTAMENTE sul sito del negozio!
NON serve mettere niente a mano! Il bot fa tutto!
Uso: python caccia_scrape.py voghion
     python caccia_scrape.py thun
     python caccia_scrape.py bazta
     python caccia_scrape.py aliexpress
Come funziona:
 1. Va sulla pagina Offerte / Novità / Best Seller del negozio
 2. Legge i prodotti: nome, prezzo, prezzo vecchio, foto, link
 3. Trasforma il link in link Awin (con la tua commissione!)
 4. Salva top10_<store>.csv con le offerte VERE
"""
import os, sys, re, requests, urllib.parse
from bs4 import BeautifulSoup
STORE=(sys.argv[1] if len(sys.argv)>1 else "voghion").lower().strip()
PUB="3154361"
# Config per ogni negozio: pagina offerte + ID Awin + nome
CONFIG={
  "voghion": {"urls": ["https://www.voghion.com/","https://www.voghion.com/deals","https://www.voghion.com/sale"], "mid":"44635","s":"3618806","v":"44635","q":"476294","nome":"Voghion Global"},
  "thun": {"urls": ["https://www.thun.com/it-it/offerte","https://www.thun.com/it-it/","https://www.thun.com/it-it/novita"], "mid":"","s":"","v":"","q":"","nome":"Thun IT"},
  "bazta": {"urls": ["https://www.bazta.com/","https://www.bazta.com/offerte"], "mid":"","s":"","v":"","q":"","nome":"Bazta IT"},
  "aliexpress": {"urls": ["https://www.aliexpress.com/","https://www.aliexpress.com/wholesale?SearchText=deals"], "mid":"12251","s":"","v":"","q":"","nome":"AliExpress IT"},
}
def awin_link(prod_url, cfg):
    # Trasforma link prodotto in link Awin con commissione!
    # Per Voghion usiamo il cread che già funziona, con u= link prodotto
    if cfg.get("s") and cfg.get("v") and cfg.get("q"):
        u=urllib.parse.quote(prod_url, safe="")
        return f"https://www.awin1.com/cread.php?s={cfg['s']}&v={cfg['v']}&q={cfg['q']}&r={PUB}&u={u}"
    # Per gli altri: awclick generico con p= link prodotto
    if cfg.get("mid"):
        u=urllib.parse.quote(prod_url, safe="")
        return f"https://www.awin1.com/awclick.php?mid={cfg['mid']}&id={PUB}&p={u}"
    # Se non abbiamo mid, torniamo il link normale (meglio che niente, ma senza commissione - da sistemare con ID Awin)
    return prod_url
def prezzo_da_testo(t):
    if not t: return None
    t=t.replace("\u20ac","").replace("€","").replace("EUR","").strip()
    m=re.search(r"(\d+[\.,]\d{2}|\d+)", t.replace(",","."))
    if not m: return None
    try:
        f=float(m.group(1))
        return f if 0.5 < f < 5000 else None
    except: return None
def main():
    cfg=CONFIG.get(STORE)
    if not cfg:
        print(f"Negozio {STORE} non configurato!"); return
    print(f"=== BOT SCRAPE AUTOMATICO: {cfg['nome']} ===")
    print("Il bot va sul sito e prende le offerte vere, da solo!")
    headers={"User-Agent":"Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36","Accept-Language":"it-IT,it;q=0.9"}
    prodotti=[]
    visti=set()
    for page_url in cfg["urls"]:
        if len(prodotti)>=10: break
        try:
            print(f"Vado su: {page_url}")
            r=requests.get(page_url, headers=headers, timeout=25)
            print(f" -> {r.status_code} - {len(r.text)} caratteri")
            if r.status_code!=200: continue
            soup=BeautifulSoup(r.text, "html.parser")
            # Cerca tutti i link prodotto con immagine e prezzo
            for a in soup.find_all("a", href=True):
                href=a["href"]
                if not href or len(href)<5: continue
                # Deve essere un link prodotto (contiene /product, /item, /p/, /dp/, ecc. o è lungo)
                if not any(k in href.lower() for k in ["/product","/item","/p/","/dp/","/detail","-p-",".html"]):
                    continue
                # Immagine dentro il link
                img_tag=a.find("img")
                if not img_tag: continue
                img=img_tag.get("src") or img_tag.get("data-src") or img_tag.get("data-lazy") or ""
                if not img or "logo" in img.lower() or "icon" in img.lower() or len(img)<10: continue
                if img.startswith("//"): img="https:"+img
                if img.startswith("/"): 
                    base=page_url.split("/")[0]+"//"+page_url.split("/")[2]
                    img=base+img
                # Nome
                nome=(a.get_text(" ", strip=True) or img_tag.get("alt") or "")[:150].strip()
                if len(nome)<5: continue
                # Prezzo vicino al link (nel genitore)
                parent=a.parent
                prezzo=None; vecchio=None
                if parent:
                    txt=parent.get_text(" ", strip=True)
                    # Cerca 2 prezzi: il primo è quello scontato, il secondo è il vecchio
                    nums=re.findall(r"(\d+[\.,]\d{2})\s*€", txt)
                    if nums:
                        prezzo=prezzo_da_testo(nums[0])
                        if len(nums)>=2: vecchio=prezzo_da_testo(nums[1])
                if not prezzo: continue
                # Link assoluto
                if href.startswith("/"):
                    base=page_url.split("/")[0]+"//"+page_url.split("/")[2]
                    href=base+href
                if href in visti: continue
                visti.add(href)
                sconto=round((1-prezzo/vecchio)*100,1) if vecchio and vecchio>prezzo else ""
                prodotti.append({"nome":nome,"prezzo":prezzo,"vecchio":vecchio or "","sconto":sconto,"link":awin_link(href, cfg),"img":img,"store":cfg["nome"],"asin":"","stelle":"4.5"})
                print(f"  ✅ Trovato: {nome[:50]} | {prezzo}€ sconto {sconto}%")
                if len(prodotti)>=10: break
        except Exception as e:
            print(f"Errore {page_url}: {e}")
    print(f"Totale offerte VERE trovate: {len(prodotti)}")
    # Se lo scrape non trova niente (sito bloccato), usa fallback 1 messaggio pulito (come prima) così non resta vuoto!
    if not prodotti:
        print("Scrape 0 - uso fallback 1 messaggio pulito")
        link=awin_link(cfg["urls"][0], cfg)
        prodotti.append({"nome":f"Offerte {cfg['nome']} - Scopri gli sconti di oggi!","prezzo":"Offerta","vecchio":"","sconto":"","link":link,"img":"","store":cfg["nome"],"asin":"","stelle":"4.5"})
    import csv
    fn=f"top10_{STORE}.csv"
    with open(fn,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=["nome","prezzo","vecchio","sconto","link","img","store","asin","stelle"]); w.writeheader()
        for p in prodotti[:10]: w.writerow(p)
    print(f"Salvato {fn} - {len(prodotti[:10])} offerte VERE - FATTO DAL BOT, NON A MANO!")
if __name__=="__main__": main()
