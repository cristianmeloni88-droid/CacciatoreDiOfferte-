# SHARDAN AFFILIAZIONI - Jarvis Dashboard
Affiliate Monitor v2.4.1 - Assistente vocale stile Iron Man

## Cosa contiene
- Dashboard HUD con orb centrale animato
- 10 agenti: AMA, AWI, CON, MED, DEC, TEM, ALI, ERR, POST, CAPO
- 7 affiliazioni: Amazon, Awin, Conrad, MediaWorld, Decathlon, Temu, AliExpress
- Prodotti, guadagni reali, cacciatore errori >70%, post IA, voce

## Come usarlo su GitHub Pages
1. Carica tutti i file in un repo pubblico
2. Settings > Pages > Deploy from branch main / root
3. Apri il link Pages in Chrome / Safari
4. Tocca l'orb una volta per sbloccare voce, poi parla: "Ciao Jarvis"

## Struttura
- index.html = dashboard completa
- app.js = logica, calcoli, agenti, voce
- styles.css = stile HUD
- agenti.js = definizione 10 agenti
- prodotti.json = 20 prodotti demo (14 + 3 Temu + 3 AliExpress)
- README.md = questo file

## Collegamenti reali (prossimo passo)
Metti le tue chiavi in config.js: TELEGRAM_TOKEN, GROQ_API_KEY, GOOGLE_SHEET_URL
