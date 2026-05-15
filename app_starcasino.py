import streamlit as st
import promo


st.set_page_config(
    page_title="STARCASINO CSV",
    layout="wide"
)

st.title("Estrazioni Conti per promozione - STARCASINO")

st.write("Inserisci i filtri e poi genera il CSV.")

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
    value=None
)

betradar_input = st.text_area(
    "Betradar ID separati da virgola",
    value="61526570,61061655,61624622"
)

quota_min = st.number_input(
    "Quota minima su tutti gli eventi",
    min_value=0.0,
    value=1.5,
    step=0.1
)

is_sistema = st.selectbox(
    "Tipo ticket",
    options=[0, 1],
    format_func=lambda x: "Solo ticket singoli - is_sistema=0" if x == 0 else "Solo sistemi - is_sistema=1"
)

cf_input = st.text_input(
    "CF specifico opzionale",
    value=""
)

# =========================================================
# BOTTONE GENERA
# =========================================================
if st.button("Genera CSV"):

    if data_vendita_da is None:
        st.error("Devi inserire una data vendita da cui iniziare l'estrazione.")
        st.stop()

    if ora_vendita_da is None:
        ora_vendita_da = "00:00:00"

    data_vendita_da_str = f"{data_vendita_da} {ora_vendita_da}"

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
    promo.CF = cf_input.strip() if cf_input.strip() else None

    st.info("Estrazione dati in corso...")
    st.write(f"Data vendita da: {promo.DATA_VENDITA_DA}")
    st.write(f"Numero eventi richiesto: {len(betradar_list)}")

    df = promo.estrai_dati()

    if df.empty:
        st.error("Nessun dato trovato dal database.")
    else:
        st.success(f"Righe lette dal database: {len(df)}")

        df = promo.normalizza_output(df)
        df = promo.applica_filtro_quota_tutti_eventi(df)

        if df.empty:
            st.warning("Nessun ticket valido dopo il filtro quota.")
        else:
            colonne_ticket = [
                "id_ticket",
                "cf",
                "num_conto",
                "nome_commerciale",
                "des_stato",
                "data_ora_vend",
                "importo_pagato",
                "importo_vincita_potenziale",
            ]

            ticket_cf = (
                df[colonne_ticket]
                .drop_duplicates(subset=["id_ticket", "cf"])
                .sort_values(by=["nome_commerciale", "cf", "id_ticket"])
                .reset_index(drop=True)
            )

            st.success(f"Ticket trovati: {ticket_cf['id_ticket'].nunique()}")
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
