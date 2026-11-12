# SHARDAN - Amazon Top 10 - Selettori Vetrina
# STORE 4 - Amazon - PARTIAMO DA QUI
# Perche Amazon e difficile: Amazon blocca chi legge troppe pagine troppo in fretta.
# Quindi: 1 richiesta all ora, non di piu. E se Amazon blocca, il file NON inventa prezzi, salta.
# Vetrine usate (sono le vetrine di Amazon, non lista tua):
#  - https://www.amazon.it/deals -> Offerte del giorno di Amazon
#  - https://www.amazon.it/gp/bestsellers -> Piu venduti secondo Amazon
#  - https://www.amazon.it/gp/movers-and-shakers -> Quelli che stanno salendo di piu
import re, csv, math, time, requests
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
    "Accept-Language": "it-IT,it;q=0.9",
    "Accept": "text/html,application/xhtml+xml",
}

VETRINE_AMAZON = [
    ("deals", "https://www.amazon.it/deals"),
    ("bestsellers", "https://www.amazon.it/gp/bestsellers"),
    ("movers", "https://www.amazon.it/gp/movers-and-shakers"),
]

# SELETTORI AMAZON - dove Amazon scrive titolo e prezzo nella pagina
# Questi sono i nomi che Amazon usa nel codice della pagina:
#  - Contenitore prodotto: data-component-type="s-search-result" oppure div con data-asin
#  - Titolo: h2 > a > span  oppure span con a-size-medium
#  - Prezzo intero: span class="a-price-whole" -> es: 29
#  - Prezzo decimali: span class="a-price-fraction" -> es: 90  => 29,90
#  - Prezzo vecchio: span class="a-text-price" > span class="a-offscreen" -> es: 89,90 €
#  - Stelle: span class="a-icon-alt" -> es: "4,7 su 5 stelle"
#  - Num recensioni: span class="a-size-base" dopo le stelle
SELECTORS_INFO = """
SELETTORI AMAZON (per debug):
- Prodotto: [data-component-type="s-search-result"] o [data-asin]
- Titolo: h2 a span
- Prezzo: .a-price-whole + .a-price-fraction
- Vecchio: .a-text-price .a-offscreen
- Stelle: .a-icon-alt
"""

def pulisci_prezzo_amazon(intero, frazione):
    try:
        intero = intero.replace(".", "").replace(",", "").strip()
        frazione = frazione.strip()
        return float(f"{intero}.{frazione}")
    except:
        return None

def estrai_prodotti_amazon(html, vetrina_nome):
    """Estrae prodotti da HTML Amazon usando i selettori sopra. Senza BeautifulSoup, con regex robuste."""
    prodotti = []
    # Dividi per prodotto: ogni prodotto ha data-asin="B..."
    blocchi = re.split(r'data-asin="(B[A-Z0-9]{9})"', html)
    # blocchi[0] = testa, poi asin, blocco, asin, blocco...
    for i in range(1, len(blocchi)-1, 2):
        asin = blocchi[i]
        blocco = blocchi[i+1][:8000]  # primi 8000 caratteri del blocco prodotto
        # TITOLO: cerca h2 > a > span
        m_titolo = re.search(r'<h2[^>]*>.*?<span[^>]*>([^<]{10,200})</span>', blocco, flags=re.S)
        if not m_titolo:
            m_titolo = re.search(r'a-size-medium[^>]*>([^<]{10,200})<', blocco)
        titolo = m_titolo.group(1).strip() if m_titolo else ""
        titolo = re.sub(r'\s+', ' ', titolo).strip()
        if len(titolo) < 10: continue
        # PREZZO: a-price-whole + a-price-fraction
        m_prezzo = re.search(r'a-price-whole[^>]*>([\d\.,]+)<.*?a-price-fraction[^>]*>(\d+)', blocco, flags=re.S)
        if not m_prezzo: continue
        prezzo = pulisci_prezzo_amazon(m_prezzo.group(1), m_prezzo.group(2))
        if not prezzo: continue
        # PREZZO VECCHIO: a-text-price
        m_vecchio = re.search(r'a-text-price.*?a-offscreen[^>]*>([\d\.,]+)', blocco, flags=re.S)
        vecchio = None
        if m_vecchio:
            try: vecchio = float(m_vecchio.group(1).replace(".", "").replace(",", ".").replace("€","").strip())
            except: vecchio = None
        if not vecchio or vecchio <= prezzo: vecchio = prezzo  # se non c e vecchio, non e offerta, lo scartiamo dopo
        # STELLE
        m_stelle = re.search(r'(\d[\.,]\d)\s*su 5 stelle', blocco)
        stelle = float(m_stelle.group(1).replace(",", ".")) if m_stelle else 4.5
        # NUM RECENSIONI: cerca numero dopo stelle, es: "1.250" vicino a a-size-base
        m_rec = re.search(r'a-size-base[^>]*>([\d\.,]+)</span>\s*</a>\s*</span>\s*<span[^>]*>\s*<span', blocco)
        num_rec = 100
        if m_rec:
            try: num_rec = int(m_rec.group(1).replace(".", "").replace(",", ""))
            except: num_rec = 100
        # PUNTEGGIO Qualita-Prezzo
        sconto = round((vecchio - prezzo)/vecchio*100, 1) if vecchio else 0
        punti_sconto = min(40, (sconto/70)*40) if sconto>0 else 0
        punti_stelle = (stelle/5)*30
        punti_popol = min(20, math.log10(num_rec+1)/math.log10(5000)*20) if num_rec else 5
        punti_conv = 10 if prezzo < 50 else (7 if prezzo < 150 else 4)
        punteggio = round(punti_sconto + punti_stelle + punti_popol + punti_conv, 1)
        link = f"https://www.amazon.it/dp/{asin}"
        prodotti.append({
            "Nome": titolo, "Prezzo": prezzo, "Vecchio": vecchio, "Sconto%": sconto,
            "Recensioni": stelle, "NumRecensioni": num_rec, "PunteggioQP": punteggio,
            "Categoria": vetrina_nome, "Shop": "Amazon", "Link": link, "ASIN": asin,
            "Agente": "AMA_CACCIA", "Fonte": f"amazon-vetrina-{vetrina_nome}",
            "Stato": "ERRORE_POSSIBILE" if sconto >= 70 else ("TOP10_QP" if punteggio >= 55 and sconto >= 20 else "SCARTO"),
            "DataControllo": datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
    return prodotti

def caccia_amazon_top10():
    print("=== SHARDAN Amazon Top 10 - Vetrine Amazon ===")
    tutti = []
    for nome_vetrina, url in VETRINE_AMAZON:
        print(f"\n--- Amazon vetrina: {nome_vetrina} -> {url} ---")
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            print(f"Status: {r.status_code}, {len(r.text)} caratteri")
            if r.status_code != 200:
                print("Amazon ha bloccato o non ha risposto. NON invento prezzi. Provo prossima vetrina.")
                continue
            if "Inserisci i caratteri" in r.text or "captcha" in r.text.lower():
                print("Amazon chiede captcha. STOP: non forzo. Salto questa ora.")
                continue
            prodotti = estrai_prodotti_amazon(r.text, nome_vetrina)
            print(f"Trovati {len(prodotti)} prodotti con prezzo letto in questa vetrina")
            tutti.extend(prodotti)
        except Exception as e:
            print(f"Errore vetrina {nome_vetrina}: {e}")
        time.sleep(5)  # pausa educata: Amazon blocca se vai troppo veloce
    # Deduplica per ASIN, tieni punteggio piu alto
    visti = {}
    for p in tutti:
        if p["ASIN"] not in visti or p["PunteggioQP"] > visti[p["ASIN"]]["PunteggioQP"]:
            visti[p["ASIN"]] = p
    unici = list(visti.values())
    # Top 10: solo TOP10_QP, ordinati per punteggio
    top10 = sorted([p for p in unici if p["Stato"]=="TOP10_QP"], key=lambda x: x["PunteggioQP"], reverse=True)[:10]
    errori = [p for p in unici if p["Stato"]=="ERRORE_POSSIBILE"]
    print(f"\n=== RISULTATO AMAZON ===")
    print(f"Prodotti letti totali: {len(unici)} | Top10: {len(top10)} | Errori >70%: {len(errori)} | Scartati: {len(unici)-len(top10)-len(errori)}")
    for i, p in enumerate(top10, 1):
        print(f"{i}. {p['Nome'][:80]} - {p['Prezzo']}€ da {p['Vecchio']}€ (-{p['Sconto%']}%) Punteggio {p['PunteggioQP']} Stelle {p['Recensioni']} Rec {p['NumRecensioni']}")
    for e in errori:
        print(f"!!! ERRORE? {e['Nome'][:60]} -{e['Sconto%']}% -> NON PUBBLICARE, A CAPO")
    if top10:
        with open("top10_amazon.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(top10[0].keys()))
            w.writeheader(); w.writerows(top10)
        print(f"Salvati Top10 Amazon in top10_amazon.csv")
    else:
        print("Nessun Top10 questa ora. Normale se Amazon ha bloccato o se vetrina senza prezzi vecchi.")
    return top10, errori

if __name__ == "__main__":
    caccia_amazon_top10()
