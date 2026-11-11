
# 🦊 FURBO - Progetto Completo
## Cosa c'è dentro
- agenti.py = 8 agenti (AMA, AWI, CON, MED, DEC, ERR, POST, CAPO) + routing + controllo errori
- dashboard.py = Furbo Dashboard Streamlit con 6 tab (Home, Prodotti, Errori, Post IA, Guadagni, Squadra IA)
- bot.py = esempio collegamento Telegram -> agente giusto
- prodotti.csv = i 14 prodotti di partenza (modifica qui, il bot legge da qui)
- requirements.txt

## Avvio in 5 minuti - 0€
1. pip install -r requirements.txt
2. Crea chiave gratis su groq.com -> mettila in GROQ_API_KEY
3. Crea bot su @BotFather -> metti token in TELEGRAM_TOKEN
4. streamlit run dashboard.py  -> apri dal telefono
5. python bot.py -> test

## Google Sheets Livello 1 (senza codice)
Colonne: Nome | Prezzo | Prezzo Vecchio | Categoria | Shop | Link Affiliato | Recensioni | Attivo | Agente
Formula errore: =SE((C2-B2)/C2>0.7,"⚠️ ERRORE","OK")

## Cosa fare dopo
- Metti i tuoi veri link affiliati in prodotti.csv (sostituisci example.com)
- In dashboard.py collega Supabase quando vuoi passare a Livello 2
- Ricorda: in ogni post metti "Come affiliato guadagno dagli acquisti idonei. #ad"
