"""
SHARDAN - POST Telegram - Formato Ufficiale
Formato deciso da Cristian:
- 10 post per slot
- 1 con notifica + 9 silenziosi
- Ogni post: foto, nome + descrizione corta, prezzo + vecchio prezzo + sconto, stelle, link
- Se piu di 10 righe / troppo lungo: spezza in 2 messaggi
- 18:00 Best of the Day chiusura. Dopo le 18:00 niente.
- CAPO approva prima di POST. Solo offerte approvate.
- Sconto >70% mai auto-post, chiede Yes/No a Cristian
- Sconto <20% scartato, score <55 scartato
"""
import os, csv, requests

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHANNEL = os.environ.get("TELEGRAM_CHANNEL_ID", "")  # es: -1001234567890 o @mio_canale
API = f"https://api.telegram.org/bot{TOKEN}"

def stella_emoji(voto):
    try: v = float(voto or 0)
    except: v = 0
    if v >= 4.5: return "⭐⭐⭐⭐⭐"
    if v >= 4.0: return "⭐⭐⭐⭐"
    if v >= 3.5: return "⭐⭐⭐⭐"
    if v >= 3.0: return "⭐⭐⭐"
    return "⭐⭐"

def formatta_post(p, posizione):
    nome = p.get("nome","Prodotto")[:120]
    desc = p.get("descrizione","")[:120]
    prezzo = p.get("prezzo","?")
    vecchio = p.get("vecchio","")
    sconto = p.get("sconto","")
    stelle = stella_emoji(p.get("stelle","4.5"))
    link = p.get("link","")
    # Riga prezzo
    riga_prezzo = f"💰 <b>{prezzo}€</b>"
    if vecchio:
        try:
            if float(vecchio) > float(prezzo):
                riga_prezzo += f"  <s>{vecchio}€</s>"
        except: pass
    if sconto:
        try:
            s = float(sconto)
            if s >= 20:
                riga_prezzo += f"  🔥 <b>-{int(s)}%</b>"
        except: pass
    testo = f"<b>{posizione}. {nome}</b>\n"
    if desc: testo += f"{desc}\n"
    testo += f"{riga_prezzo}\n{stelle}\n"
    if link: testo += f"👉 <a href=\"{link}\">Vedi Offerta</a>"
    # Telegram limite 4096 caratteri, noi restiamo sotto 900
    return testo[:900]

def invia_post(p, posizione, notifica=True):
    if not TOKEN or not CHANNEL:
        print("Manca TELEGRAM_BOT_TOKEN o TELEGRAM_CHANNEL_ID nei Secrets")
        return False
    testo = formatta_post(p, posizione)
    img = p.get("img","")
    # 1. Se c'e foto, manda foto + didascalia
    if img and img.startswith("http"):
        r = requests.post(f"{API}/sendPhoto", data={
            "chat_id": CHANNEL,
            "photo": img,
            "caption": testo,
            "parse_mode": "HTML",
            "disable_notification": not notifica,
        }, timeout=20)
        if r.status_code == 200:
            print(f"✅ Post {posizione} inviato con foto (notifica={notifica})")
            return True
        print(f"Foto fallita, provo solo testo: {r.text[:200]}")
    # 2. Fallback solo testo
    r = requests.post(f"{API}/sendMessage", data={
        "chat_id": CHANNEL,
        "text": testo,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
        "disable_notification": not notifica,
    }, timeout=20)
    if r.status_code == 200:
        print(f"✅ Post {posizione} inviato solo testo (notifica={notifica})")
        return True
    print(f"❌ Errore invio post {posizione}: {r.text[:300]}")
    return False

def posta_top10_da_csv(csv_file="top10_amazon.csv"):
    if not os.path.exists(csv_file):
        print(f"Non trovo {csv_file}")
        return
    rows = list(csv.DictReader(open(csv_file, encoding="utf-8")))
    # Filtro CAPO: sconto <20% scartato, sconto >70% chiede a Cristian (qui lo salta e lo mette in coda manuale)
    da_postare = []
    da_chiedere = []
    for r in rows:
        try: s = float(r.get("sconto") or 0)
        except: s = 0
        if s < 20: 
            print(f"Scarto {r.get('nome','')[:40]} sconto {s}% <20%")
            continue
        if s > 70:
            da_chiedere.append(r)
            print(f"⚠️ Sconto >70% - NON auto-posto, chiedo a Cristian: {r.get('nome','')[:50]}")
            continue
        da_postare.append(r)
    da_postare = da_postare[:10]
    print(f"Posto {len(da_postare)} prodotti, 1 con notifica + 9 silenziosi")
    for i, p in enumerate(da_postare, 1):
        notifica = (i == 1)  # solo il primo fa suonare, gli altri 9 silenziosi
        invia_post(p, i, notifica=notifica)
    if da_chiedere:
        txt = "⚠️ <b>CAPO - Serve il tuo YES/NO</b>\nQueste offerte hanno sconto >70%, potrebbero essere errori di prezzo:\n"
        for p in da_chiedere:
            txt += f"• {p.get('nome','')[:60]} - {p.get('prezzo')}€ sconto {p.get('sconto')}% - {p.get('link','')}\n"
        txt += "Rispondi YES per postare, NO per scartare."
        requests.post(f"{API}/sendMessage", data={"chat_id": CHANNEL, "text": txt, "parse_mode": "HTML"}, timeout=20)
        print("Inviato messaggio CAPO per offerte >70%")

def posta_best_of_day(tutte_top10):
    # tutte_top10 = lista di dict da tutti gli store, prende il migliore sconto
    if not tutte_top10: return
    try: best = max(tutte_top10, key=lambda x: float(x.get("sconto") or 0))
    except: best = tutte_top10[0]
    testo = f"🏆 <b>BEST OF THE DAY - Chiusura 18:00</b>\n\n{formatta_post(best, 1)}\n\nGrazie per averci seguito oggi! Domani alle 08:00 si ricomincia 🔥"
    requests.post(f"{API}/sendMessage", data={"chat_id": CHANNEL, "text": testo, "parse_mode": "HTML", "disable_notification": False}, timeout=20)
    print("Best of Day inviato")

if __name__ == "__main__":
    posta_top10_da_csv()
