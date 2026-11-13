"""
SHARDAN - Agente NOMI V3 - Nome dalla pagina Amazon, SENZA Groq Vision
Perche: Groq ha tolto tutti i modelli Vision dal piano gratis (scout, maverick, 3.2).
Quindi NOMI non guarda piu la foto con Groq. Va sulla pagina Amazon del prodotto
usando ASIN: https://www.amazon.it/dp/ASIN e prende il <title> che e il nome vero.
Gratis, sempre, senza API key.
"""
import csv, os, re, requests

CSV_FILE = "top10_amazon.csv"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Accept-Language": "it-IT,it;q=0.9",
}

def nome_e_brutto(nome):
    if not nome: return True
    n = nome.lower()
    if "su 5 stelle" in n: return True
    if "stelle" in n and len(nome) < 30: return True
    if "il mio amazon" in n: return True
    return False

def nome_da_pagina_amazon(asin, link):
    # Prova 1: pagina /dp/ASIN
    urls = []
    if asin: urls.append(f"https://www.amazon.it/dp/{asin}")
    if link and "/dp/" in link: urls.append(link.split("?")[0])
    for url in urls:
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            html = r.text
            # 1) og:title
            m = re.search(r'<meta property="og:title" content="([^"]+)"', html)
            if m:
                nome = m.group(1).strip()
                if len(nome) >= 12 and "amazon" not in nome.lower()[:20]:
                    return nome[:150]
            # 2) <title>
            m2 = re.search(r'<title>([^<]+)</title>', html)
            if m2:
                nome = m2.group(1).strip()
                # Pulisci "Amazon.it: ..."
                nome = re.sub(r'^Amazon\.it\s*:\s*', '', nome, flags=re.I)
                nome = re.sub(r'\s*:\s*Amazon\.it.*$', '', nome, flags=re.I)
                nome = nome.strip()
                if len(nome) >= 12 and "su 5 stelle" not in nome.lower():
                    return nome[:150]
            # 3) productTitle
            m3 = re.search(r'id="productTitle"[^>]*>([^<]+)<', html)
            if m3:
                nome = re.sub(r'\s+', ' ', m3.group(1)).strip()
                if len(nome) >= 12:
                    return nome[:150]
        except Exception as e:
            print(f"  Errore pagina {url[:60]}: {e}")
            continue
    return None

def main():
    print("=== SHARDAN Agente NOMI V3 - Nome dalla pagina Amazon, senza Groq Vision ===")
    if not os.path.exists(CSV_FILE):
        print(f"Non trovo {CSV_FILE}")
        return
    rows = list(csv.DictReader(open(CSV_FILE, encoding="utf-8")))
    print(f"Righe da controllare: {len(rows)}")
    cambiati = 0
    for r in rows:
        nome = r.get("nome", "")
        if not nome_e_brutto(nome):
            print(f"OK gia buono: {nome[:60]}")
            continue
        asin = r.get("asin","")
        print(f"\nDa sistemare: {nome} - {r.get('prezzo')}€ - ASIN {asin}")
        nuovo = nome_da_pagina_amazon(asin, r.get("link",""))
        if nuovo:
            print(f"  -> NUOVO NOME da pagina Amazon: {nuovo[:80]}")
            r["nome"] = nuovo
            cambiati += 1
        else:
            print("  -> Non trovato nome su pagina, lascio vecchio, non invento")
    campi = list(rows[0].keys()) if rows else []
    if "descrizione" not in campi: campi.append("descrizione")
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campi)
        w.writeheader()
        for r in rows: w.writerow(r)
    print(f"\nFatto! Nomi sistemati: {cambiati}/{len(rows)} - Salvato {CSV_FILE}")

if __name__ == "__main__":
    main()
