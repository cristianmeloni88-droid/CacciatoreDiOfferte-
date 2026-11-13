"""
SHARDAN - Agente NOMI - Riconosce il nome dalla foto - FIX V2
Problema di prima: usava solo 1 modello Groq Vision, e Groq lo ha tolto.
Ora prova 3 modelli in ordine. Se il primo non esiste, prova il secondo.
Se nessuno funziona, lascia il nome vecchio, non inventa.
"""
import csv, os, requests

GROQ_KEY = os.environ.get("GROQ_API_KEY", "")
CSV_FILE = "top10_amazon.csv"

MODELLI_VISION = [
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "meta-llama/llama-4-maverick-17b-128e-instruct",
    "llama-3.2-90b-vision-preview",
]

def nome_e_brutto(nome):
    if not nome: return True
    n = nome.lower()
    if "su 5 stelle" in n: return True
    if "stelle" in n and len(nome) < 30: return True
    return False

def chiedi_a_groq_vision(img_url, prezzo):
    if not GROQ_KEY or not img_url:
        return None
    for modello in MODELLI_VISION:
        try:
            print(f"  Provo modello {modello}...")
            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
                json={
                    "model": modello,
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
            data = r.json()
            if "choices" not in data:
                print(f"  Modello {modello} non disponibile: {str(data)[:150]} - provo prossimo")
                continue
            txt = data["choices"][0]["message"]["content"].strip()
            print(f"  Groq Vision ({modello}) dice: {txt[:100]}")
            if "|" in txt:
                nome, desc = txt.split("|", 1)
                nome = nome.strip()[:100]
                if len(nome) >= 8 and "stelle" not in nome.lower():
                    return nome, desc.strip()[:150]
            return None
        except Exception as e:
            print(f"  Modello {modello} errore: {e} - provo prossimo")
            continue
    print("  Tutti i modelli Vision non disponibili, lascio nome vecchio")
    return None

def main():
    print("=== SHARDAN Agente NOMI - Nome dalla foto - FIX V2 ===")
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
    campi = list(rows[0].keys()) if rows else []
    if "descrizione" not in campi: campi.append("descrizione")
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campi)
        w.writeheader()
        for r in rows: w.writerow(r)
    print(f"\nFatto! Nomi sistemati: {cambiati}/{len(rows)} - Salvato {CSV_FILE}")

if __name__ == "__main__":
    main()
