import streamlit as st
from datetime import time
import promo
import promo_5evetswin
import promo_3moreevents
import promo_live


# =========================================================
# CONFIGURAZIONE PAGINA
# =========================================================

st.set_page_config(
    page_title="STARCASINO - Gestione Promozioni",
    layout="wide"
)

# =========================================================
# STILE GRAFICO
# =========================================================

st.markdown(
    """
    <style>

    /* Contenitore principale */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1450px;
    }

    /* Titolo principale */
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

    /* Box menu */
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

    /* Selectbox */
    div[data-baseweb="select"] > div {
        border-radius: 12px !important;
        min-height: 48px;
        font-weight: 700;
        border: 2px solid #2563eb !important;
        background-color: #ffffff;
    }

    /* Box descrizione promo */
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

    .promo-more {
        background: #eefbf3;
        border-color: #a7dfba;
        border-left: 6px solid #16a34a;
    }

    .promo-win {
        background: #fff8e8;
        border-color: #f5d889;
        border-left: 6px solid #e5a000;
    }

    /* Etichette campi */
    label[data-testid="stWidgetLabel"] p {
        font-weight: 700 !important;
    }

    /* Input */
    input, textarea {
        border-radius: 10px !important;
    }

    /* Pulsanti */
    .stButton > button {
        border-radius: 10px;
        font-weight: 800;
        padding: 0.65rem 1.2rem;
    }

    .stDownloadButton > button {
        border-radius: 10px;
        font-weight: 800;
    }

    /* Divider */
    hr {
        margin-top: 1rem;
        margin-bottom: 1.5rem;
    }

    </style>
    """,
    unsafe_allow_html=True,
)

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
        "🔴 PromoLive",
        "🎟️ 3moreEvents",
        "🏆 5evetsWin",
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
# PROMO 2 - PROMOLIVE
# =========================================================

elif promozione_selezionata == "🔴 PromoLive":

    st.markdown(
        """
        <div class="promo-card promo-betradar">
            <div class="promo-card-title">🔴 PromoLive</div>
            <div class="promo-card-text">
                <b>Obiettivo:</b> individuare ticket singoli con un solo evento,
                appartenente a una delle manifestazioni indicate, con filtro
                LIVE / PRE-MATCH e filtro Sport.
                <br><br>
                <b>Regola:</b> vengono estratti esclusivamente ticket con
                <b>is_sistema = 0</b> e <b>num_eventi = 1</b>.
                L'unica manifestazione del ticket deve essere una delle
                manifestazioni inserite nella lista.
                <br><br>
                Esempio: inserendo <b>309,4774</b>, vengono estratti ticket
                con un solo evento avente manifestazione <b>309 oppure 4774</b>.
                <br><br>
                <b>Output:</b> ticket estratti e dettaglio dell'unico evento.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    data_vendita_da = st.date_input(
        "Data vendita da",
        value=None,
        format="DD/MM/YYYY",
        key="promolive_data_vendita_da",
    )

    ora_vendita_da = st.time_input(
        "Ora vendita da",
        value=time(0, 0),
        key="promolive_ora_vendita_da",
    )

    manifestazione_input = st.text_area(
        "Codici manifestazione separati da virgola",
        value="",
        key="promolive_manifestazione_input",
        help=(
            "Inserisci uno o più codici. Il ticket deve avere un solo evento "
            "e la manifestazione deve essere una di quelle indicate. "
            "Esempio: 309,4774 significa 309 OPPURE 4774."
        ),
    )

    flg_live = st.selectbox(
        "Tipo evento - flg_live",
        options=[0, 1],
        format_func=lambda x: (
            "0 - Pre-match"
            if x == 0
            else "1 - Live"
        ),
        index=1,
        key="promolive_flg_live",
    )

    sport_selezionati = st.multiselect(
        "Sport",
        options=[
            "CALCIO",
            "TENNIS",
            "BASKET",
            "PALLAVOLO",
            "HOCKEY",
            "BASEBALL",
            "RUGBY",
            "ALTRO",
        ],
        default=["CALCIO"],
        key="promolive_sport",
        help=(
            "Seleziona uno o più sport. Con più sport viene applicata "
            "una logica OR. Default: CALCIO."
        ),
    )

    quota_min = st.number_input(
        "Quota minima evento",
        min_value=0.0,
        value=1.5,
        step=0.1,
        format="%.2f",
        key="promolive_quota_min",
        help=(
            "PromoLive estrae ticket con un solo evento, quindi la quota "
            "minima si applica a quell'unico evento."
        ),
    )

    cf_input = st.text_input(
        "CF specifico opzionale",
        value="",
        key="promolive_cf_input",
    )

    mercato_input = st.text_input(
        "Mercato opzionale - des_scom, separa più valori con virgola",
        value="",
        key="promolive_mercato_input",
        help=(
            "Con più mercati viene applicata una logica OR: l'unico evento "
            "deve avere uno dei mercati indicati."
        ),
    )

    importo_giocato_min = st.number_input(
        "Importo Giocato minimo opzionale",
        min_value=0.0,
        value=0.0,
        step=1.0,
        format="%.2f",
        key="promolive_importo_min",
    )

    importo_giocato_max = st.number_input(
        "Importo Giocato massimo opzionale - lascia 0 per non applicare limite massimo",
        min_value=0.0,
        value=0.0,
        step=1.0,
        format="%.2f",
        key="promolive_importo_max",
    )

    if st.button("Genera CSV PromoLive", key="genera_csv_promolive"):

        if data_vendita_da is None:
            st.error("Devi inserire una data vendita da cui iniziare l'estrazione.")
            st.stop()

        data_vendita_da_str = (
            f"{data_vendita_da.strftime('%Y-%m-%d')} "
            f"{ora_vendita_da.strftime('%H:%M:%S')}"
        )

        manifestazione_list = list(dict.fromkeys(
            x.strip()
            for x in manifestazione_input.split(",")
            if x.strip()
        ))

        if not manifestazione_list:
            st.error("Devi inserire almeno un codice manifestazione.")
            st.stop()

        mercato_list = list(dict.fromkeys(
            x.strip()
            for x in mercato_input.split(",")
            if x.strip()
        ))

        promo_live.DATA_VENDITA_DA = data_vendita_da_str
        promo_live.MANIFESTAZIONE_LIST = manifestazione_list
        promo_live.FLG_LIVE = int(flg_live)
        promo_live.DES_SPORT_LIST = (
            sport_selezionati if sport_selezionati else None
        )
        promo_live.QUOTA_MIN_TUTTI_EVENTI = float(quota_min)
        promo_live.IS_SISTEMA = 0
        promo_live.CF = (
            cf_input.strip().upper()
            if cf_input.strip()
            else None
        )
        promo_live.DES_SCOM_LIST = (
            mercato_list if mercato_list else None
        )

        st.info("Estrazione dati PromoLive in corso...")

        st.write(f"Data vendita da: {promo_live.DATA_VENDITA_DA}")
        st.write(
            f"Manifestazioni ammesse: {', '.join(manifestazione_list)}"
        )
        st.write("Numero eventi richiesto: 1")
        st.write("Tipo ticket: singola - is_sistema = 0")
        st.write(
            f"flg_live: {promo_live.FLG_LIVE} "
            f"({'LIVE' if promo_live.FLG_LIVE == 1 else 'PRE-MATCH'})"
        )
        st.write(
            f"Sport: {promo_live.DES_SPORT_LIST or 'TUTTI'}"
        )
        st.write(
            f"Quota minima evento: {promo_live.QUOTA_MIN_TUTTI_EVENTI}"
        )
        st.write(
            f"Mercato: {promo_live.DES_SCOM_LIST or 'TUTTI'}"
        )

        if promo_live.CF:
            st.write(f"CF filtrato: {promo_live.CF}")

        if importo_giocato_min > 0:
            st.write(f"Importo Giocato minimo: {importo_giocato_min}")

        if importo_giocato_max > 0:
            st.write(f"Importo Giocato massimo: {importo_giocato_max}")

        try:
            ticket_cf, dettaglio = promo_live.esegui_estrazione()
        except Exception as e:
            st.error("Errore durante l'estrazione PromoLive.")
            st.exception(e)
            st.stop()

        if ticket_cf is None or ticket_cf.empty:
            st.warning("Nessun ticket trovato con i filtri impostati.")
            st.stop()

        if importo_giocato_min > 0:
            ticket_validi = ticket_cf.loc[
                ticket_cf["Importo Giocato"] >= float(importo_giocato_min),
                "id_ticket",
            ]
            ticket_cf = ticket_cf[
                ticket_cf["id_ticket"].isin(ticket_validi)
            ].copy()
            dettaglio = dettaglio[
                dettaglio["id_ticket"].isin(ticket_validi)
            ].copy()

        if importo_giocato_max > 0:
            ticket_validi = ticket_cf.loc[
                ticket_cf["Importo Giocato"] <= float(importo_giocato_max),
                "id_ticket",
            ]
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

        st.subheader("Ticket estratti")
        st.dataframe(ticket_cf, use_container_width=True)

        csv_ticket = ticket_cf.to_csv(
            sep=";",
            index=False,
            decimal=",",
        ).encode("utf-8-sig")

        st.download_button(
            label="Scarica CSV ticket PromoLive",
            data=csv_ticket,
            file_name="1_promolive_ticket_cf_filtrati.csv",
            mime="text/csv",
        )

        st.subheader("Dettaglio evento")
        st.dataframe(dettaglio, use_container_width=True)

        csv_dettaglio = dettaglio.to_csv(
            sep=";",
            index=False,
            decimal=",",
        ).encode("utf-8-sig")

        st.download_button(
            label="Scarica CSV dettaglio evento PromoLive",
            data=csv_dettaglio,
            file_name="2_promolive_dettaglio_eventi_filtrati.csv",
            mime="text/csv",
        )


# =========================================================
# PROMO 3 - 3moreEvents
# =========================================================

elif promozione_selezionata == "🎟️ 3moreEvents":

    st.markdown(
        """
        <div class="promo-card promo-more">
            <div class="promo-card-title">🎟️ 3moreEvents</div>
            <div class="promo-card-text">
                <b>Obiettivo:</b> individuare ticket con un numero di eventi
                maggiore o uguale alla soglia impostata. Il valore predefinito
                è 3 eventi.
                <br><br>
                La quota minima deve essere rispettata da <b>tutti gli eventi</b>
                del ticket. È possibile anche impostare una quota minima
                complessiva del ticket, calcolata come prodotto delle quote
                evento. È inoltre possibile filtrare sport, codici
                manifestazione, mercato, tipo ticket, CF e importo giocato.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

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

    num_eventi_min = st.number_input(
        "Numero minimo di eventi del ticket",
        min_value=1,
        value=3,
        step=1,
        key="3more_num_eventi_min",
        help="Saranno estratti i ticket con num_eventi maggiore o uguale a questo valore.",
    )

    quota_min = st.number_input(
        "Quota minima per ogni evento",
        min_value=0.0,
        value=1.5,
        step=0.1,
        format="%.2f",
        key="3more_quota_min",
        help="Ogni singolo evento del ticket deve avere almeno questa quota.",
    )

    quota_ticket_min = st.number_input(
        "Quota minima del ticket",
        min_value=0.0,
        value=0.0,
        step=0.1,
        format="%.2f",
        key="3more_quota_ticket_min",
        help=(
            "Quota complessiva calcolata moltiplicando le quote dei singoli "
            "eventi. Lascia 0 per non applicare il filtro."
        ),
    )

    sport_selezionati = st.multiselect(
        "Sport ammessi nel ticket",
        options=[
            "CALCIO",
            "TENNIS",
            "BASKET",
            "PALLAVOLO",
            "HOCKEY",
            "BASEBALL",
            "RUGBY",
            "ALTRO",
        ],
        default=["CALCIO", "TENNIS"],
        key="3more_sport",
        help=(
            "Il ticket viene accettato solo se tutti i suoi eventi appartengono "
            "agli sport selezionati. Nessuna selezione significa tutti gli sport."
        ),
    )

    manifestazione_input = st.text_input(
        "Manifestazione opzionale - separa più valori con virgola",
        value="",
        key="3more_manifestazione",
        help=(
            "Il ticket viene accettato se almeno un evento contiene una delle "
            "manifestazioni inserite."
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
        help=(
            "Quando impostato, il ticket deve contenere un solo mercato distinto "
            "e tale mercato deve essere tra quelli indicati."
        ),
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

    if st.button("Genera CSV 3moreEvents", key="genera_csv_3more"):

        if data_vendita_da is None:
            st.error("Devi inserire una data vendita da cui iniziare l'estrazione.")
            st.stop()

        data_vendita_da_str = (
            f"{data_vendita_da.strftime('%Y-%m-%d')} "
            f"{ora_vendita_da.strftime('%H:%M:%S')}"
        )

        manifestazione_list = list(dict.fromkeys(
            x.strip()
            for x in manifestazione_input.split(",")
            if x.strip()
        ))

        mercato_list = list(dict.fromkeys(
            x.strip()
            for x in mercato_input.split(",")
            if x.strip()
        ))

        promo_3moreevents.DATA_VENDITA_DA = data_vendita_da_str
        promo_3moreevents.NUM_EVENTI_MIN = int(num_eventi_min)
        promo_3moreevents.QUOTA_MIN_TUTTI_EVENTI = float(quota_min)
        promo_3moreevents.QUOTA_TICKET_MIN = float(quota_ticket_min)
        promo_3moreevents.DES_SPORT_LIST = (
            sport_selezionati if sport_selezionati else None
        )
        promo_3moreevents.MANIFESTAZIONE_LIST = (
            manifestazione_list if manifestazione_list else None
        )
        promo_3moreevents.IS_SISTEMA = int(is_sistema)
        promo_3moreevents.CF = (
            cf_input.strip().upper() if cf_input.strip() else None
        )
        promo_3moreevents.DES_SCOM_LIST = (
            mercato_list if mercato_list else None
        )

        st.info("Estrazione dati 3moreEvents in corso...")

        st.write(f"Data vendita da: {promo_3moreevents.DATA_VENDITA_DA}")
        st.write(
            f"Numero eventi: num_eventi >= {promo_3moreevents.NUM_EVENTI_MIN}"
        )
        st.write(
            "Quota minima per ogni evento: "
            f"{promo_3moreevents.QUOTA_MIN_TUTTI_EVENTI}"
        )
        st.write(
            "Quota minima del ticket: "
            f"{promo_3moreevents.QUOTA_TICKET_MIN if promo_3moreevents.QUOTA_TICKET_MIN > 0 else 'NESSUN FILTRO'}"
        )
        st.write(
            "Sport ammessi: "
            f"{promo_3moreevents.DES_SPORT_LIST or 'TUTTI'}"
        )
        st.write(
            "Manifestazioni: "
            f"{promo_3moreevents.MANIFESTAZIONE_LIST or 'TUTTE'}"
        )
        st.write(f"is_sistema: {promo_3moreevents.IS_SISTEMA}")
        st.write(
            f"Mercato: {promo_3moreevents.DES_SCOM_LIST or 'TUTTI'}"
        )

        if promo_3moreevents.CF:
            st.write(f"CF filtrato: {promo_3moreevents.CF}")

        if importo_giocato_min > 0:
            st.write(f"Importo Giocato minimo: {importo_giocato_min}")

        if importo_giocato_max > 0:
            st.write(f"Importo Giocato massimo: {importo_giocato_max}")

        try:
            ticket_cf, dettaglio = promo_3moreevents.esegui_estrazione()
        except Exception as e:
            st.error("Errore durante l'estrazione 3moreEvents.")
            st.exception(e)
            st.stop()

        if ticket_cf is None or ticket_cf.empty:
            st.warning("Nessun ticket trovato con i filtri impostati.")
            st.stop()

        if importo_giocato_min > 0:
            ticket_validi = ticket_cf.loc[
                ticket_cf["Importo Giocato"] >= float(importo_giocato_min),
                "id_ticket",
            ]
            ticket_cf = ticket_cf[
                ticket_cf["id_ticket"].isin(ticket_validi)
            ].copy()
            dettaglio = dettaglio[
                dettaglio["id_ticket"].isin(ticket_validi)
            ].copy()

        if importo_giocato_max > 0:
            ticket_validi = ticket_cf.loc[
                ticket_cf["Importo Giocato"] <= float(importo_giocato_max),
                "id_ticket",
            ]
            ticket_cf = ticket_cf[
                ticket_cf["id_ticket"].isin(ticket_validi)
            ].copy()
            dettaglio = dettaglio[
                dettaglio["id_ticket"].isin(ticket_validi)
            ].copy()

        if ticket_cf.empty:
            st.warning("Nessun ticket trovato dopo il filtro Importo Giocato.")
            st.stop()

        st.success(f"Ticket trovati: {ticket_cf['id_ticket'].nunique()}")
        st.write(f"CF trovati: {ticket_cf['cf'].nunique()}")
        st.write(
            "Punti vendita trovati: "
            f"{ticket_cf['nome_commerciale'].nunique()}"
        )

        st.subheader("Ticket estratti")
        st.dataframe(ticket_cf, use_container_width=True)

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
        )

        st.subheader("Dettaglio eventi")
        st.dataframe(dettaglio, use_container_width=True)

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
        )


# =========================================================
# PROMO 4 - 5evetsWin
# =========================================================

elif promozione_selezionata == "🏆 5evetsWin":

    st.markdown(
        """
        <div class="promo-card promo-win">
            <div class="promo-card-title">🏆 5evetsWin</div>
            <div class="promo-card-text">
                <b>Obiettivo:</b> individuare i ticket composti esattamente dagli
                eventi Betradar selezionati e contare, per ogni singolo ticket,
                quanti eventi hanno esito <b>WI</b> e quanti hanno esito <b>LO</b>.
                <br><br>
                Se inserisci 5 Betradar ID, il sistema cerca esclusivamente
                ticket da 5 eventi composti da quegli stessi 5 eventi.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
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

    betradar_input = st.text_area(
        "Betradar ID separati da virgola",
        value="53452557,53452541,53452547,53452561,53452543",
        key="5evetswin_betradar_input",
    )

    quota_min = st.number_input(
        "Quota minima su tutti gli eventi",
        min_value=0.0,
        value=1.0,
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

        promo_5evetswin.DATA_VENDITA_DA = data_vendita_da_str
        promo_5evetswin.BETRADAR_ID_LIST = betradar_list
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
        st.write(f"Numero eventi esatto: {len(betradar_list)}")
        st.write(
            f"Regola eventi: num_eventi = {len(betradar_list)}"
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

        st.subheader("Ticket estratti")

        st.write(
            "Le colonne eventi_WI ed eventi_LO indicano, per ogni ticket, "
            "quanti eventi hanno rispettivamente cod_stato_esito = WI "
            "e cod_stato_esito = LO."
        )

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
            label="Scarica CSV ticket con conteggio WI/LO",
            data=csv_ticket,
            file_name="1_5evetswin_ticket_WI_LO.csv",
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