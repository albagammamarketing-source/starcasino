import streamlit as st
from datetime import time

import promo
import promo_3moreEvents


# =========================================================
# CONFIGURAZIONE PAGINA
# =========================================================

st.set_page_config(
    page_title="STARCASINO - Gestione Promozioni",
    layout="wide",
)


# =========================================================
# STILE GRAFICO
# =========================================================

st.markdown(
    """
    <style>

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1450px;
    }

    .main-title {
        font-size: 36px;
        font-weight: 800;
        margin-bottom: 4px;
        letter-spacing: -0.5px;
    }

    .main-subtitle {
        font-size: 17px;
        color: #6b7280;
        margin-bottom: 26px;
    }

    .menu-box {
        padding: 16px 18px;
        border-radius: 14px;
        border: 1px solid #d7dce3;
        background: #f8fafc;
        margin-bottom: 10px;
    }

    .menu-title {
        font-size: 18px;
        font-weight: 800;
        margin-bottom: 3px;
    }

    .menu-help {
        font-size: 14px;
        color: #6b7280;
    }

    div[data-baseweb="select"] > div {
        border-radius: 12px !important;
        min-height: 48px;
        font-weight: 700;
        border: 2px solid #2563eb !important;
        background-color: #ffffff;
    }

    .promo-card {
        padding: 20px 22px;
        border-radius: 14px;
        margin: 8px 0 22px 0;
        border: 1px solid;
    }

    .promo-card-title {
        font-size: 22px;
        font-weight: 800;
        margin-bottom: 8px;
    }

    .promo-card-text {
        font-size: 16px;
        line-height: 1.55;
    }

    .promo-betradar {
        background: #eef5ff;
        border-color: #b9d1ff;
        border-left: 6px solid #2563eb;
    }

    .promo-3more {
        background: #eefbf3;
        border-color: #a9dfbd;
        border-left: 6px solid #16a34a;
    }

    label[data-testid="stWidgetLabel"] p {
        font-weight: 700 !important;
    }

    input, textarea {
        border-radius: 10px !important;
    }

    .stButton > button {
        border-radius: 10px;
        font-weight: 800;
        padding: 0.65rem 1.2rem;
    }

    .stDownloadButton > button {
        border-radius: 10px;
        font-weight: 800;
    }

    hr {
        margin-top: 1rem;
        margin-bottom: 1.5rem;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# TESTATA
# =========================================================

st.markdown(
    '<div class="main-title">🎯 Estrazioni Promozioni - STARCASINO</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="main-subtitle">'
    'Seleziona la promozione, configura i filtri e genera il CSV di estrazione.'
    '</div>',
    unsafe_allow_html=True,
)


# =========================================================
# MENU PROMOZIONI
# =========================================================

st.markdown(
    """
    <div class="menu-box">
        <div class="menu-title">📌 Seleziona promozione</div>
        <div class="menu-help">
            Scegli il tipo di estrazione che vuoi eseguire.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

promozione_selezionata = st.selectbox(
    "Seleziona promozione",
    options=[
        "🎯 Promo Betradar attuale",
        "⚽ 3moreEvents",
    ],
    label_visibility="collapsed",
)

st.divider()


# =========================================================
# PROMO 1 - BETRADAR ATTUALE
# =========================================================

if promozione_selezionata == "🎯 Promo Betradar attuale":

    st.markdown(
        """
        <div class="promo-card promo-betradar">
            <div class="promo-card-title">🎯 Promo Betradar attuale</div>
            <div class="promo-card-text">
                <b>Obiettivo:</b> individuare i ticket giocati su una specifica
                combinazione di eventi Betradar e restituire i principali dati
                anagrafici ed economici dei ticket trovati.
                <br><br>
                <b>Output:</b> id_ticket, CF, numero conto, nome commerciale,
                stato ticket, data vendita, mercato, importo giocato e
                vincita potenziale.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # =====================================================
    # FILTRI
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
    # ESTRAZIONE
    # =====================================================

    if st.button(
        "Genera CSV",
        key="genera_csv_betradar",
    ):

        if data_vendita_da is None:
            st.error(
                "Devi inserire una data vendita da cui iniziare l'estrazione."
            )
            st.stop()

        data_vendita_da_str = (
            f"{data_vendita_da.strftime('%Y-%m-%d')} "
            f"{ora_vendita_da.strftime('%H:%M:%S')}"
        )

        betradar_list = list(
            dict.fromkeys(
                x.strip()
                for x in betradar_input.split(",")
                if x.strip()
            )
        )

        if not betradar_list:
            st.error(
                "Devi inserire almeno un betradar_id."
            )
            st.stop()

        mercato_list = list(
            dict.fromkeys(
                x.strip()
                for x in mercato_input.split(",")
                if x.strip()
            )
        )

        promo.DATA_VENDITA_DA = data_vendita_da_str
        promo.BETRADAR_ID_LIST = betradar_list
        promo.QUOTA_MIN_TUTTI_EVENTI = float(quota_min)
        promo.IS_SISTEMA = int(is_sistema)
        promo.CF = (
            cf_input.strip().upper()
            if cf_input.strip()
            else None
        )
        promo.DES_SCOM_LIST = (
            mercato_list
            if mercato_list
            else None
        )

        st.info(
            "Estrazione dati in corso..."
        )

        st.write(
            f"Data vendita da: {promo.DATA_VENDITA_DA}"
        )
        st.write(
            f"Betradar richiesti: {', '.join(betradar_list)}"
        )
        st.write(
            f"Numero eventi richiesto: {len(betradar_list)}"
        )
        st.write(
            f"Quota minima: {promo.QUOTA_MIN_TUTTI_EVENTI}"
        )
        st.write(
            f"is_sistema: {promo.IS_SISTEMA}"
        )
        st.write(
            f"Mercato: "
            f"{promo.DES_SCOM_LIST if promo.DES_SCOM_LIST else 'TUTTI'}"
        )

        if promo.CF:
            st.write(
                f"CF filtrato: {promo.CF}"
            )

        if importo_giocato_min > 0:
            st.write(
                f"Importo Giocato minimo: {importo_giocato_min}"
            )

        if importo_giocato_max > 0:
            st.write(
                f"Importo Giocato massimo: {importo_giocato_max}"
            )

        try:
            df = promo.estrai_dati()

        except Exception as e:
            st.error(
                "Errore durante l'estrazione dati dal database."
            )
            st.exception(e)
            st.stop()

        if df is None or df.empty:
            st.error(
                "Nessun dato trovato dal database."
            )
            st.stop()

        st.success(
            f"Righe lette dal database: {len(df)}"
        )

        try:
            df = promo.normalizza_output(df)
            df = promo.applica_filtro_quota_tutti_eventi(df)

        except Exception as e:
            st.error(
                "Errore durante la normalizzazione o il filtro quota."
            )
            st.exception(e)
            st.stop()

        if df is None or df.empty:
            st.warning(
                "Nessun ticket valido dopo il filtro quota."
            )
            st.stop()

        # =================================================
        # FILTRO IMPORTO GIOCATO
        # =================================================

        if importo_giocato_min > 0:
            df = df[
                df["importo_pagato"]
                >= float(importo_giocato_min)
            ].copy()

        if importo_giocato_max > 0:
            df = df[
                df["importo_pagato"]
                <= float(importo_giocato_max)
            ].copy()

        if df.empty:
            st.warning(
                "Nessun ticket trovato dopo il filtro Importo Giocato."
            )
            st.stop()

        # =================================================
        # OUTPUT
        # =================================================

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
            st.write(
                colonne_mancanti
            )
            st.write(
                "Colonne disponibili nel dataframe:"
            )
            st.write(
                list(df.columns)
            )
            st.stop()

        ticket_cf = (
            df[colonne_ticket]
            .drop_duplicates(
                subset=["id_ticket", "cf"]
            )
            .sort_values(
                by=[
                    "nome_commerciale",
                    "cf",
                    "id_ticket",
                ]
            )
            .reset_index(drop=True)
        )

        ticket_cf = ticket_cf.rename(
            columns={
                "des_scom": "Mercato",
                "importo_pagato": "Importo Giocato",
                "importo_vincita_potenziale":
                    "Importo Vincita Potenziale",
            }
        )

        st.success(
            f"Ticket trovati: "
            f"{ticket_cf['id_ticket'].nunique()}"
        )

        st.write(
            f"CF trovati: "
            f"{ticket_cf['cf'].nunique()}"
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
            key="download_betradar_ticket",
        )


# =========================================================
# PROMO 2 - 3moreEvents
# =========================================================

elif promozione_selezionata == "⚽ 3moreEvents":

    st.markdown(
        """
        <div class="promo-card promo-3more">
            <div class="promo-card-title">⚽ 3moreEvents</div>
            <div class="promo-card-text">
                <b>Obiettivo:</b> individuare i ticket con almeno un determinato
                numero di eventi e applicare filtri sulla quota complessiva
                del ticket e sullo sport.
                <br><br>
                <b>Regola principale:</b>
                <code>num_eventi &gt;= valore impostato</code>.
                Il valore predefinito è <b>3</b>.
                <br><br>
                La quota ticket viene calcolata utilizzando la variabile
                <code>quota</code> presente in <code>Ticket_Detail</code>.
                Gli sport selezionabili sono <b>CALCIO</b> e <b>TENNIS</b>.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # =====================================================
    # FILTRI
    # =====================================================

    data_vendita_da = st.date_input(
        "Data vendita da",
        value=None,
        format="DD/MM/YYYY",
        key="3more_data_vendita_da",
    )

    ora_vendita_da = st.time_input(
        "Ora vendita da",
        value=time(0, 0),
        key="3more_ora_vendita_da",
    )

    numero_eventi_min = st.number_input(
        "Numero Eventi minimo - num_eventi >=",
        min_value=1,
        value=3,
        step=1,
        key="3more_num_eventi_min",
    )

    quota_ticket_min = st.number_input(
        "Quota ticket minima",
        min_value=0.0,
        value=1.0,
        step=0.1,
        format="%.2f",
        key="3more_quota_ticket_min",
        help=(
            "La quota ticket viene calcolata utilizzando "
            "Ticket_Detail.quota."
        ),
    )

    sport_selezionati = st.multiselect(
        "Sport ammessi - des_sport",
        options=[
            "CALCIO",
            "TENNIS",
        ],
        default=[
            "CALCIO",
            "TENNIS",
        ],
        key="3more_des_sport",
        help=(
            "Per impostazione predefinita sono selezionati "
            "CALCIO e TENNIS."
        ),
    )

    is_sistema = st.selectbox(
        "Tipo ticket",
        options=[0, 1],
        format_func=lambda x: (
            "Solo ticket singoli - is_sistema=0"
            if x == 0
            else "Solo sistemi - is_sistema=1"
        ),
        key="3more_is_sistema",
    )

    cf_input = st.text_input(
        "CF specifico opzionale",
        value="",
        key="3more_cf_input",
    )

    mercato_input = st.text_input(
        "Mercato opzionale - des_scom, separa più valori con virgola",
        value="",
        key="3more_mercato_input",
    )

    importo_giocato_min = st.number_input(
        "Importo Giocato minimo opzionale",
        min_value=0.0,
        value=0.0,
        step=1.0,
        format="%.2f",
        key="3more_importo_min",
    )

    importo_giocato_max = st.number_input(
        "Importo Giocato massimo opzionale - lascia 0 per non applicare limite massimo",
        min_value=0.0,
        value=0.0,
        step=1.0,
        format="%.2f",
        key="3more_importo_max",
    )

    # =====================================================
    # ESTRAZIONE
    # =====================================================

    if st.button(
        "Genera CSV 3moreEvents",
        key="genera_csv_3moreEvents",
    ):

        if data_vendita_da is None:
            st.error(
                "Devi inserire una data vendita da cui iniziare l'estrazione."
            )
            st.stop()

        if not sport_selezionati:
            st.error(
                "Devi selezionare almeno uno sport tra CALCIO e TENNIS."
            )
            st.stop()

        data_vendita_da_str = (
            f"{data_vendita_da.strftime('%Y-%m-%d')} "
            f"{ora_vendita_da.strftime('%H:%M:%S')}"
        )

        mercato_list = list(
            dict.fromkeys(
                x.strip()
                for x in mercato_input.split(",")
                if x.strip()
            )
        )

        promo_3moreEvents.DATA_VENDITA_DA = (
            data_vendita_da_str
        )

        promo_3moreEvents.NUM_EVENTI_MIN = (
            int(numero_eventi_min)
        )

        promo_3moreEvents.QUOTA_TICKET_MIN = (
            float(quota_ticket_min)
        )

        promo_3moreEvents.DES_SPORT_LIST = (
            list(sport_selezionati)
        )

        promo_3moreEvents.IS_SISTEMA = (
            int(is_sistema)
        )

        promo_3moreEvents.CF = (
            cf_input.strip().upper()
            if cf_input.strip()
            else None
        )

        promo_3moreEvents.DES_SCOM_LIST = (
            mercato_list
            if mercato_list
            else None
        )

        st.info(
            "Estrazione dati 3moreEvents in corso..."
        )

        st.write(
            f"Data vendita da: "
            f"{promo_3moreEvents.DATA_VENDITA_DA}"
        )

        st.write(
            f"Numero eventi: num_eventi >= "
            f"{promo_3moreEvents.NUM_EVENTI_MIN}"
        )

        st.write(
            f"Quota ticket minima: "
            f"{promo_3moreEvents.QUOTA_TICKET_MIN}"
        )

        st.write(
            f"Sport ammessi: "
            f"{', '.join(promo_3moreEvents.DES_SPORT_LIST)}"
        )

        st.write(
            f"is_sistema: "
            f"{promo_3moreEvents.IS_SISTEMA}"
        )

        st.write(
            f"Mercato: "
            f"{promo_3moreEvents.DES_SCOM_LIST if promo_3moreEvents.DES_SCOM_LIST else 'TUTTI'}"
        )

        if promo_3moreEvents.CF:
            st.write(
                f"CF filtrato: "
                f"{promo_3moreEvents.CF}"
            )

        if importo_giocato_min > 0:
            st.write(
                f"Importo Giocato minimo: "
                f"{importo_giocato_min}"
            )

        if importo_giocato_max > 0:
            st.write(
                f"Importo Giocato massimo: "
                f"{importo_giocato_max}"
            )

        try:
            ticket_cf, dettaglio = (
                promo_3moreEvents.esegui_estrazione()
            )

        except Exception as e:
            st.error(
                "Errore durante l'estrazione 3moreEvents."
            )
            st.exception(e)
            st.stop()

        if ticket_cf is None or ticket_cf.empty:
            st.warning(
                "Nessun ticket trovato con i filtri impostati."
            )
            st.stop()

        # =================================================
        # FILTRO IMPORTO GIOCATO
        # =================================================

        if importo_giocato_min > 0:
            ticket_cf = ticket_cf[
                ticket_cf["Importo Giocato"]
                >= float(importo_giocato_min)
            ].copy()

        if importo_giocato_max > 0:
            ticket_cf = ticket_cf[
                ticket_cf["Importo Giocato"]
                <= float(importo_giocato_max)
            ].copy()

        if ticket_cf.empty:
            st.warning(
                "Nessun ticket trovato dopo il filtro Importo Giocato."
            )
            st.stop()

        # =================================================
        # ALLINEA DETTAGLIO AI TICKET RIMASTI
        # =================================================

        ticket_validi = set(
            ticket_cf["id_ticket"]
            .astype(str)
            .tolist()
        )

        if (
            dettaglio is not None
            and not dettaglio.empty
        ):
            dettaglio = dettaglio[
                dettaglio["id_ticket"]
                .astype(str)
                .isin(ticket_validi)
            ].copy()

        # =================================================
        # RISULTATI
        # =================================================

        st.success(
            f"Ticket trovati: "
            f"{ticket_cf['id_ticket'].nunique()}"
        )

        st.write(
            f"CF trovati: "
            f"{ticket_cf['cf'].nunique()}"
        )

        st.write(
            "Punti vendita trovati: "
            f"{ticket_cf['nome_commerciale'].nunique()}"
        )

        st.subheader(
            "Ticket estratti"
        )

        st.dataframe(
            ticket_cf,
            use_container_width=True,
        )

        # =================================================
        # DOWNLOAD CSV TICKET
        # =================================================

        csv_ticket = ticket_cf.to_csv(
            sep=";",
            index=False,
            decimal=",",
        ).encode("utf-8-sig")

        st.download_button(
            label="Scarica CSV ticket 3moreEvents",
            data=csv_ticket,
            file_name="1_3moreEvents_ticket.csv",
            mime="text/csv",
            key="download_3more_ticket",
        )

        # =================================================
        # DOWNLOAD CSV DETTAGLIO
        # =================================================

        if (
            dettaglio is not None
            and not dettaglio.empty
        ):

            csv_dettaglio = dettaglio.to_csv(
                sep=";",
                index=False,
                decimal=",",
            ).encode("utf-8-sig")

            st.download_button(
                label="Scarica CSV dettaglio eventi 3moreEvents",
                data=csv_dettaglio,
                file_name="2_3moreEvents_dettaglio_eventi.csv",
                mime="text/csv",
                key="download_3more_dettaglio",
            )
