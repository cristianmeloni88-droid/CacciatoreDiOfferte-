"""
SHARDAN - MyLead CPI per TIPO - App o Giochi - VERSIONE LOGIN
Uso: python auto_mylead_tipo.py app    -> 3 App (1 notifica + 2 silenziosi)
Uso: python auto_mylead_tipo.py giochi -> 3 Giochi (1 notifica + 2 silenziosi)
Priorità:
 1. MYLEAD_API_KEY (token fisso, se c'è)
 2. MYLEAD_USERNAME + MYLEAD_PASSWORD -> login, prende token temporaneo, lo usa subito
 3. MYLEAD_TOP_MANUALE / MYLEAD_TOP_MANUALE_GIOCHI
"""
import os, sys, requests
TOKEN=os.environ.get("TELEGRAM_BOT_TOKEN","")
CHANNEL=os.environ.get("TELEGRAM_CHANNEL_ID","")
API=f"https://api.telegram.org/bot{TOKEN}"
TIPO=(sys.argv[1] if len(sys.argv)>1 else "app").lower().strip()
if TIPO in ["game","games"]: TIPO="giochi"
if TIPO not in ["app","giochi"]: TIPO="app"

def login_e_token():
    # 1. Se c'è API key fissa, usala
    key=os.environ.get("MYLEAD_API_KEY","").strip()
    if key:
        print("Uso MYLEAD_API_KEY fissa")
        return key
    # 2. Login con username + password -> token temporaneo
    user=os.environ.get("MYLEAD_USERNAME","").strip()
    pwd=os.environ.get("MYLEAD_PASSWORD","").strip()
    if not user or not pwd:
        print("Manca MYLEAD_USERNAME / MYLEAD_PASSWORD e manca MYLEAD_API_KEY")
        return None
    print(f"Login MyLead come {user} ...")
    # Prova i 2 endpoint di login più comuni di MyLead
    for url in ["https://mylead.global/api/external/v1/auth/login","https://mylead.global/api/v1/auth/login","https://pub.mylead.global/api/auth/login"]:
        try:
            r=requests.post(url, json={"username":user,"email":user,"password":pwd}, timeout=20)
            print(f"Login {url} -> {r.status_code}")
            if r.status_code==200:
                d=r.json()
                tok=d.get("token") or d.get("access_token") or d.get("data",{}).get("token") if isinstance(d,dict) else None
                if tok:
                    print("Token temporaneo preso! ✅")
                    return tok
        except Exception as e:
            print(f"Login {url} errore: {e}")
    print("Login fallito - controllo manuale")
    return None

def prendi_da_api():
    tok=login_e_token()
    if not tok: return []
    headers={"Authorization": f"Bearer {tok}"}
    for url in ["https://mylead.global/api/external/v1/campaigns","https://mylead.global/api/v1/campaigns","https://mylead.global/api/external/v1/offers"]:
        try:
            r=requests.get(url, headers=headers, timeout=20)
            print(f"GET {url} -> {r.status_code}")
            if r.status_code!=200: continue
            data=r.json()
            lst=data if isinstance(data, list) else data.get("campaigns", data.get("data", data.get("offers", [])))
            out=[]
            for o in lst:
                if not isinstance(o,dict): continue
                nome=o.get("name","") or ""
                link=o.get("link","") or o.get("tracking_link","") or ""
                try: pay=float(o.get("payout",0) or o.get("rate",0) or 0)
                except: pay=0
                cat=(str(o.get("category",""))+" "+str(o.get("type",""))+" "+nome).lower()
                is_gioco=any(k in cat for k in ["game","gioco","play","casino","gaming"])
                is_cpi=any(k in cat for k in ["cpi","install","app","mobile"]) or True
                if TIPO=="app" and is_gioco: continue
                if TIPO=="giochi" and not is_gioco: continue
                if nome and link and pay>=0.20:
                    out.append({"nome":nome,"link":link,"payout":pay})
            out.sort(key=lambda x: x["payout"], reverse=True)
            if out: return out[:3]
        except Exception as e:
            print(f"GET {url} errore: {e}")
    return []

def prendi_da_manuale():
    env_name="MYLEAD_TOP_MANUALE" if TIPO=="app" else "MYLEAD_TOP_MANUALE_GIOCHI"
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
        print(f"Nessuna offerta {TIPO} - controlla Secrets MYLEAD_USERNAME / MYLEAD_PASSWORD o MANUALE")
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
