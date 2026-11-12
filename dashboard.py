
# SHARDAN AFFILIAZIONI - Versione Jarvis - dashboard.py per Streamlit
# Questa e' la versione corretta da caricare su GitHub al posto della vecchia Furbo Dashboard
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Shardan Affiliazioni - Jarvis", page_icon="🦊", layout="wide")
# Stile Jarvis HUD scuro cyan
st.markdown("""
<style>
.stApp { background-color: #050b14; color: #e8f6ff; }
h1,h2,h3 { color: #00e5ff !important; font-family: monospace; }
div[data-testid="metric"] { background: rgba(0,229,255,0.08); border: 1px solid #00e5ff; border-radius: 12px; padding: 10px; }
</style>
""", unsafe_allow_html=True)

st.title("🦊 SHARDAN AFFILIAZIONI - J.A.R.V.I.S.")
st.caption("Ciao, sono Jarvis. Tocca un comando qui sotto e ti rispondo. | Stato: IN ASCOLTO... | Squadra: 13 agenti attivi | CAPO: unico manager")

# Comandi Jarvis
col_a, col_b, col_c = st.columns(3)
if col_a.button("🎙️ Quanto ho guadagnato oggi?"):
    st.success("Jarvis: Oggi 41€. Amazon 12€, Awin 18€, Conrad 11€. Sei a +12€ rispetto a ieri.")
if col_b.button("🚨 Ci sono errori di prezzo?"):
    st.warning("Jarvis: 1 possibile errore da controllare. Cuffie da 89.90€ a 8.90€ -90%. Vuoi che lo approvi?")
if col_c.button("📢 Cosa pubblico oggi?"):
    st.info("Jarvis: Top 3 da pubblicare: 1) Batteria LiFePO4, 2) Cuffie Bluetooth, 3) Tenda 3 Persone. Chiedo a CAPO? Sì / No")

if "prodotti" not in st.session_state:
    st.session_state.prodotti = pd.DataFrame([
        {"Nome":"Cuffie Bluetooth","Prezzo":29.90,"Vecchio":89.90,"Categoria":"elettronica","Shop":"MediaWorld","Link":"https://example.com/cuffie","Recensioni":4.5,"Attivo":True,"Agente":"MED_VERIFICA"},
        {"Nome":"Batteria LiFePO4 100Ah","Prezzo":189.00,"Vecchio":249.00,"Categoria":"batterie","Shop":"Conrad","Link":"https://example.com/batteria","Recensioni":4.8,"Attivo":True,"Agente":"CON_VERIFICA"},
        {"Nome":"Tenda 3 Persone","Prezzo":89.90,"Vecchio":119.90,"Categoria":"outdoor","Shop":"Decathlon","Link":"https://example.com/tenda","Recensioni":4.6,"Attivo":True,"Agente":"DEC_VERIFICA"},
        {"Nome":"Caricabatterie USB-C 65W","Prezzo":19.90,"Vecchio":39.90,"Categoria":"elettronica","Shop":"Amazon","Link":"https://example.com/caricatore","Recensioni":4.7,"Attivo":True,"Agente":"AMA_VERIFICA"},
        {"Nome":"Pannello Solare 100W","Prezzo":79.00,"Vecchio":129.00,"Categoria":"batterie","Shop":"Awin","Link":"https://example.com/pannello","Recensioni":4.4,"Attivo":True,"Agente":"AWI_VERIFICA"},
    ])

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🏠 Home","📦 Prodotti","🤖 Squadra IA - 13 Agenti","🚨 Errori Prezzo","✍️ Post IA","💰 Guadagni"])

with tab1:
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Utenti oggi", "128", "+12")
    c2.metric("Click affiliati", "342", "+41")
    c3.metric("Vendite stimate", "18", "+3")
    c4.metric("Guadagni oggi", "41€", "+12€")
    st.info("Jarvis dice: Ieri hanno cercato di più: batteria, tenda, diodo. CAPO consiglia Batteria LiFePO4 per domani.")

with tab2:
    st.header("📦 Prodotti - Modifica e il bot si aggiorna")
    df = st.data_editor(st.session_state.prodotti, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Salva Prodotti"):
        st.session_state.prodotti = df
        st.success("Salvato! Jarvis ha aggiornato gli agenti.")

with tab3:
    st.header("🤖 Squadra IA - 2 per affiliazione + 1 CAPO")
    squadra = pd.DataFrame([
        {"Agente":"AMA_CACCIA","Affiliazione":"Amazon","Ruolo":"Cacciatore","Stato":"✅ Attivo","Ultima azione":"Ha trovato 5 offerte"},
        {"Agente":"AMA_VERIFICA","Affiliazione":"Amazon","Ruolo":"Verificatore","Stato":"✅ Attivo","Ultima azione":"Ha tenuto 2 migliori"},
        {"Agente":"AWI_CACCIA","Affiliazione":"Awin","Ruolo":"Cacciatore","Stato":"✅ Attivo","Ultima azione":"Ha trovato 5 prodotti"},
        {"Agente":"AWI_VERIFICA","Affiliazione":"Awin","Ruolo":"Verificatore","Stato":"✅ Attivo","Ultima azione":"Controllata commissione"},
        {"Agente":"CON_CACCIA","Affiliazione":"Conrad","Ruolo":"Cacciatore","Stato":"✅ Attivo","Ultima azione":"Ha trovato 5 batterie"},
        {"Agente":"CON_VERIFICA","Affiliazione":"Conrad","Ruolo":"Verificatore","Stato":"✅ Attivo","Ultima azione":"Verificati dati tecnici"},
        {"Agente":"MED_CACCIA","Affiliazione":"MediaWorld","Ruolo":"Cacciatore","Stato":"✅ Attivo","Ultima azione":"Ha trovato 5 cuffie"},
        {"Agente":"MED_VERIFICA","Affiliazione":"MediaWorld","Ruolo":"Verificatore","Stato":"✅ Attivo","Ultima azione":"Confronto con Amazon OK"},
        {"Agente":"DEC_CACCIA","Affiliazione":"Decathlon","Ruolo":"Cacciatore","Stato":"✅ Attivo","Ultima azione":"Ha trovato 5 tende"},
        {"Agente":"DEC_VERIFICA","Affiliazione":"Decathlon","Ruolo":"Verificatore","Stato":"✅ Attivo","Ultima azione":"Verificati peso/impermeabilità"},
        {"Agente":"ERR","Affiliazione":"Supporto","Ruolo":"Guardiano errori","Stato":"🔴 1 da controllare","Ultima azione":"Segnalato -90%"},
        {"Agente":"POST","Affiliazione":"Supporto","Ruolo":"Copywriter","Stato":"✍️ 3 post pronti","Ultima azione":"3 post creati"},
        {"Agente":"CAPO","Affiliazione":"Manager","Ruolo":"UNICO MANAGER","Stato":"👑 In attesa Sì/No","Ultima azione":"Riepilogo 08:00 pronto"},
    ])
    st.dataframe(squadra, use_container_width=True)
    st.caption("Flusso: Cacciatore trova 5 -> Verificatore tiene 2 -> CAPO ti chiede Sì/No. Solo CAPO parla con te.")

with tab4:
    st.header("🚨 Cacciatore di Errori di Prezzo")
    df = st.session_state.prodotti.copy()
    df["Sconto %"] = ((df["Vecchio"]-df["Prezzo"])/df["Vecchio"]*100).round(1)
    st.dataframe(df, use_container_width=True)
    st.warning("Esempio errore: Se Cuffie da 89.90€ vanno a 8.90€ (-90%) appariranno qui in rosso. Jarvis ti avvisa, tu approvi.")
    c1,c2 = st.columns(2)
    if c1.button("✅ Approva e Pubblica"): st.success("Pubblicato sul canale!")
    if c2.button("❌ Ignora"): st.info("Ignorato")

with tab5:
    st.header("✍️ Post IA - Jarvis + POST")
    prod = st.selectbox("Scegli prodotto", st.session_state.prodotti["Nome"].tolist())
    if st.button("Genera 3 Post"):
        riga = st.session_state.prodotti[st.session_state.prodotti["Nome"]==prod].iloc[0]
        st.text(f"Telegram Bot: 🔥 OFFERTA! {riga['Nome']} a {riga['Prezzo']}€ invece di {riga['Vecchio']}€\nCome affiliato guadagno dagli acquisti idonei. #ad")
        st.text(f"Canale: {riga['Nome']} finalmente in offerta da {riga['Shop']} a {riga['Prezzo']}€.\nCome affiliato guadagno dagli acquisti idonei. #ad")
        st.text(f"TikTok 15 sec: Non comprare {riga['Nome']} prima di vedere questo! {riga['Prezzo']}€ invece di {riga['Vecchio']}€.\nCome affiliato guadagno dagli acquisti idonei. #ad")

with tab6:
    st.header("💰 Guadagni")
    st.metric("Totale oggi", "41€", "+12€ rispetto a ieri")
    st.bar_chart({"Amazon":12,"Awin":18,"Conrad":11,"MediaWorld":9,"Decathlon":7})
    st.write("Top prodotto: Batteria LiFePO4 | Categoria top: batterie | Shop che paga di più: Awin")
