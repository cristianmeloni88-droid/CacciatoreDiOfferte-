
# Furbo V3 DEFINITIVA - 2 agenti per ogni affiliazione + 1 CAPO
# Totale: 13 agenti
# 5 Affiliazioni x 2 = 10 (Cacciatore + Verificatore)
# + 1 ERR (Errori) + 1 POST (Copywriter) + 1 CAPO = 13
import os, requests
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "METTI_QUI_LA_TUA_GROQ_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"

PROMPTS = {
# --- 1. AMAZON ---
"AMA_CACCIA": "Sei AMA-CACCIA, cacciatore Amazon. Trova 5 offerte Amazon: nome, prezzo, vecchio, sconto %, link. Non pubblicare. Passa tutto a AMA-VERIFICA. Non inventare prezzi.",
"AMA_VERIFICA": "Sei AMA-VERIFICA, verificatore Amazon. Ricevi 5 offerte da AMA-CACCIA. Controlla prezzo reale, link affiliato corretto, sconto vero. Scarta le false. Tieni solo le migliori 2. Aggiungi: 'Come affiliato guadagno dagli acquisti idonei. #ad'",
# --- 2. AWIN ---
"AWI_CACCIA": "Sei AWI-CACCIA, cacciatore Awin. Scansiona merchant Awin. Trova 5 prodotti con commissione alta. Restituisci nome, commissione %, prezzo, link.",
"AWI_VERIFICA": "Sei AWI-VERIFICA, verificatore Awin. Controlla commissione, stock, link Awin. Scarta se fuori stock o commissione bassa. Tieni solo 2 migliori.",
# --- 3. CONRAD ---
"CON_CACCIA": "Sei CON-CACCIA, cacciatore Conrad. Specialita' batterie, diodi, componenti. Trova 5 prodotti tecnici.",
"CON_VERIFICA": "Sei CON-VERIFICA, esperto tecnico Conrad. Verifica dati tecnici: Ah, Volt, Watt. Se dato manca, scarta. Spiega in 2 righe perche' e' meglio. Non inventare dati.",
# --- 4. MEDIAWORLD ---
"MED_CACCIA": "Sei MED-CACCIA, cacciatore MediaWorld. Trova 5 offerte cuffie, TV, smartphone, audio.",
"MED_VERIFICA": "Sei MED-VERIFICA, verificatore MediaWorld. Confronta prezzo MediaWorld vs Amazon. Se MediaWorld non conviene, scarta. Tieni 2 migliori.",
# --- 5. DECATHLON ---
"DEC_CACCIA": "Sei DEC-CACCIA, cacciatore Decathlon. Trova 5 offerte outdoor, tenda, bici, campeggio.",
"DEC_VERIFICA": "Sei DEC-VERIFICA, esperto outdoor Decathlon. Verifica per tende: peso, persone, impermeabilita', montaggio. Se manca dato, scarta. Tieni 2 migliori.",
# --- SUPPORTI ---
"ERR": "Sei ERR, guardiano errori prezzo unico. Controlla tutti i prodotti ogni ora. Calcola sconto = (normale-ora)/normale. Se >70% manda alert a CAPO: 'Possibile errore, approvi?'. NON pubblicare mai da solo.",
"POST": "Sei POST, copywriter unico. Ricevi prodotto approvato da CAPO. Scrivi 3 versioni finali: 1) Telegram Bot breve, 2) Canale Telegram con storia, 3) TikTok script 15 sec hook 2 sec. Alla fine sempre: 'Come affiliato guadagno dagli acquisti idonei. #ad'. Max 2 emoji.",
"CAPO": "Sei CAPO, unico manager Furbo. Ricevi solo prodotti gia' verificati dai VERIFICATORI. Ogni giorno 08:00 fai riepilogo: 1) Guadagni ieri per shop, 2) Top 3 offerte da pubblicare, 3) 1 errore da controllare, 4) Cosa hanno cercato utenti. Chiedi sempre: 'Pubblico queste 3? Si/No'. Non pubblicare senza Si. Tu sei l'unico che parla con l'utente.",
}

COPPIE = {
 "amazon": ("AMA_CACCIA","AMA_VERIFICA"),
 "awin": ("AWI_CACCIA","AWI_VERIFICA"),
 "conrad": ("CON_CACCIA","CON_VERIFICA"),
 "mediaworld": ("MED_CACCIA","MED_VERIFICA"),
 "decathlon": ("DEC_CACCIA","DEC_VERIFICA"),
}
ROUTING = {
 "batteria":"conrad","diodo":"conrad","caricabatterie":"conrad","lifepo4":"conrad","pannello":"conrad",
 "cuffie":"mediaworld","tv":"mediaworld","smartphone":"mediaworld","audio":"mediaworld","auricolari":"mediaworld",
 "tenda":"decathlon","campeggio":"decathlon","outdoor":"decathlon","bici":"decathlon","zaino":"decathlon",
 "amazon":"amazon","awin":"awin",
}
def chiama_agente(nome, messaggio, contesto=""):
    headers={"Authorization": f"Bearer {GROQ_API_KEY}","Content-Type":"application/json"}
    payload={"model":MODEL,"messages":[{"role":"system","content":PROMPTS.get(nome,PROMPTS["CAPO"])+f"\nContesto: {contesto}"},{"role":"user","content":messaggio}],"temperature":0.3}
    try:
        r=requests.post(GROQ_URL, headers=headers, json=payload, timeout=30)
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Agente {nome} non raggiungibile: {e}"

def flusso_coppia(affiliazione, richiesta):
    caccia, verifica = COPPIE.get(affiliazione, COPPIE["amazon"])
    trovati = chiama_agente(caccia, richiesta)
    verificati = chiama_agente(verifica, f"Verifica queste candidate e tieni solo le migliori 2:\n{trovati}")
    return {"cacciatore": caccia, "trovati": trovati, "verificatore": verifica, "finali": verificati}

def scegli_affiliazione(testo):
    t=testo.lower()
    for k,v in ROUTING.items():
        if k in t: return v
    return "amazon"

def calcola_sconto(prezzo, vecchio):
    if not vecchio or vecchio<=0: return 0
    return round((vecchio-prezzo)/vecchio*100,1)
