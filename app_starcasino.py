import streamlit as st
from datetime import time
import promo


st.set_page_config(
    page_title="STARCASINO CSV",
    layout="wide"
)

st.title("Estrazioni Conti per promozione - STARCASINO")

st.write("Inserisci i filtri e poi genera il CSV.")

st.info(
    "Output CSV: id_ticket, cf, num_conto, nome_commerciale, des_stato, "
    "data_ora_vend, Mercato, Importo Giocato, Importo Vincita Potenziale"
)

# =========================================================
# INTERFACCIA FILTRI
# =========================================================

data_vendita_da = st.date_input(
    "Data vendita da",
    value=None,
    format="DD/MM/YYYY"
)

ora_vendita_da = st.time_input(
    "Ora vendita da",
    value=time(0, 0)
)

betradar_input = st.text_area(
    "Betradar ID separati da virgola",
    value="61526570,61061655,61624622"
)

quota_min = st.number_input(
    "Quota minima su tutti gli eventi",
    min_value=0.0,
    value=1.5,
    step=0.1,
    format="%.2f"
)

is_sistema = st.selectbox(
    "Tipo ticket",
    options=[0, 1],
    format_func=lambda x: (
        "Solo ticket singoli - is_sistema=0"
        if x == 0
        else "Solo sistemi - is_sistema=1"
    )
)

cf_input = st.text_input(
    "CF specifico opzionale",
    value=""
)

# =========================================================
# NUOVI FILTRI
# =========================================================

mercato_input = st.text_input(
    "Mercato opzionale - des_scom, esempio 1X2",
    value=""
)

importo_giocato_min = st.number_input(
    "Importo Giocato minimo opzionale",
    min_value=0.0,
    value=0.0,
    step=1.0,
    format="%.2f"
)

importo_giocato_max = st.number_input(
    "Importo Giocato massimo opzionale - lascia 0 per non applicare limite massimo",
    min_value=0.0,
    value=0.0,
    step=1.0,
    format="%.2f"
)

# =========================================================
# BOTTONE GENERA
# =========================================================

if st.button("Genera CSV"):

    if data_vendita_da is None:
        st.error("Devi inserire una data vendita da cui iniziare l'estrazione.")
        st.stop()

    data_vendita_da_str = (
        f"{data_vendita_da.strftime('%Y-%m-%d')} "
        f"{ora_vendita_da.strftime('%H:%M:%S')}"
    )

    betradar_list = [
        x.strip()
        for x in betradar_input.split(",")
        if x.strip()
    ]

    if not betradar_list:
        st.error("Devi inserire almeno un betradar_id.")
        st.stop()

    # Passo i valori inseriti dall'interfaccia a promo.py
    promo.DATA_VENDITA_DA = data_vendita_da_str
    promo.BETRADAR_ID_LIST = betradar_list
    promo.QUOTA_MIN_TUTTI_EVENTI = float(quota_min)
    promo.IS_SISTEMA = int(is_sistema)
    promo.CF = cf_input.strip().upper() if cf_input.strip() else None

    st.info("Estrazione dati in corso...")

    st.write(f"Data vendita da: {promo.DATA_VENDITA_DA}")
    st.write(f"Betradar richiesti: {', '.join(betradar_list)}")
    st.write(f"Numero eventi richiesto: {len(betradar_list)}")
    st.write(f"Quota minima: {promo.QUOTA_MIN_TUTTI_EVENTI}")
    st.write(f"is_sistema: {promo.IS_SISTEMA}")

    if promo.CF:
        st.write(f"CF filtrato: {promo.CF}")

    if mercato_input.strip():
        st.write(f"Mercato filtrato: {mercato_input.strip()}")

    if importo_giocato_min > 0:
        st.write(f"Importo Giocato minimo: {importo_giocato_min}")

    if importo_giocato_max > 0:
        st.write(f"Importo Giocato massimo: {importo_giocato_max}")

    # =====================================================
    # ESTRAZIONE DATI
    # =====================================================

    try:
        df = promo.estrai_dati()
    except Exception as e:
        st.error("Errore durante l'estrazione dati dal database.")
        st.exception(e)
        st.stop()

    if df is None or df.empty:
        st.error("Nessun dato trovato dal database.")
        st.stop()

    st.success(f"Righe lette dal database: {len(df)}")

    # =====================================================
    # NORMALIZZAZIONE E FILTRO QUOTA
    # =====================================================

    try:
        df = promo.normalizza_output(df)
        df = promo.applica_filtro_quota_tutti_eventi(df)
    except Exception as e:
        st.error("Errore durante la normalizzazione o il filtro quota.")
        st.exception(e)
        st.stop()

    if df is None or df.empty:
        st.warning("Nessun ticket valido dopo il filtro quota.")
        st.stop()

    # =====================================================
    # FILTRO MERCATO
    # =====================================================

    if mercato_input.strip():
        mercati_filtrati = [
            x.strip().upper()
            for x in mercato_input.split(",")
            if x.strip()
        ]

        df["des_scom"] = df["des_scom"].fillna("").astype(str).str.strip()

        df = df[
            df["des_scom"].str.upper().isin(mercati_filtrati)
        ].copy()

        if df.empty:
            st.warning("Nessun ticket trovato dopo il filtro Mercato.")
            st.stop()

    # =====================================================
    # FILTRO IMPORTO GIOCATO
    # =====================================================

    if importo_giocato_min > 0:
        df = df[df["importo_pagato"] >= float(importo_giocato_min)].copy()

    if importo_giocato_max > 0:
        df = df[df["importo_pagato"] <= float(importo_giocato_max)].copy()

    if df.empty:
        st.warning("Nessun ticket trovato dopo il filtro Importo Giocato.")
        st.stop()

    # =====================================================
    # CREAZIONE OUTPUT TICKET / CF
    # =====================================================

    colonne_ticket = [
        "id_ticket",
        "cf",
        "num_conto",
        "nome_commerciale",
        "des_stato",
        "data_ora_vend",
        "des_scom",
        "importo_pagato",
        "importo_vincita_potenziale",
    ]

    colonne_mancanti = [
        col for col in colonne_ticket
        if col not in df.columns
    ]

    if colonne_mancanti:
        st.error("Mancano alcune colonne necessarie nel dataframe finale:")
        st.write(colonne_mancanti)

        st.write("Colonne disponibili nel dataframe:")
        st.write(list(df.columns))

        st.stop()

    ticket_cf = (
        df[colonne_ticket]
        .drop_duplicates(subset=["id_ticket", "cf"])
        .sort_values(by=["nome_commerciale", "cf", "id_ticket"])
        .reset_index(drop=True)
    )

    ticket_cf = ticket_cf.rename(columns={
        "des_scom": "Mercato",
        "importo_pagato": "Importo Giocato",
        "importo_vincita_potenziale": "Importo Vincita Potenziale",
    })

    st.success(f"Ticket trovati: {ticket_cf['id_ticket'].nunique()}")
    st.write(f"CF trovati: {ticket_cf['cf'].nunique()}")
    st.write(f"Punti vendita trovati: {ticket_cf['nome_commerciale'].nunique()}")

    st.dataframe(ticket_cf, use_container_width=True)

    csv = ticket_cf.to_csv(
        sep=";",
        index=False,
        decimal=","
    ).encode("utf-8-sig")

    st.download_button(
        label="Scarica CSV ticket",
        data=csv,
        file_name="1_starcasino_ticket_cf_filtrati.csv",
        mime="text/csv",
    )
