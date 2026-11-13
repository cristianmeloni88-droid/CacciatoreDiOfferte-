"""
SHARDAN - Agente NOMI - Riconosce il nome dala foto
Idea di Cristian: se Amazon non da il nome, lo ricaviamo dalla foto.

Come funziona:
1. Legge top10_amazon.csv (con nomi tipo "4,5 su 5 stelle")
2. Per ogni riga con nome brutto, prende la foto (colonna img)
3. Manda la foto a Groq Vision (gratis, hai gia la chiave)
4. Groq guarda la foto e dice: nome vero + descrizione corta
5. Riscrive il CSV con i nomi veri

Se Groq non risponde / non hai chiave, lascia il nome vecchio, non inventa.
"""
import csv, os, re, requests

GROQ_KEY = os.environ.get("GROQ_API_KEY", "")
CSV_FILE = "top10_amazon.csv"

def nome_e_brutto(nome):
    if not nome: return True
    n = nome.lower()
    if "su 5 stelle" in n: return True
    if "stelle" in n and len(nome) < 30: return True
    return False

def chiedi_a_groq_vision(img_url, prezzo):
    """Chiede a Groq Vision: che prodotto vedi in questa foto?"""
    if not GROQ_KEY or not img_url:
        return None
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
            json={
                "model": "meta-llama/llama-4-scout-17b-16e-instruct",
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"Guarda questa foto di un prodotto Amazon che costa circa {prezzo} euro. Dimmi SOLO: 1) Nome corto del prodotto in italiano (es: Smart TV Samsung 43 4K, Cuffie Bluetooth Sony, Aspirapolvere Dyson). 2) Una riga di descrizione. Rispondi cosi: NOME | DESCRIZIONE. Non inventare marca se non sei sicuro, usa descrizione generica."},
                        {"type": "image_url", "image_url": {"url": img_url}}
                    ]
                }],
                "max_tokens": 120,
                "temperature": 0.2,
            },
            timeout=25,
        )
        txt = r.json()["choices"][0]["message"]["content"].strip()
        print(f"  Groq Vision dice: {txt[:100]}")
        if "|" in txt:
            nome, desc = txt.split("|", 1)
            nome = nome.strip()[:100]
            # Sicurezza: se Groq dice cose strane, scarta
            if len(nome) >= 8 and "stelle" not in nome.lower():
                return nome, desc.strip()[:150]
    except Exception as e:
        print(f"  Groq Vision errore: {e}")
    return None

def main():
    print("=== SHARDAN Agente NOMI - Nome dalla foto ===")
    if not os.path.exists(CSV_FILE):
        print(f"Non trovo {CSV_FILE}, fai prima girare caccia_amazon_top10.py")
        return
    rows = list(csv.DictReader(open(CSV_FILE, encoding="utf-8")))
    print(f"Righe da controllare: {len(rows)}")
    cambiati = 0
    for r in rows:
        nome = r.get("nome", "")
        if not nome_e_brutto(nome):
            print(f"OK gia buono: {nome[:60]}")
            continue
        print(f"\nDa sistemare: {nome} - {r.get('prezzo')}€ - foto: {str(r.get('img',''))[:80]}")
        ris = chiedi_a_groq_vision(r.get("img",""), r.get("prezzo",""))
        if ris:
            nuovo_nome, desc = ris
            print(f"  -> NUOVO NOME: {nuovo_nome}")
            r["nome"] = nuovo_nome
            if desc: r["descrizione"] = desc
            cambiati += 1
        else:
            print("  -> Lascio nome vecchio, non invento")
    # Riscrivi CSV
    campi = list(rows[0].keys()) if rows else []
    if "descrizione" not in campi: campi.append("descrizione")
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campi)
        w.writeheader()
        for r in rows: w.writerow(r)
    print(f"\nFatto! Nomi sistemati: {cambiati}/{len(rows)} - Salvato {CSV_FILE}")

if __name__ == "__main__":
    main()
