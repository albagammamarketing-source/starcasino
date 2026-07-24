from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import pymysql


# =========================================================
# CONFIGURAZIONE PERCORSI
# =========================================================

BASE_PATH = Path("output")
BASE_PATH.mkdir(parents=True, exist_ok=True)

OUTPUT_CSV = BASE_PATH / "1_3moreEvents_ticket.csv"
OUTPUT_DETTAGLIO_CSV = BASE_PATH / "2_3moreEvents_dettaglio_eventi.csv"


# =========================================================
# CONFIGURAZIONE DATABASE
# =========================================================

DB_PORT = int(os.getenv("PIPELINE_DB_PORT", "3306"))

DB_CONFIG = {
    "user": os.getenv("PIPELINE_DB_USER", "dbalba11"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("PIPELINE_DB_HOST", "194.163.157.255"),
    "database": "AnalisiTickets_STARCASINO",
}


# =========================================================
# FILTRI SETTABILI DA STREAMLIT
# =========================================================

DATA_VENDITA_DA = "2026-05-01 00:00:00"

# Regola principale della promo:
# prende ticket con num_eventi >= NUM_EVENTI_MIN
NUM_EVENTI_MIN = 3

DES_STATO = None
IS_SISTEMA = 0
CF = None

# Mercato / des_scom opzionale.
DES_SCOM_LIST = None

# Sport ammessi nel ticket.
# Il ticket è valido solo se TUTTI i suoi eventi appartengono
# agli sport selezionati.
DES_SPORT_LIST = ["CALCIO", "TENNIS"]

# Quota ticket minima.
# La quota ticket viene calcolata moltiplicando le quote
# dei singoli eventi presenti in Ticket_Detail.quota / 100.
# None oppure 0 = nessun filtro minimo.
QUOTA_TICKET_MIN = 1.0


# =========================================================
# CONNESSIONE DATABASE
# =========================================================

def apri_connessione(cfg: dict):
    if not cfg.get("password"):
        raise RuntimeError(
            "Password database non configurata. "
            "Imposta la variabile d'ambiente DB_PASSWORD."
        )

    return pymysql.connect(
        host=cfg["host"],
        port=DB_PORT,
        user=cfg["user"],
        password=cfg["password"],
        database=cfg["database"],
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )


# =========================================================
# QUERY
# =========================================================

def costruisci_query() -> tuple[str, list[object]]:
    """
    Estrae tutti i dettagli dei ticket che rispettano:

    - data_ora_vend >= DATA_VENDITA_DA
    - num_eventi >= NUM_EVENTI_MIN
    - is_sistema = IS_SISTEMA
    - eventuale CF
    - eventuale filtro mercato
    - tutti gli eventi del ticket devono appartenere agli sport
      selezionati in DES_SPORT_LIST

    Il filtro sulla QUOTA TICKET viene applicato dopo l'estrazione,
    calcolando il prodotto delle quote evento da Ticket_Detail.quota.
    """

    if NUM_EVENTI_MIN is None or int(NUM_EVENTI_MIN) <= 0:
        raise ValueError("NUM_EVENTI_MIN deve essere maggiore di 0.")

    col_data = "STR_TO_DATE(tg.data_ora_vend, '%%Y%%m%%d %%H:%%i:%%s')"

    where_clauses = [
        "tg.data_ora_vend IS NOT NULL",
        "tg.data_ora_vend <> ''",
        f"{col_data} >= %s",
        "tg.num_eventi >= %s",
        "tg.is_sistema = %s",
    ]

    params: list[object] = [
        DATA_VENDITA_DA,
        int(NUM_EVENTI_MIN),
        int(IS_SISTEMA),
    ]

    if DES_STATO:
        where_clauses.append("tg.des_stato = %s")
        params.append(DES_STATO)

    filtro_cf = str(CF).strip() if CF is not None else ""
    if filtro_cf:
        where_clauses.append("UPPER(TRIM(tg.cf)) = %s")
        params.append(filtro_cf.upper())

    # -----------------------------------------------------
    # FILTRO SPORT A LIVELLO TICKET
    # -----------------------------------------------------
    sport_list = list(dict.fromkeys(
        str(x).strip().upper()
        for x in (DES_SPORT_LIST or [])
        if str(x).strip()
    ))

    if sport_list:
        sport_placeholders = ",".join(["%s"] * len(sport_list))

        # Sono ammessi solo ticket in cui:
        # 1) esiste almeno un evento con sport selezionato;
        # 2) non esiste alcun evento appartenente a sport non selezionati.
        where_clauses.append(
            f"""
            EXISTS (
                SELECT 1
                FROM Ticket_Detail td_sport_ok
                WHERE td_sport_ok.id_ticket = tg.id_ticket
                  AND UPPER(TRIM(COALESCE(td_sport_ok.des_sport, '')))
                      IN ({sport_placeholders})
            )
            """
        )
        params.extend(sport_list)

        where_clauses.append(
            f"""
            NOT EXISTS (
                SELECT 1
                FROM Ticket_Detail td_sport_ko
                WHERE td_sport_ko.id_ticket = tg.id_ticket
                  AND UPPER(TRIM(COALESCE(td_sport_ko.des_sport, '')))
                      NOT IN ({sport_placeholders})
            )
            """
        )
        params.extend(sport_list)

    # -----------------------------------------------------
    # FILTRO MERCATO A LIVELLO TICKET
    # -----------------------------------------------------
    des_scom_list = list(dict.fromkeys(
        str(x).strip()
        for x in (DES_SCOM_LIST or [])
        if str(x).strip()
    ))

    if des_scom_list:
        mercato_placeholders = ",".join(["%s"] * len(des_scom_list))

        where_clauses.append(
            f"""
            tg.id_ticket IN (
                SELECT td_scom.id_ticket
                FROM Ticket_Detail td_scom
                GROUP BY td_scom.id_ticket
                HAVING
                    COUNT(
                        DISTINCT TRIM(COALESCE(td_scom.des_scom, ''))
                    ) = 1
                    AND MAX(
                        TRIM(COALESCE(td_scom.des_scom, ''))
                    ) IN ({mercato_placeholders})
            )
            """
        )
        params.extend(des_scom_list)

    where_sql = "\n        AND ".join(where_clauses)

    query = f"""
        SELECT
            tg.id_ticket,
            tg.num_conto,
            tg.cf,
            tg.nome_commerciale,
            tg.num_eventi,
            tg.des_stato,
            tg.is_sistema,
            tg.data_ora_vend,
            tg.importo_pagato_eur,
            tg.importo_vincita_eur,
            td.betradar_id,
            td.des_sport,
            td.des_manif,
            td.des_scom,
            td.des_eve,
            td.quota,
            td.cod_stato_esito
        FROM Ticket_General tg
        INNER JOIN Ticket_Detail td
            ON tg.id_ticket = td.id_ticket
        WHERE {where_sql}
        ORDER BY
            {col_data},
            tg.cf,
            tg.id_ticket,
            td.betradar_id
    """

    return query, params


def estrai_dati() -> pd.DataFrame:
    query, params = costruisci_query()
    conn = apri_connessione(DB_CONFIG)

    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

        return pd.DataFrame(rows)

    finally:
        conn.close()


# =========================================================
# NORMALIZZAZIONE
# =========================================================

def normalizza_output(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()

    colonne_testo = [
        "id_ticket",
        "num_conto",
        "cf",
        "nome_commerciale",
        "des_stato",
        "data_ora_vend",
        "betradar_id",
        "des_sport",
        "des_manif",
        "des_scom",
        "des_eve",
        "cod_stato_esito",
    ]

    for col in colonne_testo:
        if col in df.columns:
            df[col] = (
                df[col]
                .fillna("")
                .astype(str)
                .str.strip()
            )

    colonne_numeriche = [
        "num_eventi",
        "is_sistema",
        "importo_pagato_eur",
        "importo_vincita_eur",
        "quota",
    ]

    for col in colonne_numeriche:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce",
            )

    df["importo_pagato"] = (
        df["importo_pagato_eur"] / 100
    ).round(2)

    df["importo_vincita_potenziale"] = (
        df["importo_vincita_eur"] / 100
    ).round(2)

    # Ticket_Detail.quota è memorizzata in centesimi:
    # 150 -> 1,50
    df["quota_evento"] = (
        df["quota"] / 100
    ).round(4)

    return df


# =========================================================
# QUOTA TICKET
# =========================================================

def aggiungi_quota_ticket(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcola la quota complessiva del ticket come prodotto
    delle quote dei singoli eventi:

        quota_ticket = quota_evento_1 * quota_evento_2 * ...

    Usa Ticket_Detail.quota come richiesto.
    """

    if df.empty:
        return df

    if "quota_evento" not in df.columns:
        raise ValueError("Colonna quota_evento non presente.")

    quote_ticket = (
        df.groupby("id_ticket", as_index=False)
        .agg(
            quota_ticket=("quota_evento", "prod")
        )
    )

    quote_ticket["quota_ticket"] = (
        quote_ticket["quota_ticket"]
        .round(4)
    )

    return df.merge(
        quote_ticket,
        on="id_ticket",
        how="left",
        validate="many_to_one",
    )


def applica_filtro_quota_ticket(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = aggiungi_quota_ticket(df)

    if QUOTA_TICKET_MIN is None or float(QUOTA_TICKET_MIN) <= 0:
        return df

    ticket_validi = (
        df.loc[
            df["quota_ticket"] >= float(QUOTA_TICKET_MIN),
            "id_ticket",
        ]
        .drop_duplicates()
    )

    return df[
        df["id_ticket"].isin(ticket_validi)
    ].copy()


# =========================================================
# OUTPUT TICKET
# =========================================================

def crea_output_ticket(df: pd.DataFrame) -> pd.DataFrame:
    colonne_output = [
        "id_ticket",
        "cf",
        "num_conto",
        "nome_commerciale",
        "des_stato",
        "data_ora_vend",
        "num_eventi",
        "Sport",
        "quota_ticket",
        "Mercato",
        "Importo Giocato",
        "Importo Vincita Potenziale",
    ]

    if df.empty:
        return pd.DataFrame(columns=colonne_output)

    sport_per_ticket = (
        df.groupby("id_ticket")["des_sport"]
        .agg(
            lambda s: ", ".join(
                sorted({
                    str(x).strip()
                    for x in s
                    if str(x).strip()
                })
            )
        )
        .rename("Sport")
        .reset_index()
    )

    base = (
        df[
            [
                "id_ticket",
                "cf",
                "num_conto",
                "nome_commerciale",
                "des_stato",
                "data_ora_vend",
                "num_eventi",
                "quota_ticket",
                "des_scom",
                "importo_pagato",
                "importo_vincita_potenziale",
            ]
        ]
        .drop_duplicates(subset=["id_ticket"])
        .merge(
            sport_per_ticket,
            on="id_ticket",
            how="left",
            validate="one_to_one",
        )
    )

    base = base.rename(
        columns={
            "des_scom": "Mercato",
            "importo_pagato": "Importo Giocato",
            "importo_vincita_potenziale":
                "Importo Vincita Potenziale",
        }
    )

    base = (
        base[
            colonne_output
        ]
        .sort_values(
            by=["nome_commerciale", "cf", "id_ticket"]
        )
        .reset_index(drop=True)
    )

    return base


# =========================================================
# OUTPUT DETTAGLIO
# =========================================================

def crea_output_dettaglio(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    colonne = [
        "id_ticket",
        "cf",
        "num_conto",
        "nome_commerciale",
        "des_stato",
        "data_ora_vend",
        "num_eventi",
        "quota_ticket",
        "betradar_id",
        "des_sport",
        "des_manif",
        "des_scom",
        "des_eve",
        "quota_evento",
        "cod_stato_esito",
        "importo_pagato",
        "importo_vincita_potenziale",
    ]

    colonne_presenti = [
        col for col in colonne
        if col in df.columns
    ]

    dettaglio = df[colonne_presenti].copy()

    dettaglio = dettaglio.rename(
        columns={
            "des_scom": "Mercato",
            "importo_pagato": "Importo Giocato",
            "importo_vincita_potenziale":
                "Importo Vincita Potenziale",
        }
    )

    return (
        dettaglio
        .sort_values(
            by=["id_ticket", "betradar_id"],
            na_position="last",
        )
        .reset_index(drop=True)
    )


# =========================================================
# FUNZIONE COMPLETA PER STREAMLIT
# =========================================================

def esegui_estrazione() -> tuple[pd.DataFrame, pd.DataFrame]:
    df = estrai_dati()

    if df.empty:
        return (
            crea_output_ticket(df),
            crea_output_dettaglio(df),
        )

    df = normalizza_output(df)
    df = applica_filtro_quota_ticket(df)

    if df.empty:
        return (
            crea_output_ticket(df),
            crea_output_dettaglio(df),
        )

    return (
        crea_output_ticket(df),
        crea_output_dettaglio(df),
    )


# =========================================================
# SALVATAGGIO CSV
# =========================================================

def salva_csv(df: pd.DataFrame, path: Path) -> None:
    df.to_csv(
        path,
        sep=";",
        index=False,
        encoding="utf-8-sig",
        decimal=",",
    )
    print(f"Salvato: {path}")


# =========================================================
# MAIN LOCALE
# =========================================================

def main() -> None:
    print("Estrazione STARCASINO - promo_3moreEvents")
    print(f"Data vendita da: {DATA_VENDITA_DA}")
    print(f"Numero eventi minimo: {NUM_EVENTI_MIN}")
    print(f"Quota ticket minima: {QUOTA_TICKET_MIN}")
    print(f"Sport ammessi: {DES_SPORT_LIST}")
    print(f"is_sistema: {IS_SISTEMA}")

    ticket, dettaglio = esegui_estrazione()

    salva_csv(ticket, OUTPUT_CSV)
    salva_csv(dettaglio, OUTPUT_DETTAGLIO_CSV)

    print(f"Ticket trovati: {len(ticket)}")
    print(f"Righe dettaglio: {len(dettaglio)}")


if __name__ == "__main__":
    main()
