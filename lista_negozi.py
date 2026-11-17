"""
SHARDAN - Lista tutti i negozi JOINED su Awin con nome esatto
Uso: python lista_negozi.py
Stampa nome + ID di tutti i negozi approvati. Così vediamo come si chiama davvero Thun / Bazta / Voghion.
"""
import os, requests
PUB=os.environ.get("AWIN_PUBLISHER_ID","3154361").strip()
TOKEN=os.environ.get("AWIN_API_KEY","").strip()
HEAD={"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"}
print("=== LISTA NEGOZI JOINED ===")
print(f"Publisher: {PUB}")
if not TOKEN:
    print("Manca AWIN_API_KEY"); exit()
for pagina in [0,100,200]:
    try:
        r=requests.get(f"https://api.awin.com/publishers/{PUB}/programmes?relationship=joined&limit=100&offset={pagina}", headers=HEAD, timeout=30)
        print(f"Pagina offset {pagina} -> {r.status_code}")
        if r.status_code!=200:
            print(r.text[:500]); break
        data=r.json()
        progs=data if isinstance(data,list) else data.get("programmes", data.get("data", []))
        print(f"Trovati in pagina: {len(progs)}")
        if not progs: break
        for p in progs:
            adv=p.get("advertiser",{}) if isinstance(p,dict) else {}
            print(f" - {adv.get('name')} | ID={adv.get('id')} | status={p.get('status')}")
    except Exception as e:
        print("Errore:", e); break
print("=== FINE LISTA ===")
