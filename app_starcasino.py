import streamlit as st
from datetime import time
import promo
import promo_5evetswin


# =========================================================
# CONFIGURAZIONE PAGINA
# =========================================================

st.set_page_config(
    page_title="STARCASINO - Gestione Promozioni",
    layout="wide"
)

st.title("Estrazioni Promozioni - STARCASINO")
st.write("Seleziona la promozione da utilizzare e imposta i relativi filtri.")


# =========================================================
# MENU PROMOZIONI
# =========================================================

promozione_selezionata = st.selectbox(
    "Seleziona promozione",
    options=[
        "Promo Betradar attuale",
        "5evetsWin",
    ],
)

st.divider()


# =========================================================
# PROMO 1 - BETRADAR ATTUALE
# =========================================================

if promozione_selezionata == "Promo Betradar attuale":

    st.header("Promo Betradar attuale")

    st.write(
        "Estrazione dei ticket STARCASINO sulla base di una specifica "
        "combinazione di eventi Betradar e dei filtri impostati."
    )

    st.info(
        "Output CSV: id_ticket, cf, num_conto, nome_commerciale, des_stato, "
        "data_ora_vend, Mercato, Importo Giocato, Importo Vincita Potenziale"
    )

    # =====================================================
    # INTERFACCIA FILTRI
    # =====================================================

    data_vendita_da = st.date_input(
        "Data vendita da",
        value=None,
        format="DD/MM/YYYY",
        key="betradar_data_vendita_da",
    )

    ora_vendita_da = st.time_input(
        "Ora vendita da",
        value=time(0, 0),
        key="betradar_ora_vendita_da",
    )

    betradar_input = st.text_area(
        "Betradar ID separati da virgola",
        value="61526570,61061655,61624622",
        key="betradar_id_input",
    )

    quota_min = st.number_input(
        "Quota minima su tutti gli eventi",
        min_value=0.0,
        value=1.5,
        step=0.1,
        format="%.2f",
        key="betradar_quota_min",
    )

    is_sistema = st.selectbox(
        "Tipo ticket",
        options=[0, 1],
        format_func=lambda x: (
            "Solo ticket singoli - is_sistema=0"
            if x == 0
            else "Solo sistemi - is_sistema=1"
        ),
        key="betradar_is_sistema",
    )

    cf_input = st.text_input(
        "CF specifico opzionale",
        value="",
        key="betradar_cf_input",
    )

    mercato_input = st.text_input(
        "Mercato opzionale - des_scom, separa più valori con virgola",
        value="",
        key="betradar_mercato_input",
    )

    importo_giocato_min = st.number_input(
        "Importo Giocato minimo opzionale",
        min_value=0.0,
        value=0.0,
        step=1.0,
        format="%.2f",
        key="betradar_importo_min",
    )

    importo_giocato_max = st.number_input(
        "Importo Giocato massimo opzionale - lascia 0 per non applicare limite massimo",
        min_value=0.0,
        value=0.0,
        step=1.0,
        format="%.2f",
        key="betradar_importo_max",
    )

    # =====================================================
    # BOTTONE GENERA
    # =====================================================

    if st.button("Genera CSV", key="genera_csv_betradar"):

        if data_vendita_da is None:
            st.error("Devi inserire una data vendita da cui iniziare l'estrazione.")
            st.stop()

        data_vendita_da_str = (
            f"{data_vendita_da.strftime('%Y-%m-%d')} "
            f"{ora_vendita_da.strftime('%H:%M:%S')}"
        )

        betradar_list = list(dict.fromkeys(
            x.strip()
            for x in betradar_input.split(",")
            if x.strip()
        ))

        if not betradar_list:
            st.error("Devi inserire almeno un betradar_id.")
            st.stop()

        mercato_list = list(dict.fromkeys(
            x.strip()
            for x in mercato_input.split(",")
            if x.strip()
        ))

        # =============================================
        # PASSAGGIO FILTRI A promo.py
        # =============================================

        promo.DATA_VENDITA_DA = data_vendita_da_str
        promo.BETRADAR_ID_LIST = betradar_list
        promo.QUOTA_MIN_TUTTI_EVENTI = float(quota_min)
        promo.IS_SISTEMA = int(is_sistema)
        promo.CF = cf_input.strip().upper() if cf_input.strip() else None
        promo.DES_SCOM_LIST = mercato_list if mercato_list else None

        st.info("Estrazione dati in corso...")

        st.write(f"Data vendita da: {promo.DATA_VENDITA_DA}")
        st.write(f"Betradar richiesti: {', '.join(betradar_list)}")
        st.write(f"Numero eventi richiesto: {len(betradar_list)}")
        st.write(f"Quota minima: {promo.QUOTA_MIN_TUTTI_EVENTI}")
        st.write(f"is_sistema: {promo.IS_SISTEMA}")
        st.write(
            f"Mercato: "
            f"{promo.DES_SCOM_LIST if promo.DES_SCOM_LIST else 'TUTTI'}"
        )

        if promo.CF:
            st.write(f"CF filtrato: {promo.CF}")

        if importo_giocato_min > 0:
            st.write(f"Importo Giocato minimo: {importo_giocato_min}")

        if importo_giocato_max > 0:
            st.write(f"Importo Giocato massimo: {importo_giocato_max}")

        # =============================================
        # ESTRAZIONE DATI
        # =============================================

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

        # =============================================
        # NORMALIZZAZIONE E FILTRO QUOTA
        # =============================================

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

        # =============================================
        # FILTRO IMPORTO GIOCATO
        # =============================================

        if importo_giocato_min > 0:
            df = df[
                df["importo_pagato"] >= float(importo_giocato_min)
            ].copy()

        if importo_giocato_max > 0:
            df = df[
                df["importo_pagato"] <= float(importo_giocato_max)
            ].copy()

        if df.empty:
            st.warning(
                "Nessun ticket trovato dopo il filtro Importo Giocato."
            )
            st.stop()

        # =============================================
        # CREAZIONE OUTPUT TICKET / CF
        # =============================================

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
            col
            for col in colonne_ticket
            if col not in df.columns
        ]

        if colonne_mancanti:
            st.error(
                "Mancano alcune colonne necessarie nel dataframe finale:"
            )
            st.write(colonne_mancanti)
            st.write("Colonne disponibili nel dataframe:")
            st.write(list(df.columns))
            st.stop()

        ticket_cf = (
            df[colonne_ticket]
            .drop_duplicates(subset=["id_ticket", "cf"])
            .sort_values(
                by=["nome_commerciale", "cf", "id_ticket"]
            )
            .reset_index(drop=True)
        )

        ticket_cf = ticket_cf.rename(columns={
            "des_scom": "Mercato",
            "importo_pagato": "Importo Giocato",
            "importo_vincita_potenziale": "Importo Vincita Potenziale",
        })

        st.success(
            f"Ticket trovati: {ticket_cf['id_ticket'].nunique()}"
        )
        st.write(
            f"CF trovati: {ticket_cf['cf'].nunique()}"
        )
        st.write(
            "Punti vendita trovati: "
            f"{ticket_cf['nome_commerciale'].nunique()}"
        )

        st.dataframe(
            ticket_cf,
            use_container_width=True,
        )

        csv = ticket_cf.to_csv(
            sep=";",
            index=False,
            decimal=",",
        ).encode("utf-8-sig")

        st.download_button(
            label="Scarica CSV ticket",
            data=csv,
            file_name="1_starcasino_ticket_cf_filtrati.csv",
            mime="text/csv",
        )


# =========================================================
# PROMO 2 - 5evetsWin
# =========================================================

elif promozione_selezionata == "5evetsWin":

    st.header("5evetsWin")

    st.write(
        "Estrazione e classificazione dei ticket STARCASINO in base "
        "al numero di eventi vincenti con cod_stato_esito = WI."
    )

    st.info(
        "Il campo Eventi indica il numero esatto di eventi del ticket. "
        "Deve coincidere con il numero di Betradar ID inseriti."
    )

    data_vendita_da = st.date_input(
        "Data vendita da",
        value=None,
        format="DD/MM/YYYY",
        key="5evetswin_data_vendita_da",
    )

    ora_vendita_da = st.time_input(
        "Ora vendita da",
        value=time(0, 0),
        key="5evetswin_ora_vendita_da",
    )

    eventi_max = st.number_input(
        "Eventi",
        min_value=1,
        value=5,
        step=1,
        key="5evetswin_eventi_max",
        help=(
            "Numero massimo di eventi giocati del ticket. "
            "Esempio: 5 = ticket con num_eventi da 1 a 5."
        ),
    )

    betradar_input = st.text_area(
        "Betradar ID separati da virgola",
        value="",
        key="5evetswin_betradar_input",
    )

    quota_min = st.number_input(
        "Quota minima su tutti gli eventi",
        min_value=0.0,
        value=1.5,
        step=0.1,
        format="%.2f",
        key="5evetswin_quota_min",
    )

    is_sistema = st.selectbox(
        "Tipo ticket",
        options=[0, 1],
        format_func=lambda x: (
            "Solo ticket singoli - is_sistema=0"
            if x == 0
            else "Solo sistemi - is_sistema=1"
        ),
        key="5evetswin_is_sistema",
    )

    cf_input = st.text_input(
        "CF specifico opzionale",
        value="",
        key="5evetswin_cf_input",
    )

    mercato_input = st.text_input(
        "Mercato opzionale - des_scom, separa più valori con virgola",
        value="",
        key="5evetswin_mercato_input",
    )

    importo_giocato_min = st.number_input(
        "Importo Giocato minimo opzionale",
        min_value=0.0,
        value=0.0,
        step=1.0,
        format="%.2f",
        key="5evetswin_importo_min",
    )

    importo_giocato_max = st.number_input(
        "Importo Giocato massimo opzionale - lascia 0 per non applicare limite massimo",
        min_value=0.0,
        value=0.0,
        step=1.0,
        format="%.2f",
        key="5evetswin_importo_max",
    )

    if st.button("Genera CSV 5evetsWin", key="genera_csv_5evetswin"):

        if data_vendita_da is None:
            st.error("Devi inserire una data vendita da cui iniziare l'estrazione.")
            st.stop()

        data_vendita_da_str = (
            f"{data_vendita_da.strftime('%Y-%m-%d')} "
            f"{ora_vendita_da.strftime('%H:%M:%S')}"
        )

        betradar_list = list(dict.fromkeys(
            x.strip()
            for x in betradar_input.split(",")
            if x.strip()
        ))

        mercato_list = list(dict.fromkeys(
            x.strip()
            for x in mercato_input.split(",")
            if x.strip()
        ))

        if not betradar_list:
            st.error("Devi inserire almeno un Betradar ID.")
            st.stop()

        if len(betradar_list) != int(eventi_max):
            st.error(
                f"Hai impostato Eventi = {int(eventi_max)}, "
                f"ma hai inserito {len(betradar_list)} Betradar ID. "
                "I due valori devono coincidere."
            )
            st.stop()

        promo_5evetswin.DATA_VENDITA_DA = data_vendita_da_str
        promo_5evetswin.EVENTI = int(eventi_max)
        promo_5evetswin.BETRADAR_ID_LIST = (
            betradar_list if betradar_list else None
        )
        promo_5evetswin.QUOTA_MIN_TUTTI_EVENTI = float(quota_min)
        promo_5evetswin.IS_SISTEMA = int(is_sistema)
        promo_5evetswin.CF = (
            cf_input.strip().upper()
            if cf_input.strip()
            else None
        )
        promo_5evetswin.DES_SCOM_LIST = (
            mercato_list if mercato_list else None
        )

        st.info("Estrazione dati 5evetsWin in corso...")

        st.write(f"Data vendita da: {promo_5evetswin.DATA_VENDITA_DA}")
        st.write(f"Numero massimo eventi: {promo_5evetswin.EVENTI}")
        st.write(
            f"Regola eventi: 1 <= num_eventi <= "
            f"{promo_5evetswin.EVENTI}"
        )
        st.write(
            f"Betradar: "
            f"{', '.join(betradar_list) if betradar_list else 'TUTTI'}"
        )
        st.write(
            f"Quota minima: {promo_5evetswin.QUOTA_MIN_TUTTI_EVENTI}"
        )
        st.write(f"is_sistema: {promo_5evetswin.IS_SISTEMA}")
        st.write(
            f"Mercato: "
            f"{promo_5evetswin.DES_SCOM_LIST if promo_5evetswin.DES_SCOM_LIST else 'TUTTI'}"
        )

        if promo_5evetswin.CF:
            st.write(f"CF filtrato: {promo_5evetswin.CF}")

        if importo_giocato_min > 0:
            st.write(f"Importo Giocato minimo: {importo_giocato_min}")

        if importo_giocato_max > 0:
            st.write(f"Importo Giocato massimo: {importo_giocato_max}")

        try:
            ticket_cf, dettaglio = promo_5evetswin.esegui_estrazione()
        except Exception as e:
            st.error(
                "Errore durante l'estrazione o classificazione 5evetsWin."
            )
            st.exception(e)
            st.stop()

        if ticket_cf is None or ticket_cf.empty:
            st.warning("Nessun ticket trovato con i filtri impostati.")
            st.stop()

        if importo_giocato_min > 0:
            ticket_validi = ticket_cf[
                ticket_cf["Importo Giocato"] >= float(importo_giocato_min)
            ]["id_ticket"]

            ticket_cf = ticket_cf[
                ticket_cf["id_ticket"].isin(ticket_validi)
            ].copy()

            dettaglio = dettaglio[
                dettaglio["id_ticket"].isin(ticket_validi)
            ].copy()

        if importo_giocato_max > 0:
            ticket_validi = ticket_cf[
                ticket_cf["Importo Giocato"] <= float(importo_giocato_max)
            ]["id_ticket"]

            ticket_cf = ticket_cf[
                ticket_cf["id_ticket"].isin(ticket_validi)
            ].copy()

            dettaglio = dettaglio[
                dettaglio["id_ticket"].isin(ticket_validi)
            ].copy()

        if ticket_cf.empty:
            st.warning(
                "Nessun ticket trovato dopo il filtro Importo Giocato."
            )
            st.stop()

        st.success(
            f"Ticket trovati: {ticket_cf['id_ticket'].nunique()}"
        )
        st.write(f"CF trovati: {ticket_cf['cf'].nunique()}")
        st.write(
            "Punti vendita trovati: "
            f"{ticket_cf['nome_commerciale'].nunique()}"
        )

        st.subheader("Riepilogo classificazioni")

        riepilogo_classificazioni = (
            ticket_cf["classificazione_events_win"]
            .value_counts()
            .rename_axis("classificazione_events_win")
            .reset_index(name="numero_ticket")
        )

        st.dataframe(
            riepilogo_classificazioni,
            use_container_width=True,
        )

        st.subheader("Ticket classificati")

        st.dataframe(
            ticket_cf,
            use_container_width=True,
        )

        csv_ticket = ticket_cf.to_csv(
            sep=";",
            index=False,
            decimal=",",
        ).encode("utf-8-sig")

        st.download_button(
            label="Scarica CSV ticket classificati",
            data=csv_ticket,
            file_name="1_5evetswin_ticket_classificati.csv",
            mime="text/csv",
        )

        csv_dettaglio = dettaglio.to_csv(
            sep=";",
            index=False,
            decimal=",",
        ).encode("utf-8-sig")

        st.download_button(
            label="Scarica CSV dettaglio eventi",
            data=csv_dettaglio,
            file_name="2_5evetswin_dettaglio_eventi.csv",
            mime="text/csv",
        )
