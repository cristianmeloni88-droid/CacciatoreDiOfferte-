"""
SHARDAN - POST Telegram - FIX DEFINITIVO V2
PROBLEMA VISTO NEI LOG: POST scartava tutto con "Scarto ... sconto 0.0% <20%"
PERCHE: Amazon non da il vecchio prezzo, quindi sconto = 0, ma il prodotto e buono.
FIX: se vecchio prezzo manca, NON scartare. Posta lo stesso con solo prezzo.
Solo se vecchio prezzo ESISTE e sconto <20%, allora scarta.
"""
import os, csv, requests

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHANNEL = os.environ.get("TELEGRAM_CHANNEL_ID", "")
API = f"https://api.telegram.org/bot{TOKEN}"

def stella_emoji(voto):
    try: v = float(voto or 0)
    except: v = 0
    if v >= 4.5: return "⭐⭐⭐⭐⭐"
    if v >= 4.0: return "⭐⭐⭐⭐"
    if v >= 3.0: return "⭐⭐⭐"
    return "⭐⭐"

def formatta_post(p, posizione):
    nome = (p.get("nome") or "Prodotto")[:120]
    desc = (p.get("descrizione") or "")[:120]
    prezzo = p.get("prezzo") or "?"
    vecchio = (p.get("vecchio") or "").strip()
    sconto = p.get("sconto") or ""
    stelle = stella_emoji(p.get("stelle") or "4.5")
    link = p.get("link") or ""
    riga_prezzo = f"💰 <b>{prezzo}€</b>"
    # Se vecchio prezzo esiste e > prezzo, mostralo
    try:
        if vecchio and float(vecchio) > float(prezzo):
            riga_prezzo += f"  <s>{vecchio}€</s>"
    except: pass
    try:
        s = float(sconto) if sconto not in ("", None) else 0
        if s >= 20:
            riga_prezzo += f"  🔥 <b>-{int(s)}%</b>"
    except: pass
    testo = f"<b>{posizione}. {nome}</b>\n"
    if desc: testo += f"{desc}\n"
    testo += f"{riga_prezzo}\n{stelle}\n"
    if link: testo += f"👉 <a href=\"{link}\">Vedi Offerta</a>"
    return testo[:900]

def invia_post(p, posizione, notifica=True):
    if not TOKEN or not CHANNEL:
        print("Manca TELEGRAM_BOT_TOKEN o TELEGRAM_CHANNEL_ID")
        return False
    testo = formatta_post(p, posizione)
    img = (p.get("img") or "").strip()
    if img.startswith("http"):
        r = requests.post(f"{API}/sendPhoto", data={"chat_id": CHANNEL, "photo": img, "caption": testo, "parse_mode": "HTML", "disable_notification": not notifica}, timeout=20)
        if r.status_code == 200:
            print(f"✅ Post {posizione} inviato con foto (notifica={notifica})")
            return True
        print(f"Foto fallita, provo solo testo: {r.text[:200]}")
    r = requests.post(f"{API}/sendMessage", data={"chat_id": CHANNEL, "text": testo, "parse_mode": "HTML", "disable_notification": not notifica}, timeout=20)
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
    print(f"POST FIX V2 - Righe lette: {len(rows)}")
    da_postare = []
    da_chiedere = []
    for r in rows:
        nome = r.get("nome","")[:50]
        vecchio = (r.get("vecchio") or "").strip()
        try: s = float(r.get("sconto") or 0)
        except: s = 0
        # REGOLA NUOVA:
        # - Se vecchio prezzo MANCA -> sconto sconosciuto, POSTA LO STESSO
        # - Se vecchio prezzo ESISTE e sconto <20% -> scarta
        # - Se vecchio prezzo ESISTE e sconto >70% -> chiedi a Cristian
        if not vecchio:
            print(f"Tengo {nome} - vecchio prezzo mancante, sconto sconosciuto - POSTO LO STESSO")
            da_postare.append(r)
            continue
        if s < 20:
            print(f"Scarto {nome} sconto {s}% <20% con vecchio prezzo presente")
            continue
        if s > 70:
            da_chiedere.append(r)
            print(f"⚠️ Sconto >70% - NON auto-posto, chiedo a Cristian: {nome}")
            continue
        da_postare.append(r)
    da_postare = da_postare[:10]
    print(f"Posto {len(da_postare)} prodotti, 1 con notifica + 9 silenziosi")
    for i, p in enumerate(da_postare, 1):
        invia_post(p, i, notifica=(i==1))
    if da_chiedere:
        txt = "⚠️ <b>CAPO - Serve il tuo YES/NO</b>\n"
        for p in da_chiedere:
            txt += f"• {p.get('nome','')[:60]} - {p.get('prezzo')}€ sconto {p.get('sconto')}% - {p.get('link','')}\n"
        requests.post(f"{API}/sendMessage", data={"chat_id": CHANNEL, "text": txt, "parse_mode": "HTML"}, timeout=20)

if __name__ == "__main__":
    posta_top10_da_csv()
