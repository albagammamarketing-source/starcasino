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
    "La seguente applicazione restituisce un file CSV con le informazioni: "
    "id_ticket, cf, num_conto, nome_commerciale, des_stato, "
    "data_ora_vend, Mercato, Importo Giocato, Importo Vincita Potenziale."
)

st.warning(
    "Il filtro Mercato è opzionale. "
    "Se viene compilato, il CSV includerà soltanto ticket composti interamente "
    "da un unico des_scom tra quelli indicati. "
    "Se viene lasciato vuoto, saranno considerati tutti i mercati."
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
    format="%.2f",
    help=(
        "Ogni evento del ticket deve avere una quota maggiore o uguale "
        "al valore indicato."
    )
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

mercato_input = st.text_input(
    "Mercato opzionale - des_scom",
    value="",
    help=(
        "Esempio: Vincente. "
        "Puoi inserire più valori separati da virgola. "
        "Quando il campo è compilato, ogni ticket sarà accettato solo se contiene "
        "un unico des_scom distinto appartenente ai valori indicati. "
        "Lascia il campo vuoto per non applicare il filtro mercato."
    )
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

    # Rimuove anche eventuali Betradar duplicati,
    # mantenendo l'ordine di inserimento.
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

    # =====================================================
    # PASSAGGIO FILTRI A promo.py
    # =====================================================

    promo.DATA_VENDITA_DA = data_vendita_da_str
    promo.BETRADAR_ID_LIST = betradar_list
    promo.QUOTA_MIN_TUTTI_EVENTI = float(quota_min)
    promo.IS_SISTEMA = int(is_sistema)
    promo.CF = cf_input.strip().upper() if cf_input.strip() else None

    # Se il campo Mercato è vuoto, promo.py non applica
    # alcun filtro su des_scom.
    promo.DES_SCOM_LIST = mercato_list if mercato_list else None

    st.info("Estrazione dati in corso...")

    st.write(f"Data vendita da: {promo.DATA_VENDITA_DA}")
    st.write(f"Betradar richiesti: {', '.join(betradar_list)}")
    st.write(f"Numero eventi richiesto: {len(betradar_list)}")
    st.write(
        f"Quota minima su ogni evento: "
        f"{promo.QUOTA_MIN_TUTTI_EVENTI:.2f}"
    )
    st.write(f"is_sistema: {promo.IS_SISTEMA}")

    if mercato_list:
        st.write(f"Mercati richiesti: {', '.join(mercato_list)}")
        st.write(
            "Regola mercato: sono ammessi soltanto ticket con un unico "
            "des_scom distinto, appartenente ai mercati indicati."
        )
    else:
        st.write("Mercato: tutti, nessun filtro applicato.")

    if promo.CF:
        st.write(f"CF filtrato: {promo.CF}")
    else:
        st.write("CF: tutti.")

    if importo_giocato_min > 0:
        st.write(
            f"Importo Giocato minimo: "
            f"{float(importo_giocato_min):.2f} euro"
        )

    if importo_giocato_max > 0:
        st.write(
            f"Importo Giocato massimo: "
            f"{float(importo_giocato_max):.2f} euro"
        )

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

    if "id_ticket" not in df.columns:
        st.error("La colonna id_ticket non è presente nei dati estratti.")
        st.write("Colonne disponibili:")
        st.write(list(df.columns))
        st.stop()

    st.success(f"Righe lette dal database: {len(df)}")
    st.write(
        f"Ticket unici letti dal database: "
        f"{df['id_ticket'].nunique()}"
    )

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
        st.warning(
            "Nessun ticket valido dopo il filtro quota. "
            "Ogni evento del ticket deve avere una quota maggiore o uguale "
            "alla quota minima indicata."
        )
        st.stop()

    # =====================================================
    # CONTROLLO SICUREZZA MERCATO
    # =====================================================
    # Il controllo viene applicato soltanto quando
    # l'utente inserisce almeno un mercato.
    #
    # promo.py applica già il filtro nella query.
    # Questo controllo aggiuntivo serve come verifica di sicurezza.

    if mercato_list:

        if "des_scom" not in df.columns:
            st.error(
                "La colonna des_scom non è presente nel dataframe, "
                "quindi non è possibile verificare il filtro mercato."
            )
            st.stop()

        controllo_mercati = (
            df.groupby("id_ticket")["des_scom"]
            .nunique(dropna=False)
            .reset_index(name="numero_mercati_distinti")
        )

        ticket_con_piu_mercati = controllo_mercati[
            controllo_mercati["numero_mercati_distinti"] > 1
        ]

        if not ticket_con_piu_mercati.empty:
            df = df[
                ~df["id_ticket"].isin(
                    ticket_con_piu_mercati["id_ticket"]
                )
            ].copy()

            st.warning(
                f"Esclusi {len(ticket_con_piu_mercati)} ticket perché "
                "contenevano più mercati des_scom."
            )

        # Verifica anche che il mercato presente sia realmente
        # compreso tra quelli richiesti.
        mercato_normalizzato = {
            mercato.strip().casefold()
            for mercato in mercato_list
        }

        mercato_ticket = (
            df.groupby("id_ticket")["des_scom"]
            .first()
            .fillna("")
            .astype(str)
            .str.strip()
            .str.casefold()
        )

        ticket_mercato_non_valido = mercato_ticket[
            ~mercato_ticket.isin(mercato_normalizzato)
        ].index

        if len(ticket_mercato_non_valido) > 0:
            df = df[
                ~df["id_ticket"].isin(ticket_mercato_non_valido)
            ].copy()

            st.warning(
                f"Esclusi {len(ticket_mercato_non_valido)} ticket perché "
                "il mercato non corrispondeva ai valori richiesti."
            )

        if df.empty:
            st.warning(
                "Nessun ticket rimasto dopo il controllo sui mercati."
            )
            st.stop()

    # =====================================================
    # FILTRO IMPORTO GIOCATO
    # =====================================================

    if "importo_pagato" not in df.columns:
        st.error(
            "La colonna importo_pagato non è presente nel dataframe."
        )
        st.stop()

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
        "importo_vincita_potenziale":
            "Importo Vincita Potenziale",
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

    mercati_presenti = sorted(
        mercato
        for mercato in (
            ticket_cf["Mercato"]
            .dropna()
            .astype(str)
            .str.strip()
            .unique()
        )
        if mercato
    )

    if mercati_presenti:
        st.write(
            "Mercati presenti nel risultato: "
            f"{', '.join(mercati_presenti)}"
        )
    else:
        st.write(
            "Mercati presenti nel risultato: nessun valore disponibile."
        )

    st.dataframe(
        ticket_cf,
        use_container_width=True
    )

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
