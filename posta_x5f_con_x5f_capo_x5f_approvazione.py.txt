# SHARDAN - REGOLA FINALE: POST posta SOLO quello che CAPO ha approvato. Alle 18 si chiude.
# FLUSSO UFFICIALE:
# CACCIA trova -> VERIFICA controlla prezzo -> CAPO approva (sicurezza) -> POST posta
# SENZA OK di CAPO, POST NON POSTA NIENTE. Scritto nel codice, non solo a parole.
# ORARI FINALI: 08, 10, 12, 14, 16, 18. Dopo le 18, NIENTE. Silenzio fino a domani 08:00.
# FORMATO PER OGNI POST:
# [Immagine articolo]
# Nome articolo + piccola descrizione
# Prezzo + Vecchio + Sconto
# Stelle
# Link
# NOTIFICHE: 1 con notifica + 9 silenziosi per ogni orario. Totale 6 notifiche al giorno.
import os, requests
from datetime import datetime

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHANNEL = os.getenv("TELEGRAM_CHANNEL_ID", "")

ORARI_FINALI = {
    "08:00": "Amazon",
    "10:00": "Awin",  # dentro: Temu + AliExpress
    "12:00": "Conrad",
    "14:00": "MediaWorld",
    "16:00": "Decathlon",
    "18:00": "BestOfDay",  # chiusura: CAPO sceglie i 10 migliori di tutta la giornata
}

def revisione_sicurezza_capo(p):
    """CAPO: 7 controlli su OGNI offerta. Se non passa, POST non riceve niente."""
    prezzo = float(p.get("Prezzo", 0) or 0)
    vecchio = float(p.get("Vecchio", 0) or 0)
    link = p.get("Link", "")
    punteggio = float(p.get("PunteggioQP", 0) or 0)
    if not prezzo or prezzo <= 0: return False, "Prezzo mancante"
    if not vecchio or vecchio <= prezzo: return False, "Non e offerta"
    sconto = round((vecchio - prezzo) / vecchio * 100, 1)
    p["Sconto%"] = sconto
    if sconto >= 70: return False, f"Sconto {sconto}% troppo alto - possibile errore, chiedi a utente"
    if sconto < 20: return False, f"Sconto {sconto}% troppo basso"
    if not link or "example.com" in link: return False, "Link mancante o finto"
    if punteggio and punteggio < 55: return False, f"Punteggio {punteggio} troppo basso"
    p["ApprovatoDaCAPO"] = True
    return True, f"CAPO OK: {p.get('Nome')} -{sconto}%"

def formatta_post(p):
    nome = p.get("Nome", "")
    descr = (p.get("Descrizione", "") or "")[:80]
    prezzo = p.get("Prezzo", "")
    vecchio = p.get("Vecchio", "")
    sconto = p.get("Sconto%", 0)
    stelle = p.get("Recensioni", "")
    num_rec = p.get("NumRecensioni", "")
    link = p.get("Link", "")
    stelle_emoji = "⭐" * int(float(stelle)) if stelle else "⭐"
    return f"{nome}\n{descr}\n💰 {prezzo}€ invece di {vecchio}€ (-{sconto}%)\n{stelle_emoji} {stelle} ({num_rec} recensioni)\n👉 {link}\nCome affiliato guadagno dagli acquisti idonei. #ad"

def posta_orario(orario, prodotti_candidati):
    """POST posta SOLO dopo OK di CAPO. Dopo le 18:00 non posta piu niente."""
    # Controllo orario: dopo le 18:00, stop
    ora_corrente = datetime.now().strftime("%H:%M")
    if ora_corrente > "18:00" and orario != "18:00":
        print(f"Dopo le 18:00 non si posta piu. Silenzio fino a domani 08:00. Ora: {ora_corrente}")
        return False
    shop = ORARI_FINALI.get(orario, "Generale")
    print(f"=== {orario} - {shop} - CAPO controlla, poi POST posta ===")
    # 1) CAPO approva
    approvati = []
    for p in prodotti_candidati:
        ok, motivo = revisione_sicurezza_capo(p)
        print(f"CAPO: {p.get('Nome')} -> {'OK' if ok else 'BLOCCATO: ' + motivo}")
        if ok: approvati.append(p)
    if not approvati:
        print(f"{shop} {orario}: CAPO non ha approvato niente, POST non posta niente")
        return False
    # 2) POST posta solo gli approvati, max 10, 1 con notifica + 9 silenziosi
    approvati = approvati[:10]
    for i, p in enumerate(approvati, 1):
        silenzioso = (i != 1)  # Solo il primo fa ding
        caption = formatta_post(p)
        img = p.get("Immagine", "") or p.get("ImageUrl", "")
        ok_invio = False
        if img and img.startswith("http"):
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
            try:
                r = requests.post(url, json={"chat_id": TELEGRAM_CHANNEL, "photo": img, "caption": caption[:1024], "disable_notification": silenzioso}, timeout=15)
                ok_invio = r.status_code == 200
            except Exception as e: print(f"Errore foto: {e}")
        if not ok_invio:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            try:
                r = requests.post(url, json={"chat_id": TELEGRAM_CHANNEL, "text": caption, "disable_notification": silenzioso}, timeout=15)
                ok_invio = r.status_code == 200
            except Exception as e: print(f"Errore testo: {e}")
        print(f"{i}/10 {p.get('Nome','')[:50]} - Notifica: {'NO silenzioso' if silenzioso else 'SI ding'} - Inviato: {ok_invio}")
    if orario == "18:00":
        print("=== CHIUSURA 18:00 - Best of the Day postato. Non si posta piu niente fino a domani 08:00. ===")
    return True

if __name__ == "__main__":
    # ESEMPIO
    esempio = [
        {"Nome": "Cuffie Bluetooth", "Descrizione": "Cuffie wireless con cancellazione rumore, 30h batteria", "Prezzo": 29.90, "Vecchio": 89.90, "PunteggioQP": 84, "Recensioni": 4.7, "NumRecensioni": 1250, "Link": "https://example.com/cuffie", "Immagine": "https://example.com/cuffie.jpg"},
        {"Nome": "Cuffie Sospette -90%", "Descrizione": "Prezzo troppo basso", "Prezzo": 8.90, "Vecchio": 89.90, "PunteggioQP": 90, "Recensioni": 4.5, "NumRecensioni": 100, "Link": "https://example.com/sospette", "Immagine": ""},
    ]
    posta_orario("08:00", esempio)
