"""
SHARDAN NOMI V5 - DEFINITIVO
- Se trova prezzo vero nella pagina -> corregge
- Se NON trova prezzo e prezzo vetrina e assurdo -> CANCELLA il prodotto, non lo tiene
Meglio 3 prodotti con prezzo vero che 10 con prezzo falso.
"""
import csv, os, re, requests
HEADERS = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1", "Accept-Language": "it-IT,it;q=0.9"}
CSV_FILE = "top10_amazon.csv"
def pulisci(t):
    if not t: return None
    t=t.replace("€","").replace("EUR","").strip().replace(".","").replace(",",".")
    t=re.sub(r"[^0-9.]","",t)
    try:
        v=float(t)
        if 0.3<v<5000: return v
    except: pass
    return None
def assurdo(nome, prezzo):
    if not prezzo: return False
    n=(nome or "").lower()
    if any(k in n for k in ["matita","rossetto","labbra","crema","stick","mascara","smalto"]) and prezzo>40: return True
    if any(k in n for k in ["candeggina","detersivo","omino bianco","ace","pulizia"]) and prezzo>30: return True
    if any(k in n for k in ["calzini","socks","elastico","fascia","fitness","palestra","straps"]) and prezzo>60: return True
    if any(k in n for k in ["elastico","coresteady","fokky"]) and prezzo>60: return True
    return False
def prendi_da_pagina(asin):
    if not asin: return None,None
    try:
        r=requests.get(f"https://www.amazon.it/dp/{asin}", headers=HEADERS, timeout=20)
        html=r.text
        nome=None
        m=re.search(r"<title>([^<]+)</title>", html)
        if m:
            nome=m.group(1).replace("Amazon.it:","").strip()
            nome=re.sub(r"\s*:\s*(Bellezza|Casa.*|Salute.*)$","",nome).strip()
            if len(nome)<10: nome=None
            if nome and len(nome)>150: nome=nome[:150]
        prezzo=None
        for mm in re.finditer(r"a-price-whole[^>]*>([^<]+)</span>.*?a-price-fraction[^>]*>([^<]+)</span>", html, re.DOTALL):
            c=pulisci(mm.group(1)+"."+mm.group(2))
            if c: prezzo=c; break
        if not prezzo:
            for mm in re.finditer(r"a-offscreen[^>]*>([^<]*?\d[\d\.,]*\s*€[^<]*?)</span>", html):
                c=pulisci(mm.group(1))
                if c: prezzo=c; break
        return nome,prezzo
    except Exception as e:
        print(f" Errore pagina {asin}: {e}")
        return None,None
def main():
    print("=== SHARDAN NOMI V5 - Nome + Prezzo Vero - Cancella falsi ===")
    rows=list(csv.DictReader(open(CSV_FILE, encoding="utf-8")))
    print(f"Righe: {len(rows)}")
    tenuti=[]
    for r in rows:
        asin=r.get("asin","").strip()
        nome_old=r.get("nome","")
        try: prezzo_old=float(r.get("prezzo") or 0)
        except: prezzo_old=0
        print(f"\nControllo: {nome_old[:50]} - {prezzo_old}€ - {asin}")
        nome_nuovo, prezzo_nuovo=prendi_da_pagina(asin)
        if nome_nuovo and len(nome_nuovo)>12:
            print(f" -> NOME: {nome_nuovo[:70]}")
            r["nome"]=nome_nuovo[:150]
        if prezzo_nuovo:
            if prezzo_old!=prezzo_nuovo and (assurdo(r.get("nome",""), prezzo_old) or prezzo_nuovo < prezzo_old*0.5):
                print(f" -> PREZZO CORRETTO: {prezzo_old}€ -> {prezzo_nuovo}€")
                r["prezzo"]=prezzo_nuovo
                r["vecchio"]=""
                r["sconto"]=""
            else:
                print(f" Prezzo confermato: {prezzo_nuovo}€")
        else:
            print(f" Prezzo pagina non trovato")
        try: p_finale=float(r.get("prezzo") or 0)
        except: p_finale=0
        if assurdo(r.get("nome",""), p_finale):
            print(f" ❌ CANCELLO: prezzo ancora assurdo {p_finale}€ per {r.get('nome','')[:40]} - meglio 0 post che post falso")
            continue
        r["da_verificare"]=""
        tenuti.append(r)
    campi=list(tenuti[0].keys()) if tenuti else list(rows[0].keys())
    with open(CSV_FILE,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=campi)
        w.writeheader()
        for r in tenuti: w.writerow(r)
    print(f"\nFatto NOMI V5! Tenuti {len(tenuti)}/{len(rows)} con prezzo vero - Salvato {CSV_FILE}")
if __name__=="__main__": main()
