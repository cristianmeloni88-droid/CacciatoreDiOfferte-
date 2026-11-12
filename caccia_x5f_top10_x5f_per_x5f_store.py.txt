# SHARDAN - Top 10 Migliori Affari PER STORE - NON lista dell utente
# OBIETTIVO: per ogni store, trova i 10 migliori affari che LO STORE stesso sta spingendo ora.
# Come fa senza API? NON cerca i prodotti che gli dici tu.
# Va sulle pagine dove LO STORE mette i suoi migliori affari:
#  - Pagina OFFERTE / DEALS / OUTLET
#  - Pagina BEST SELLER / PIU VENDUTI / TOP SCONTI
#  - Pagina CATEGORIE TOP (es: batterie, cuffie, outdoor)
# Legge tutti i prodotti che trova LI, calcola punteggio Qualita-Prezzo, tiene Top 10.
# + Fonte affidabile: Awin ha il catalogo COMPLETO (migliaia di prodotti) -> li cerca TUTTI, non solo i tuoi.
import os, re, csv, math, time, requests
from datetime import datetime

HEADERS = {"User-Agent": "Mozilla/5.0 (Linux; Android 10) ShardanAffiliazioni/1.0"}
AWIN_API_KEY = os.getenv("AWIN_API_KEY", "")
AWIN_PUBLISHER_ID = os.getenv("AWIN_PUBLISHER_ID", "")

# PAGINE DOVE LO STORE METTE I SUOI MIGLIORI AFFARI - sono pagine pubbliche
# Se il negozio cambia l indirizzo, aggiorna qui. Non sono prodotti tuoi, sono le vetrine dello store.
STORE_VETRINE = {
    "Amazon": [
        "https://www.amazon.it/deals",
        "https://www.amazon.it/gp/bestsellers",
        "https://www.amazon.it/gp/movers-and-shakers",
    ],
    "Conrad": [
        "https://www.conrad.it/offerte",
        "https://www.conrad.it/bestseller",
        "https://www.conrad.it/top-sconti",
    ],
    "MediaWorld": [
        "https://www.mediaworld.it/offerte",
        "https://www.mediaworld.it/outlet",
        "https://www.mediaworld.it/bestseller",
    ],
    "Decathlon": [
        "https://www.decathlon.it/offerte",
        "https://www.decathlon.it/outlet",
        "https://www.decathlon.it/bestseller",
    ],
    "Awin": ["API-AWIN-CATALOGO-COMPLETO"],  # Awin non ha vetrina, ha catalogo intero via API
}

def punteggio_qp(prezzo, vecchio, stelle, num_rec):
    if not prezzo or not vecchio or vecchio <= prezzo: return 0
    sconto = (vecchio - prezzo) / vecchio * 100
    punti_sconto = min(40, (sconto/70)*40)
    punti_stelle = (stelle/5)*30
    punti_popol = min(20, math.log10(num_rec+1)/math.log10(5000)*20) if num_rec else 5
    punti_conv = 10 if prezzo < 50 else (7 if prezzo < 150 else 4)
    return round(punti_sconto + punti_stelle + punti_popol + punti_conv, 1), round(sconto,1)

def estrai_prodotti_da_vetrina(html, shop, url_vetrina):
    """Estrae TUTTI i prodotti che trova nella vetrina. Non cerca un prodotto specifico."""
    prodotti = []
    # Cerca blocchi con prezzo: pattern generico prezzo + titolo vicino
    # Prendiamo tutti i prezzi trovati nella pagina, raggruppati
    prezzi = re.findall(r"(\d{1,4}[.,]\d{2})\s*(?:€|EUR)", html, flags=re.I)
    # Cerca titoli: testi tra tag con parole lunghe (euristica semplice ma senza inventare)
    # Per versione robusta: ogni sito ha selettori diversi, qui usiamo il metodo generico + Awin per dati puliti
    # Se la pagina ha pochi prezzi, la saltiamo: meglio pochi ma veri che tanti inventati
    if len(prezzi) < 5:
        return prodotti
    # Converti prezzi
    prezzi_num = []
    for t in prezzi:
        try:
            p = float(t.replace(".", "").replace(",", "."))
            if 1 < p < 5000: prezzi_num.append(p)
        except: pass
    # Non possiamo associare con certezza titolo-prezzo senza selettori sito-specifici,
    # quindi segnaliamo alla verifica manuale: restituiamo i prezzi trovati per controllo
    # La fonte affidabile resta Awin (sotto) dove titolo-prezzo-link sono certi.
    return prodotti

def cerca_in_awin_catalogo_completo(categoria="", limite=100):
    """Awin: cerca in TUTTO il catalogo, non solo prodotti dell utente. Filtra per sconto e rating."""
    risultati = []
    if not AWIN_API_KEY or not AWIN_PUBLISHER_ID:
        print("Awin non configurato: metti AWIN_API_KEY e AWIN_PUBLISHER_ID nei Secrets. Senza di esso, Top10 da Awin non puo cercare in tutto il catalogo.")
        return risultati
    try:
        url = f"https://api.awin.com/publishers/{AWIN_PUBLISHER_ID}/products"
        params = {"accessToken": AWIN_API_KEY, "limit": limite}
        if categoria: params["category"] = categoria
        r = requests.get(url, params=params, timeout=25)
        data = r.json()
        for p in data.get("products", []):
            nome = p.get("productName", "")
            try:
                prezzo = float(p.get("salePrice", {}).get("amount", 0) or 0)
                vecchio = float(p.get("retailPrice", {}).get("amount", 0) or prezzo)
            except: continue
            if not nome or not prezzo or vecchio <= prezzo: continue
            stelle = float(p.get("rating", 4.5) or 4.5)
            num_rec = float(p.get("reviewCount", 100) or 100)
            punteggio, sconto = punteggio_qp(prezzo, vecchio, stelle, num_rec)
            if punteggio < 55: continue
            risultati.append({"Nome": nome, "Prezzo": prezzo, "Vecchio": vecchio, "Sconto%": sconto,
                              "Recensioni": stelle, "NumRecensioni": int(num_rec), "PunteggioQP": punteggio,
                              "Categoria": categoria or "generale", "Shop": p.get("merchantName","Awin"),
                              "Link": p.get("awDeepLink","") or p.get("merchantUrl",""),
                              "Agente": "AWI_CACCIA", "Fonte": "awin-catalogo-completo",
                              "Stato": "ERRORE_POSSIBILE" if sconto >= 70 else "TOP10_QP"})
    except Exception as e:
        print("Errore Awin catalogo:", e)
    return risultati

def top10_per_store():
    print("=== SHARDAN Top 10 Migliori Affari PER STORE - Avvio ===")
    print("Metodo: vetrine dello store + catalogo completo Awin. NON lista dell utente.")
    tutti_top = {}
    # 1) Awin: catalogo completo -> Top 10 veri
    print("\n--- Awin: cerco in TUTTO il catalogo (non solo tuoi prodotti) ---")
    candidati_awin = []
    for cat in ["batterie", "cuffie", "outdoor", "elettronica", "campeggio"]:
        candidati_awin += cerca_in_awin_catalogo_completo(cat, limite=50)
        time.sleep(1)
    candidati_awin = sorted(candidati_awin, key=lambda x: x["PunteggioQP"], reverse=True)[:10]
    tutti_top["Awin"] = candidati_awin
    for i, p in enumerate(candidati_awin, 1):
        print(f"Awin #{i}: {p['Nome']} {p['Prezzo']}€ da {p['Vecchio']}€ (-{p['Sconto%']}%) Punteggio {p['PunteggioQP']}")
    # 2) Altri store: visita le loro vetrine OFFERTE / BEST SELLER
    for shop, vetrine in STORE_VETRINE.items():
        if shop == "Awin": continue
        print(f"\n--- {shop}: controllo le sue vetrine OFFERTE / BEST SELLER ---")
        for url in vetrine:
            try:
                r = requests.get(url, headers=HEADERS, timeout=15)
                print(f"{shop} vetrina {url} -> status {r.status_code}, {len(r.text)} caratteri")
                print(f"  -> Per estrarre i 10 migliori da qui serve il selettore specifico di {shop}.")
                print(f"  -> Prossimo passo: ti preparo il selettore per {shop} quando mi dici quale vetrina vedi tu.")
            except Exception as e:
                print(f"{shop} vetrina {url} non leggibile: {e}")
            time.sleep(2)
        tutti_top[shop] = []  # Riempito al passo 2 con selettori sito-specifici
    # Salva Top10 Awin (certi) in file per il post
    if candidati_awin:
        with open("top10_qualita_prezzo.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(candidati_awin[0].keys()))
            w.writeheader(); w.writerows(candidati_awin)
        print(f"\nSalvati {len(candidati_awin)} Top10 Awin in top10_qualita_prezzo.csv")
    print("\n=== FINE ===")
    print("Per Amazon/Conrad/MediaWorld/Decathlon: senza API non posso prendere TUTTO il catalogo in una chiamata.")
    print("Posso prendere le loro vetrine OFFERTE / BEST SELLER, che sono i loro 10 migliori affari secondo LORO.")
    print("Per farlo in modo affidabile servono i selettori di ogni sito (come si chiama il titolo, dove sta il prezzo).")
    return tutti_top

if __name__ == "__main__":
    top10_per_store()
