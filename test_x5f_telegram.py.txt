"""
TEST Telegram - Manda 1 messaggio di prova
"""
import os, requests
TOKEN=os.environ.get("TELEGRAM_BOT_TOKEN","")
CHANNEL=os.environ.get("TELEGRAM_CHANNEL_ID","")
print("TOKEN presente:", "SI" if TOKEN else "NO - manca TELEGRAM_BOT_TOKEN!")
print("CHANNEL:", repr(CHANNEL))
API=f"https://api.telegram.org/bot{TOKEN}"
r=requests.get(f"{API}/getMe", timeout=15)
print("getMe:", r.status_code, r.text[:400])
r2=requests.post(f"{API}/sendMessage", data={"chat_id":CHANNEL,"text":"🔔 TEST BOT - Se vedi questo, Telegram funziona!","parse_mode":"HTML"}, timeout=15)
print("sendMessage:", r2.status_code, r2.text[:600])
if r2.status_code==200:
    print("✅ TEST RIUSCITO - Telegram funziona!")
elif "chat not found" in r2.text:
    print("❌ CHANNEL_ID SBAGLIATO - Devi mettere -100... non il nome!")
elif "forbidden" in r2.text.lower() or "blocked" in r2.text.lower():
    print("❌ BOT NON E ADMIN - Vai nel gruppo e metti il bot come Amministratore!")
elif "unauthorized" in r2.text.lower():
    print("❌ TOKEN SBAGLIATO - Controlla TELEGRAM_BOT_TOKEN!")
else:
    print("❌ Altro errore")
