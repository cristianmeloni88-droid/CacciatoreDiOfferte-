"""
SHARDAN - MyLead CPI per TIPO - App o Giochi
Uso: python auto_mylead_tipo.py app    -> posta 3 migliori APP (1 notifica + 2 silenziosi)
Uso: python auto_mylead_tipo.py giochi -> posta 3 migliori GIOCHI (1 notifica + 2 silenziosi)
Usa MYLEAD_API_KEY se c'è, altrimenti usa MYLEAD_TOP_MANUALE
Formato MYLEAD_TOP_MANUALE per APP:  Nome|Link|Payout;Nome|Link|Payout
Formato MYLEAD_TOP_MANUALE_GIOCHI: Nome|Link|Payout;...
"""
import os, sys, requests
TOKEN=os.environ.get("TELEGRAM_BOT_TOKEN","")
CHANNEL=os.environ.get("TELEGRAM_CHANNEL_ID","")
API=f"https://api.telegram.org/bot{TOKEN}"
TIPO=(sys.argv[1] if len(sys.argv)>1 else "app").lower().strip()
if TIPO not in ["app","giochi","game","games"]: TIPO="app"
if TIPO in ["game","games"]: TIPO="giochi"

def prendi_da_api():
    key=os.environ.get("MYLEAD_API_KEY","")
    if not key: return []
    try:
        r=requests.get("https://mylead.global/api/v1/campaigns", headers={"Authorization": f"Bearer {key}"}, timeout=20)
        if r.status_code!=200: return []
        data=r.json()
        lst=data if isinstance(data, list) else data.get("campaigns", data.get("data", []))
        out=[]
        for o in lst:
            nome=o.get("name","") or ""
            link=o.get("link","") or ""
            try: pay=float(o.get("payout",0) or 0)
            except: pay=0
            cat=(o.get("category","")+" "+o.get("type","")).lower()
            # Filtra per tipo
            is_gioco = any(k in nome.lower()+cat for k in ["game","gioco","play","casino"])
            if TIPO=="app" and is_gioco: continue
            if TIPO=="giochi" and not is_gioco: continue
            if nome and link and pay>=0.30:
                out.append({"nome":nome,"link":link,"payout":pay})
        out.sort(key=lambda x: x["payout"], reverse=True)
        return out[:3]
    except: return []

def prendi_da_manuale():
    env_name = "MYLEAD_TOP_MANUALE" if TIPO=="app" else "MYLEAD_TOP_MANUALE_GIOCHI"
    txt=os.environ.get(env_name,"")
    if not txt: return []
    out=[]
    for parte in txt.split(";"):
        try:
            n,l,pay=parte.split("|")
            out.append({"nome":n.strip(),"link":l.strip(),"payout":float(pay)})
        except: continue
    out.sort(key=lambda x: x["payout"], reverse=True)
    return out[:3]

def main():
    print(f"=== MyLead CPI {TIPO.upper()} - Top 3 ===")
    top=prendi_da_api() or prendi_da_manuale()
    if not top:
        print(f"Nessuna offerta {TIPO} - metti MYLEAD_API_KEY o MYLEAD_TOP_MANUALE{'_GIOCHI' if TIPO=='giochi' else ''} nei Secrets!")
        print("Esempio manuale: Nome App|https://go.mylead.global/...|1.50;Nome App 2|https://...|1.20")
        return
    print(f"Top {len(top)} {TIPO}:")
    for p in top: print(f"  - {p['nome']} - {p['payout']}€")
    emoji="📱" if TIPO=="app" else "🎮"
    titolo="APP" if TIPO=="app" else "GIOCHI"
    for i,p in enumerate(top,1):
        notifica=(i==1)
        testo=f"{emoji} <b>{i}. {p['nome']}</b>\n{titolo} del giorno - Paga {p['payout']}€ a installazione\n👉 <a href=\"{p['link']}\">Scopri {'l\\'app' if TIPO=='app' else 'il gioco'}</a>\n\n📱 TikTok: @shardanfighter1237"
        r=requests.post(f"{API}/sendMessage", data={"chat_id":CHANNEL,"text":testo,"parse_mode":"HTML","disable_notification": not notifica}, timeout=20)
        print(f"{'✅' if r.status_code==200 else '❌'} {TIPO} {i} (notifica={notifica}) - {r.status_code}")

if __name__=="__main__": main()
