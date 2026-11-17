"""
SHARDAN - Posta SINGOLO negozio su Telegram
Uso: python posta_store.py voghion  -> posta top10_voghion.csv (1 con notifica + 9 silenziosi)
Uso: python posta_store.py thun
Uso: python posta_store.py bazta
"""
import os, sys, csv, requests
TOKEN=os.environ.get("TELEGRAM_BOT_TOKEN","")
CHANNEL=os.environ.get("TELEGRAM_CHANNEL_ID","")
API=f"https://api.telegram.org/bot{TOKEN}"
STORE=(sys.argv[1] if len(sys.argv)>1 else "voghion").lower().strip()

def formatta(p, pos):
    nome=p.get("nome","Prodotto")[:120]
    prezzo=p.get("prezzo","?")
    vecchio=p.get("vecchio","")
    sconto=p.get("sconto","")
    link=p.get("link","")
    store=p.get("store",STORE)
    riga=f"💰 <b>{prezzo}€</b>"
    if vecchio:
        try:
            if float(vecchio)>float(prezzo): riga+=f"  <s>{vecchio}€</s>"
        except: pass
    if sconto:
        try:
            if float(sconto)>=20: riga+=f"  🔥 <b>-{int(float(sconto))}%</b>"
        except: pass
    t=f"<b>{pos}. {nome}</b>\n{store}\n{riga}\n⭐⭐⭐⭐⭐\n"
    if link: t+=f"👉 <a href=\"{link}\">Vedi Offerta</a>"
    return t[:900]

def invia(p, pos, notifica):
    testo=formatta(p,pos)
    img=p.get("img","")
    if img and img.startswith("http"):
        r=requests.post(f"{API}/sendPhoto", data={"chat_id":CHANNEL,"photo":img,"caption":testo,"parse_mode":"HTML","disable_notification": not notifica}, timeout=20)
        if r.status_code==200:
            print(f"✅ {STORE} {pos} con foto (notifica={notifica})"); return True
    r=requests.post(f"{API}/sendMessage", data={"chat_id":CHANNEL,"text":testo,"parse_mode":"HTML","disable_notification": not notifica}, timeout=20)
    print(f"{'✅' if r.status_code==200 else '❌'} {STORE} {pos} (notifica={notifica}) - {r.status_code}")
    return r.status_code==200

def main():
    fn=f"top10_{STORE}.csv"
    if not os.path.exists(fn):
        print(f"Non trovo {fn} - prima lancia caccia_store.py {STORE}")
        return
    rows=list(csv.DictReader(open(fn, encoding="utf-8")))[:10]
    print(f"Posto {STORE}: {len(rows)} prodotti - 1 con notifica + {len(rows)-1} silenziosi")
    # Prima un messaggio intestazione con notifica? No: il primo prodotto ha notifica, gli altri no (come chiesto)
    for i,p in enumerate(rows,1):
        invia(p,i,notifica=(i==1))

if __name__=="__main__": main()
