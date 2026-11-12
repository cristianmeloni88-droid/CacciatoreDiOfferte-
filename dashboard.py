
# Furbo Dashboard - Streamlit - Livello 2
# Avvio: streamlit run dashboard.py
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Furbo Dashboard", page_icon="🦊", layout="wide")
st.title("🦊 Furbo Dashboard - Gestisci Tutto")

# Dati demo - sostituiti da Google Sheets / Supabase in produzione
if "prodotti" not in st.session_state:
    st.session_state.prodotti = pd.DataFrame([
        {"Nome":"Cuffie Bluetooth","Prezzo":29.90,"Vecchio":89.90,"Categoria":"elettronica","Shop":"MediaWorld","Link":"https://example.com/cuffie","Recensioni":4.5,"Attivo":True,"Agente":"MED"},
        {"Nome":"Batteria LiFePO4 100Ah","Prezzo":189.00,"Vecchio":249.00,"Categoria":"batterie","Shop":"Conrad","Link":"https://example.com/batteria","Recensioni":4.8,"Attivo":True,"Agente":"CON"},
        {"Nome":"Tenda 3 Persone","Prezzo":89.90,"Vecchio":119.90,"Categoria":"outdoor","Shop":"Decathlon","Link":"https://example.com/tenda","Recensioni":4.6,"Attivo":True,"Agente":"DEC"},
        {"Nome":"Caricabatterie USB-C 65W","Prezzo":19.90,"Vecchio":39.90,"Categoria":"elettronica","Shop":"Amazon","Link":"https://example.com/caricatore","Recensioni":4.7,"Attivo":True,"Agente":"AMA"},
        {"Nome":"Diodo Schottky 10A","Prezzo":4.90,"Vecchio":9.90,"Categoria":"componenti","Shop":"Conrad","Link":"https://example.com/diodo","Recensioni":4.9,"Attivo":False,"Agente":"CON"},
        {"Nome":"Pannello Solare 100W","Prezzo":79.00,"Vecchio":129.00,"Categoria":"batterie","Shop":"Awin","Link":"https://example.com/pannello","Recensioni":4.4,"Attivo":True,"Agente":"AWI"},
    ])

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🏠 Home","📦 Prodotti","🚨 Errori Prezzo","✍️ Post IA","💰 Guadagni","🤖 Squadra IA"])

with tab1:
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Utenti oggi", "128", "+12")
    c2.metric("Click affiliati", "342", "+41")
    c3.metric("Vendite stimate", "18", "+3")
    c4.metric("Guadagni oggi", "41€", "+12€")
    st.info("💡 Ieri hanno cercato di più: batteria, tenda, diodo. Metti in evidenza la Batteria LiFePO4 domani.")

with tab2:
    st.header("📦 Prodotti - Modifica e il bot si aggiorna")
    df = st.data_editor(st.session_state.prodotti, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Salva Prodotti"):
        st.session_state.prodotti = df
        st.success("Salvato! Il bot ora usa questi prodotti.")

with tab3:
    st.header("🚨 Cacciatore di Errori di Prezzo")
    df = st.session_state.prodotti.copy()
    df["Sconto %"] = ((df["Vecchio"]-df["Prezzo"])/df["Vecchio"]*100).round(1)
    errori = df[df["Sconto %"]>70]
    if len(errori)>0:
        st.warning(f"{len(errori)} possibili errori trovati!")
        st.dataframe(errori, use_container_width=True)
    else:
        st.success("Nessun errore >70% al momento. Esempio: se Cuffie da 89.90€ vanno a 8.90€ (-90%) appariranno qui.")
        st.dataframe(df, use_container_width=True)
    col1,col2 = st.columns(2)
    if col1.button("✅ Approva e Pubblica sul Canale"): st.success("Pubblicato sul canale Telegram!")
    if col2.button("❌ Ignora"): st.info("Ignorato")

with tab4:
    st.header("✍️ Crea Post con IA")
    prod = st.selectbox("Scegli prodotto", st.session_state.prodotti["Nome"].tolist())
    if st.button("Genera 3 Post"):
        riga = st.session_state.prodotti[st.session_state.prodotti["Nome"]==prod].iloc[0]
        st.subheader("Telegram Bot")
        st.text(f"🔥 OFFERTA! {riga['Nome']} a {riga['Prezzo']}€ invece di {riga['Vecchio']}€\nCome affiliato guadagno dagli acquisti idonei. #ad")
        st.subheader("Canale Telegram")
        st.text(f"Stavo cercando da giorni... {riga['Nome']} finalmente in offerta. {riga['Prezzo']}€ invece di {riga['Vecchio']}€ da {riga['Shop']}.\nCome affiliato guadagno dagli acquisti idonei. #ad")
        st.subheader("TikTok - Script 15 sec")
        st.text(f"HOOK: Non comprare {riga['Nome']} prima di vedere questo!\nPrezzo: {riga['Prezzo']}€ invece di {riga['Vecchio']}€. Link in bio.\nCome affiliato guadagno dagli acquisti idonei. #ad")
        if st.button("📤 Pubblica su Telegram"): st.success("Pubblicato!")

with tab5:
    st.header("💰 Guadagni")
    st.metric("Totale oggi", "41€", "+12€ rispetto a ieri")
    st.bar_chart({"Amazon":12,"Awin":18,"Conrad":11})
    st.write("Prodotto che vende di più: Batteria LiFePO4 | Categoria top: batterie | Shop che paga di più: Awin")

with tab6:
    st.header("🤖 Squadra IA - Chi sta lavorando")
    squadra = pd.DataFrame([
        {"Agente":"AMA - Amazon","Stato":"✅ Attivo","Ultimo controllo":"10 min fa","Risultato":"2 offerte trovate"},
        {"Agente":"AWI - Awin","Stato":"✅ Attivo","Ultimo controllo":"1 ora fa","Risultato":"3 prodotti pronti"},
        {"Agente":"CON - Conrad","Stato":"✅ Attivo","Ultimo controllo":"5 min fa","Risultato":"Batteria in evidenza"},
        {"Agente":"MED - MediaWorld","Stato":"✅ Attivo","Ultimo controllo":"20 min fa","Risultato":"Cuffie -66%"},
        {"Agente":"DEC - Decathlon","Stato":"✅ Attivo","Ultimo controllo":"30 min fa","Risultato":"Tenda pronta"},
        {"Agente":"ERR - Errori","Stato":"🔴 1 da controllare","Ultimo controllo":"Ora","Risultato":"Controlla tab Errori"},
        {"Agente":"POST - Copywriter","Stato":"✍️ 3 post pronti","Ultimo controllo":"Ora","Risultato":"Vai a tab Post IA"},
        {"Agente":"CAPO - Manager","Stato":"👑 In attesa tuo Sì/No","Ultimo controllo":"08:00","Risultato":"Riepilogo pronto"},
    ])
    st.dataframe(squadra, use_container_width=True)
    if st.button("Chiedi a CAPO il riepilogo di oggi"):
        st.success("CAPO: 128 utenti oggi, 41€ guadagnati, Top 3: Batteria, Cuffie, Tenda. Pubblico queste 3? Si/No")
