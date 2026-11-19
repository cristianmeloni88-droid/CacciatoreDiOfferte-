"""
SHARDAN - Posta - CON PREZZI vecchio barrato + nuovo + sconto - SENZA DUPLICATI
Formato: ~~vecchio~~ -> nuovo + sconto + risparmio
"""
import os, sys, csv, requests
TOKEN=os.environ.get("TELEGRAM_BOT_TOKEN","")
CHANNEL=os.environ.get("TELEGRAM_CHANNEL_ID","")
API=f"https://api.telegram.org/bot{TOKEN}"
STORE=(sys.argv[1] if len(sys.argv)>1 else "voghion").lower().strip()
LOGHI={"voghion":"https://www.google.com/s2/favicons?domain=voghion.com&sz=256","thun":"https://www.google.com/s2/favicons?domain=thun.com&sz=256","bazta":"https://www.google.com/s2/favicons?domain=bazta.com&sz=256","aliexpress":"https://logo.clearbit.com/aliexpress.com","doctorquality":"https://www.google.com/s2/favicons?domain=doctorquality.it&sz=256","natugea":"https://www.google.com/s2/favicons?domain=natugea.com&sz=256","imou":"https://www.google.com/s2/favicons?domain=imou.com&sz=256"}
def fmt_prezzo(v):
    try:
        f=float(str(v).replace(",",".").replace("€","").strip())
        if f<=0: return None
        return f"{f:.2f} €".replace(".",",")
    except: return None
def main():
    fn=f"top10_{STORE}.csv"
    if not os.path.exists(fn):
        print(f"Non trovo {fn}"); return
    rows_raw=list(csv.DictReader(open(fn, encoding="utf-8")))
    import re
    def base_p(n):
        n=str(n).lower()
        n=re.sub(r"\bcon\b.*$","",n)
        n=re.sub(r"[^a-z0-9]+"," ",n)
        parole=[w for w in n.split() if w not in ("di","a","per","da","con","il","la","le","in","e","cm","mm","pezzi","set","da")]
        return " ".join(parole[:4])
    visti=set(); visti_base=set(); rows=[]
    for r0 in rows_raw:
        nome=str(r0.get("nome","")).strip()
        # SALTA righe spazzatura: descrizioni negozio, non prodotti!
        if not nome: continue
        if nome.lower().startswith("offerte "): continue
        if "bomboniere, idee regalo" in nome.lower(): continue
        if len(nome)<10: continue
        # SALTA se non ha prezzo vero
        if not fmt_prezzo(r0.get("prezzo","")): continue
        nn=re.sub(r"[^a-z0-9]+"," ",nome.lower()).strip()[:60]
        ii=str(r0.get("img","")).lower()
        bb=base_p(nome)
        if nn in visti: continue
        if bb in visti_base: continue
        if any(x in ii for x in ["no-image","noimage","no_image","placeholder","nophoto"]): continue
        visti.add(nn); visti_base.add(bb); rows.append(r0)
        if len(rows)>=10: break
    print(f"Posto {STORE}: {len(rows)} con PREZZI!")
    for i,p in enumerate(rows,1):
        nome=p.get("nome","Offerta")[:150]
        store=p.get("store",STORE)
        link=p.get("link","")
        img=p.get("img","") or LOGHI.get(STORE,"")
        nuovo=fmt_prezzo(p.get("prezzo",""))
        vecchio=fmt_prezzo(p.get("vecchio",""))
        try: sconto=float(str(p.get("sconto","0")).replace(",",".").replace("%",""))
        except: sconto=0
        if vecchio and nuovo and vecchio != nuovo:
            try:
                v_old=float(str(p.get("vecchio","")).replace(",","."))
                v_new=float(str(p.get("prezzo","")).replace(",","."))
                risparmio=v_old - v_new
                risparmio_txt=f"💸 Risparmi {risparmio:.2f} €".replace(".",",")
            except: risparmio_txt=""
            if sconto and sconto>0:
                riga_prezzi=f"~~{vecchio}~~  ➡️  <b>{nuovo}</b>\n🔥 Sconto: <b>-{int(round(sconto))}%</b>  {risparmio_txt}"
            else:
                riga_prezzi=f"~~{vecchio}~~  ➡️  <b>{nuovo}</b>\n{risparmio_txt}"
        elif nuovo:
            riga_prezzi=f"💰 Prezzo: <b>{nuovo}</b>"
            if sconto and sconto>0:
                riga_prezzi+=f"  🔥 -{int(round(sconto))}%"
        else:
            riga_prezzi=""
        testo=f"🔥 <b>{store}</b>\n\n{nome}\n\n{riga_prezzi}\n\n👉 <a href=\"{link}\">Vedi Offerta</a>\n\n📱 TikTok: @shardanfighter1237"
        notifica=(i==1)
        if img and img.startswith("http"):
            r=requests.post(f"{API}/sendPhoto", data={"chat_id":CHANNEL,"photo":img,"caption":testo,"parse_mode":"HTML","disable_notification": not notifica}, timeout=20)
            print(f"Foto {STORE} {i}: {r.status_code}")
            if r.status_code==200: continue
        r=requests.post(f"{API}/sendMessage", data={"chat_id":CHANNEL,"text":testo,"parse_mode":"HTML","disable_notification": not notifica,"disable_web_page_preview": True}, timeout=20)
        print(f"{'✅' if r.status_code==200 else '❌'} {STORE} {i} - {r.status_code}")
if __name__=="__main__": main()
