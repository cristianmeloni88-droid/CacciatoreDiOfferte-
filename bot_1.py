
# bot.py - Telegram Bot collegato a Squadra Furbo
# pip install python-telegram-bot groq
import os
from agenti import chiama_agente, scegli_agente, calcola_sconto
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "METTI_QUI_TOKEN_BOTFATHER")

# Esempio di handler - integra nel tuo bot.py esistente
def gestisci_messaggio(testo_utente):
    agente = scegli_agente(testo_utente)
    risposta = chiama_agente(agente, testo_utente)
    return f"[{agente}] {risposta}"

if __name__=="__main__":
    print(gestisci_messaggio("cerco una batteria lifepo4"))
    print(gestisci_messaggio("cuffie bluetooth in offerta?"))
