"""
SHARDAN - Agente NOMI V4 - Nome + PREZZO VERO dalla pagina prodotto
FIX prezzi falsi: la vetrina dava 270€ per una matita, 650€ per ACE.
La vetrina mente, la pagina del prodotto no.
NOMI V4 va su amazon.it/dp/ASIN e prende:
- Nome vero da <title>
- Prezzo vero da a-price-whole + a-price-fraction nella pagina prodotto
Se prezzo vetrina > 5x prezzo pagina, corregge con prezzo pagina.
Se prezzo pagina non trovato, tiene prezzo vetrina ma marca come DA VERIFICARE.
"""
import csv, os, re, requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Accept-Language": "it-IT,it;q=0.9",
}
CSV_FILE = "top10_amazon.csv"

def nome_e_brutto(nome):
    if not nome: return True
    n = nome.lower()
    if "su 5 stelle" in n: return True
    if "stelle" in n and len(nome) < 30: return True
    return False

def pulisci_prezzo(testo):
    if not testo: return None
    testo = testo.replace("€","").replace("EUR","").replace("&euro;","").strip()
    testo = testo.replace(".","").replace(",",".")
    testo = re.sub(r"[^0-9.]", "", testo)
    try:
        v = float(testo)
        if 0.3 < v < 5000: return v
    except: pass
    return None

def prendi_nome_e_prezzo_da_pagina(asin, prezzo_vetrina):
    """Va sulla pagina prodotto e prende nome + prezzo vero"""
    if not asin: return None, None
    url = f"https://www.amazon.it/dp/{asin}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        html = r.text
        # NOME da <title>
        nome = None
        m_title = re.search(r"<title>([^<]+)</title>", html)
        if m_title:
            nome = m_title.group(1).strip()
            # Pulisci: "Amazon.it: Rimmel ... : Bellezza" -> prendi prima parte
            nome = nome.replace("Amazon.it:", "").strip()
            # Togli " : Bellezza" finale se c'e
            nome = re.sub(r"\s*:\s*(Bellezza|Casa e cucina|Salute.*|Bricolage.*)$", "", nome).strip()
            # Togli "Amazon.it" residuo
            if len(nome) < 10: nome = None
            if nome and len(nome) > 150: nome = nome[:150]
        # PREZZO VERO dalla pagina prodotto - cerca a-price-whole vicino a a-price
        # Prova 3 modi, in ordine, e prendi il primo prezzo plausibile
        prezzo = None
        # Modo 1: a-price con data-a-color price
        for m in re.finditer(r"a-price-whole[^>]*>([^<]+)</span>.*?a-price-fraction[^>]*>([^<]+)</span>", html, re.DOTALL):
            cand = pulisci_prezzo(m.group(1) + "." + m.group(2))
            if cand:
                # Sanity: se prezzo vetrina e 270 e cand e 5.9, cand e giusto
                # Se ci sono piu prezzi, prendi il primo che e < prezzo vetrina se vetrina e assurdo
                prezzo = cand
                break
        # Modo 2: a-offscreen con €
        if not prezzo:
            for m in re.finditer(r"a-offscreen[^>]*>([^<]*?\d[\d\.,]*\s*€[^<]*?)</span>", html):
                cand = pulisci_prezzo(m.group(1))
                if cand:
                    prezzo = cand
                    break
        return nome, prezzo
    except Exception as e:
        print(f"  Errore pagina {asin}: {e}")
        return None, None

def prezzo_e_assurdo(nome, prezzo):
    """CAPO - Controllo plausibilita: una matita non costa 270€, una candeggina non costa 650€"""
    if not prezzo: return False
    n = (nome or "").lower()
    # Bellezza / cura: matita, rossetto, crema, stick labbra -> max 40€
    if any(k in n for k in ["matita", "rossetto", "labbra", "crema", "stick", "mascara", "smalto"]):
        if prezzo > 40: return True
    # Pulizia casa: candeggina, detersivo, omino bianco, ace -> max 30€
    if any(k in n for k in ["candeggina", "detersivo", "omino bianco", "ace", "pulizia"]):
        if prezzo > 30: return True
    # Calzini, elastici, fascette fitness -> max 40€
    if any(k in n for k in ["calzini", "socks", "elastico", "fascia", "fitness", "palestra"]):
        if prezzo > 60: return True
    return False

def main():
    print("=== SHARDAN Agente NOMI V4 - Nome + PREZZO VERO ===")
    if not os.path.exists(CSV_FILE):
        print(f"Non trovo {CSV_FILE}")
        return
    rows = list(csv.DictReader(open(CSV_FILE, encoding="utf-8")))
    print(f"Righe: {len(rows)}")
    corretti = 0
    for r in rows:
        asin = r.get("asin","").strip()
        nome_old = r.get("nome","")
        try: prezzo_old = float(r.get("prezzo") or 0)
        except: prezzo_old = 0
        print(f"\nControllo: {nome_old[:50]} - {prezzo_old}€ - ASIN {asin}")
        nome_nuovo, prezzo_nuovo = prendi_nome_e_prezzo_da_pagina(asin, prezzo_old)
        # Correggi nome se brutto o se pagina da nome migliore
        if nome_nuovo and (nome_e_brutto(nome_old) or len(nome_nuovo) > 12):
            print(f"  -> NOME: {nome_nuovo[:70]}")
            r["nome"] = nome_nuovo[:150]
            corretti += 1
        # Correggi prezzo se pagina da prezzo diverso e piu plausibile
        if prezzo_nuovo:
            # Se prezzo vetrina e assurdo (es. 270 per matita) e prezzo pagina e plausibile, correggi
            if prezzo_old != prezzo_nuovo:
                # Se prezzo pagina e molto piu basso e prezzo vecchio era assurdo, correggi sicuro
                if prezzo_e_assurdo(r.get("nome",""), prezzo_old) or prezzo_nuovo < prezzo_old * 0.5:
                    print(f"  -> PREZZO CORRETTO: {prezzo_old}€ -> {prezzo_nuovo}€ (vetrina sbagliava)")
                    r["prezzo"] = prezzo_nuovo
                    r["vecchio"] = ""
                    r["sconto"] = ""
                    corretti += 1
                else:
                    print(f"  Prezzo pagina {prezzo_nuovo}€, tengo vetrina {prezzo_old}€ (simili)")
            else:
                print(f"  Prezzo confermato: {prezzo_nuovo}€")
        else:
            print(f"  Prezzo pagina non trovato, tengo vetrina {prezzo_old}€")
        # Ultimo controllo CAPO: se prezzo ancora assurdo, marca come DA VERIFICARE e non postare
        try: p_finale = float(r.get("prezzo") or 0)
        except: p_finale = 0
        if prezzo_e_assurdo(r.get("nome",""), p_finale):
            print(f"  ⚠️ CAPO: Prezzo ancora assurdo {p_finale}€ per {r.get('nome','')[:40]} - segno come DA VERIFICARE, POST lo saltera")
            r["da_verificare"] = "SI"
        else:
            r["da_verificare"] = ""
    campi = list(rows[0].keys()) if rows else []
    if "da_verificare" not in campi: campi.append("da_verificare")
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campi)
        w.writeheader()
        for r in rows: w.writerow(r)
    print(f"\nFatto NOMI V4! Corretti: {corretti} - Salvato {CSV_FILE}")

if __name__ == "__main__":
    main()
