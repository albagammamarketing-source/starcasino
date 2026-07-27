from __future__ import annotations

import math
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
DES_STATO = None
IS_SISTEMA = 0

NUM_EVENTI_MIN = 3
QUOTA_MIN_TUTTI_EVENTI = 1.5
QUOTA_TICKET_MIN = 0.0

DES_SPORT_LIST = ["CALCIO", "TENNIS"]
COD_MANIF_LIST = None
DES_SCOM_LIST = None
CF = None


# =========================================================
# CONNESSIONE DATABASE
# =========================================================

def apri_connessione(cfg: dict):
    if not cfg.get("password"):
        raise RuntimeError(
            "Password database non configurata. "
            "Imposta DB_PASSWORD nei Secrets di Streamlit."
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


def _lista_pulita(valori) -> list[str]:
    return list(
        dict.fromkeys(
            str(x).strip()
            for x in (valori or [])
            if str(x).strip()
        )
    )


# =========================================================
# QUERY
# =========================================================

def costruisci_query() -> tuple[str, list[object]]:
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

    sport_list = [x.upper() for x in _lista_pulita(DES_SPORT_LIST)]
    if sport_list:
        placeholders = ",".join(["%s"] * len(sport_list))
        where_clauses.append(
            f"""
            NOT EXISTS (
                SELECT 1
                FROM Ticket_Detail td_sport
                WHERE td_sport.id_ticket = tg.id_ticket
                  AND UPPER(TRIM(COALESCE(td_sport.des_sport, '')))
                      NOT IN ({placeholders})
            )
            """
        )
        params.extend(sport_list)

    cod_manif_list = _lista_pulita(COD_MANIF_LIST)
    if cod_manif_list:
        placeholders = ",".join(["%s"] * len(cod_manif_list))
        where_clauses.append(
            f"""
            EXISTS (
                SELECT 1
                FROM Ticket_Detail td_manif
                WHERE td_manif.id_ticket = tg.id_ticket
                  AND TRIM(CAST(td_manif.cod_manif AS CHAR))
                      IN ({placeholders})
            )
            """
        )
        params.extend(cod_manif_list)

    des_scom_list = _lista_pulita(DES_SCOM_LIST)
    if des_scom_list:
        placeholders = ",".join(["%s"] * len(des_scom_list))
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
                    ) IN ({placeholders})
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
            td.cod_manif,
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
# NORMALIZZAZIONE E FILTRI QUOTA
# =========================================================

def normalizza_output(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()

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
        "cod_manif",
        "des_manif",
        "des_scom",
        "des_eve",
        "cod_stato_esito",
    ]

    for col in colonne_testo:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()

    colonne_numeriche = [
        "num_eventi",
        "is_sistema",
        "importo_pagato_eur",
        "importo_vincita_eur",
        "quota",
    ]

    for col in colonne_numeriche:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["importo_pagato"] = (df["importo_pagato_eur"] / 100).round(2)
    df["importo_vincita_potenziale"] = (
        df["importo_vincita_eur"] / 100
    ).round(2)

    # Ticket_Detail.quota è memorizzata in centesimi:
    # 150 -> quota evento 1,50.
    df["quota_evento"] = (df["quota"] / 100).round(3)

    return df


def aggiungi_quota_ticket(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    quote_ticket = (
        df.groupby("id_ticket")["quota_evento"]
        .apply(
            lambda s: round(
                math.prod(
                    float(x)
                    for x in s.dropna()
                ),
                3,
            )
            if len(s.dropna()) == len(s) and len(s) > 0
            else float("nan")
        )
        .rename("quota_ticket")
        .reset_index()
    )

    return df.merge(
        quote_ticket,
        on="id_ticket",
        how="left",
        validate="many_to_one",
    )


def applica_filtri_quota(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    df = aggiungi_quota_ticket(df)

    ticket_validi = pd.Index(df["id_ticket"].drop_duplicates())

    if QUOTA_MIN_TUTTI_EVENTI is not None:
        validi_evento = (
            df.groupby("id_ticket")["quota_evento"]
            .min()
        )
        validi_evento = validi_evento[
            validi_evento >= float(QUOTA_MIN_TUTTI_EVENTI)
        ].index
        ticket_validi = ticket_validi.intersection(validi_evento)

    if QUOTA_TICKET_MIN is not None and float(QUOTA_TICKET_MIN) > 0:
        validi_ticket = (
            df.groupby("id_ticket")["quota_ticket"]
            .first()
        )
        validi_ticket = validi_ticket[
            validi_ticket >= float(QUOTA_TICKET_MIN)
        ].index
        ticket_validi = ticket_validi.intersection(validi_ticket)

    return df[df["id_ticket"].isin(ticket_validi)].copy()


# =========================================================
# OUTPUT
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
        "quota_ticket",
        "Mercato",
        "Importo Giocato",
        "Importo Vincita Potenziale",
    ]

    if df.empty:
        return pd.DataFrame(columns=colonne_output)

    ticket = (
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
        .sort_values(
            by=["nome_commerciale", "cf", "id_ticket"]
        )
        .reset_index(drop=True)
    )

    ticket = ticket.rename(
        columns={
            "des_scom": "Mercato",
            "importo_pagato": "Importo Giocato",
            "importo_vincita_potenziale":
                "Importo Vincita Potenziale",
        }
    )

    return ticket[colonne_output]


def crea_output_dettaglio(df: pd.DataFrame) -> pd.DataFrame:
    colonne_output = [
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
        "cod_manif",
        "des_manif",
        "Mercato",
        "des_eve",
        "quota_evento",
        "cod_stato_esito",
        "Importo Giocato",
        "Importo Vincita Potenziale",
    ]

    if df.empty:
        return pd.DataFrame(columns=colonne_output)

    dettaglio = df[
        [
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
            "cod_manif",
            "des_manif",
            "des_scom",
            "des_eve",
            "quota_evento",
            "cod_stato_esito",
            "importo_pagato",
            "importo_vincita_potenziale",
        ]
    ].copy()

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
        .sort_values(by=["id_ticket", "betradar_id"])
        .reset_index(drop=True)
    )[colonne_output]


def esegui_estrazione() -> tuple[pd.DataFrame, pd.DataFrame]:
    df = estrai_dati()

    if df.empty:
        return crea_output_ticket(df), crea_output_dettaglio(df)

    df = normalizza_output(df)
    df = applica_filtri_quota(df)

    if df.empty:
        return crea_output_ticket(df), crea_output_dettaglio(df)

    return crea_output_ticket(df), crea_output_dettaglio(df)


def salva_csv(df: pd.DataFrame, path: Path) -> None:
    df.to_csv(
        path,
        sep=";",
        index=False,
        encoding="utf-8-sig",
        decimal=",",
    )
    print(f"Salvato: {path}")


def main() -> None:
    print("Estrazione STARCASINO - 3moreEvents")
    print(f"Data vendita da: {DATA_VENDITA_DA}")
    print(f"Numero minimo eventi: {NUM_EVENTI_MIN}")
    print(f"Quota minima ogni evento: {QUOTA_MIN_TUTTI_EVENTI}")
    print(
        "Quota minima ticket: "
        f"{QUOTA_TICKET_MIN if QUOTA_TICKET_MIN else 'NESSUN FILTRO'}"
    )

    ticket, dettaglio = esegui_estrazione()

    salva_csv(ticket, OUTPUT_CSV)
    salva_csv(dettaglio, OUTPUT_DETTAGLIO_CSV)

    print(f"Ticket trovati: {len(ticket)}")
    print(f"Righe dettaglio: {len(dettaglio)}")


if __name__ == "__main__":
    main()
