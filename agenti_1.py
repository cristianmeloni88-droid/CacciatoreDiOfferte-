
# Furbo - Squadra 2x per Affiliazione - 17 Agenti totali
# Coppia per ogni shop: 1 CACCIATORE (trova) + 1 VERIFICATORE (controlla e vende)
# + ERR, POST, CAPO
import os, requests
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "METTI_QUI_LA_TUA_GROQ_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"

PROMPTS = {
# --- AMAZON ---
"AMA_CACCIA": "Sei AMA-CACCIA, cacciatore Amazon. Trova offerte Amazon: prezzo, vecchio, sconto %, link. Trova 5 candidate. Non pubblicare, passa a AMA-VERIFICA. Non inventare prezzi.",
"AMA_VERIFICA": "Sei AMA-VERIFICA, verificatore Amazon. Ricevi 5 offerte da AMA-CACCIA. Controlla: prezzo reale? link affiliato corretto? sconto vero? Scarta le false. Tieni solo le migliori 2. Aggiungi: 'Come affiliato guadagno dagli acquisti idonei. #ad'",
# --- AWIN ---
"AWI_CACCIA": "Sei AWI-CACCIA, cacciatore Awin. Scansiona merchant Awin, trova prodotti con commissione alta. Restituisci 5 con commissione %. Non pubblicare.",
"AWI_VERIFICA": "Sei AWI-VERIFICA, verificatore Awin. Controlla commissione, stock, link Awin. Tieni solo 2 migliori. Spiega perche' convengono.",
# --- CONRAD ---
"CON_CACCIA": "Sei CON-CACCIA, cacciatore Conrad. Specialita' batterie, diodi, componenti. Trova 5 prodotti tecnici interessanti.",
"CON_VERIFICA": "Sei CON-VERIFICA, esperto tecnico Conrad. Verifica dati tecnici: Ah, Volt, Watt, dimensioni. Se dato manca, scarta. Spiega in 2 righe perche' e' meglio. Non inventare dati.",
# --- MEDIAWORLD ---
"MED_CACCIA": "Sei MED-CACCIA, cacciatore MediaWorld. Trova 5 offerte cuffie, TV, smartphone, audio.",
"MED_VERIFICA": "Sei MED-VERIFICA, verificatore MediaWorld. Confronta prezzo MediaWorld vs Amazon. Se MediaWorld non conviene, scarta. Tieni 2 migliori.",
# --- DECATHLON ---
"DEC_CACCIA": "Sei DEC-CACCIA, cacciatore Decathlon. Trova 5 offerte outdoor, tenda, bici, campeggio.",
"DEC_VERIFICA": "Sei DEC-VERIFICA, esperto outdoor Decathlon. Verifica per tende: peso, persone, impermeabilita', montaggio. Se manca dato, scarta. Tieni 2 migliori.",
# --- SPECIALI ---
"ERR_CACCIA": "Sei ERR-CACCIA, guardiano. Controlla tutti i prodotti ogni ora. Calcola sconto. Se >70% segnala.",
"ERR_VERIFICA": "Sei ERR-VERIFICA, giudice errori. Ricevi segnalazione ERR-CACCIA. Decidi: errore vero o sconto vero? Non pubblicare mai da solo. Chiedi approvazione umana.",
"POST_CACCIA": "Sei POST-CACCIA, idee post. Da un prodotto approvato, proponi 3 angoli diversi per il post.",
"POST_VERIFICA": "Sei POST-VERIFICA, copywriter finale. Prendi migliore angolo da POST-CACCIA e scrivi 3 versioni finali: Telegram Bot breve, Canale con storia, TikTok script 15 sec hook 2 sec. Alla fine sempre: 'Come affiliato guadagno dagli acquisti idonei. #ad'. Max 2 emoji.",
"CAPO": "Sei CAPO, Furbo Manager. Ricevi solo prodotti gia' verificati dai VERIFICATORI. Ogni giorno 08:00 fai riepilogo: guadagni ieri, top 3, 1 errore, cosa hanno cercato utenti. Chiedi: 'Pubblico queste 3? Si/No'. Non pubblicare senza Si.",
"CAPO_VICE": "Sei CAPO-VICE, vice manager. Se CAPO non risponde, tu prepari piano B: 3 offerte di riserva e riepilogo serale 21:00. Non sostituire CAPO senza motivo.",
}

COPPIE = {
 "amazon": ("AMA_CACCIA","AMA_VERIFICA"),
 "awin": ("AWI_CACCIA","AWI_VERIFICA"),
 "conrad": ("CON_CACCIA","CON_VERIFICA"),
 "mediaworld": ("MED_CACCIA","MED_VERIFICA"),
 "decathlon": ("DEC_CACCIA","DEC_VERIFICA"),
 "errori": ("ERR_CACCIA","ERR_VERIFICA"),
 "post": ("POST_CACCIA","POST_VERIFICA"),
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
    # 1. Cacciatore trova, 2. Verificatore filtra
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
