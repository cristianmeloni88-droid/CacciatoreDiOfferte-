"""
SHARDAN - Posta - VERSIONE PULITA: 1 messaggio bello, con foto, senza anteprima che si ripete
Se c'è l'immagine, manda FOTO + testo (niente anteprima link doppia).
Se non c'è immagine, manda testo con disable_web_page_preview=True (così non esce la scritta olandese!).
"""
import os, sys, csv, requests
TOKEN=os.environ.get("TELEGRAM_BOT_TOKEN","")
CHANNEL=os.environ.get("TELEGRAM_CHANNEL_ID","")
API=f"https://api.telegram.org/bot{TOKEN}"
STORE=(sys.argv[1] if len(sys.argv)>1 else "voghion").lower().strip()
# Loghi PNG via Google - funziona per TUTTI i siti, anche Thun e Bazta!
LOGHI={"voghion":"https://www.google.com/s2/favicons?domain=voghion.com&sz=256","thun":"https://www.google.com/s2/favicons?domain=thun.com&sz=256","bazta":"https://www.google.com/s2/favicons?domain=bazta.com&sz=256","aliexpress":"https://logo.clearbit.com/aliexpress.com","doctorquality":"https://www.google.com/s2/favicons?domain=doctorquality.it&sz=256"}
def main():
    fn=f"top10_{STORE}.csv"
    if not os.path.exists(fn):
        print(f"Non trovo {fn}"); return
    rows_raw=list(csv.DictReader(open(fn, encoding="utf-8")))
    # DEDUP finale: se lo stesso nome appare 2 volte, tieni solo la prima!
    import re
    visti=set(); rows=[]
    for r0 in rows_raw:
        nn=re.sub(r"[^a-z0-9]+"," ",str(r0.get("nome","")).lower()).strip()[:60]
        ii=str(r0.get("img","")).lower()
        if nn in visti: continue
        if any(x in ii for x in ["no-image","noimage","no_image","placeholder","nophoto"]): continue
        visti.add(nn); rows.append(r0)
        if len(rows)>=10: break
    print(f"Posto {STORE}: {len(rows)} messaggio/i pulito/i - NIENTE DUPLICATI")
    for i,p in enumerate(rows,1):
        nome=p.get("nome","Offerta")[:200]
        store=p.get("store",STORE)
        link=p.get("link","")
        img=p.get("img","") or LOGHI.get(STORE,"")
        # Testo pulito: titolo + store + bottone, SENZA descrizione lunga presa da Telegram
        testo=f"🔥 <b>{store}</b>\n\n{nome}\n\n👉 <a href=\"{link}\">Vedi Offerta</a>\n\n📱 TikTok: @shardanfighter1237"
        notifica=(i==1)
        # 1. Prova con FOTO (logo negozio) - così non esce l'anteprima olandese!
        if img and img.startswith("http"):
            r=requests.post(f"{API}/sendPhoto", data={"chat_id":CHANNEL,"photo":img,"caption":testo,"parse_mode":"HTML","disable_notification": not notifica}, timeout=20)
            print(f"Foto {STORE} {i}: {r.status_code} {r.text[:200]}")
            if r.status_code==200:
                print(f"✅ {STORE} {i} con foto (notifica={notifica})"); continue
            print("Foto fallita, provo senza foto...")
        # 2. Senza foto: disabilita anteprima link (così non esce la scritta olandese duplicata!)
        r=requests.post(f"{API}/sendMessage", data={"chat_id":CHANNEL,"text":testo,"parse_mode":"HTML","disable_notification": not notifica,"disable_web_page_preview": True}, timeout=20)
        print(f"{'✅' if r.status_code==200 else '❌'} {STORE} {i} testo pulito (notifica={notifica}) - {r.status_code} - {r.text[:200]}")
if __name__=="__main__": main()
