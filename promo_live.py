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

OUTPUT_CSV = BASE_PATH / "1_promolive_ticket_cf_filtrati.csv"
OUTPUT_DETTAGLIO_CSV = BASE_PATH / "2_promolive_dettaglio_eventi_filtrati.csv"


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

# Elenco dei codici manifestazione ammessi.
# PromoLive estrae ticket con UN SOLO EVENTO.
# L'unica manifestazione del ticket deve essere una di quelle inserite.
MANIFESTAZIONE_LIST = None

# Sport ammessi. Default: CALCIO.
# Con più valori viene applicata una logica OR.
DES_SPORT_LIST = ["CALCIO"]

# 0 = pre-match
# 1 = live
FLG_LIVE = 1

# Quota minima che deve essere rispettata da TUTTI gli eventi del ticket.
QUOTA_MIN_TUTTI_EVENTI = 1.5

# Codice fiscale opzionale.
CF = None

# Mercato / des_scom opzionale.
# None = nessun filtro.
# Se valorizzato, il ticket deve avere un solo mercato distinto
# e quel mercato deve appartenere all'elenco indicato.
DES_SCOM_LIST = None


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
    """
    PromoLive:

    - SOLO ticket singoli: tg.is_sistema = 0
    - SOLO ticket con un evento: tg.num_eventi = 1
    - l'unico evento deve avere manifestazione compresa in MANIFESTAZIONE_LIST
    - con più codici manifestazione si applica una logica OR:
      es. [309, 4774] -> manifestazione 309 OPPURE 4774
    - flg_live deve essere uguale al valore selezionato
    - des_sport deve essere uno degli sport selezionati
    - eventuale filtro CF
    - eventuale filtro mercato
    """

    manifestazione_list = _lista_pulita(MANIFESTAZIONE_LIST)

    if not manifestazione_list:
        raise ValueError("Devi inserire almeno un codice manifestazione.")

    col_data = "STR_TO_DATE(tg.data_ora_vend, '%%Y%%m%%d %%H:%%i:%%s')"
    placeholders = ",".join(["%s"] * len(manifestazione_list))

    where_clauses = [
        "tg.data_ora_vend IS NOT NULL",
        "tg.data_ora_vend <> ''",
        f"{col_data} >= %s",

        # PromoLive: solo singole e un solo evento.
        "tg.is_sistema = 0",
        "tg.num_eventi = 1",

        # L'unica riga evento deve essere LIVE / PRE-MATCH
        # secondo il valore scelto.
        "COALESCE(td.flg_live, -1) = %s",

        # Con più manifestazioni è un OR tramite IN (...).
        f"""
        TRIM(CAST(td.manifestazione AS CHAR))
            IN ({placeholders})
        """
    ]

    params: list[object] = [
        DATA_VENDITA_DA,
        int(FLG_LIVE),
    ]
    params.extend(manifestazione_list)


    sport_list = [x.upper() for x in _lista_pulita(DES_SPORT_LIST)]
    if sport_list:
        sport_placeholders = ",".join(["%s"] * len(sport_list))
        where_clauses.append(
            f"""
            UPPER(TRIM(COALESCE(td.des_sport, '')))
                IN ({sport_placeholders})
            """
        )
        params.extend(sport_list)

    if DES_STATO:
        where_clauses.append("tg.des_stato = %s")
        params.append(DES_STATO)

    filtro_cf = str(CF).strip() if CF is not None else ""
    if filtro_cf:
        where_clauses.append("UPPER(TRIM(tg.cf)) = %s")
        params.append(filtro_cf.upper())

    des_scom_list = _lista_pulita(DES_SCOM_LIST)
    if des_scom_list:
        mercato_placeholders = ",".join(["%s"] * len(des_scom_list))

        # Poiché num_eventi = 1, basta filtrare direttamente
        # il mercato dell'unico evento.
        where_clauses.append(
            f"""
            TRIM(COALESCE(td.des_scom, ''))
                IN ({mercato_placeholders})
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
            td.manifestazione,
            td.des_manif,
            td.des_scom,
            td.des_eve,
            td.quota,
            td.cod_stato_esito,
            td.flg_live

        FROM Ticket_General tg
        INNER JOIN Ticket_Detail td
            ON tg.id_ticket = td.id_ticket

        WHERE {where_sql}

        ORDER BY
            {col_data},
            tg.cf,
            tg.id_ticket,
            td.manifestazione,
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
        "manifestazione",
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
        "flg_live",
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
    # 150 -> quota evento 1,50.
    df["quota_evento"] = (
        df["quota"] / 100
    ).round(3)

    return df


# =========================================================
# FILTRO QUOTA
# =========================================================

def applica_filtro_quota_tutti_eventi(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Mantiene solo i ticket in cui TUTTI gli eventi hanno:
        quota_evento >= QUOTA_MIN_TUTTI_EVENTI
    """

    if df.empty:
        return df.copy()

    if QUOTA_MIN_TUTTI_EVENTI is None:
        return df.copy()

    ticket_validi = (
        df.groupby("id_ticket")["quota_evento"]
        .min()
    )

    ticket_validi = ticket_validi[
        ticket_validi >= float(QUOTA_MIN_TUTTI_EVENTI)
    ].index

    return df[
        df["id_ticket"].isin(ticket_validi)
    ].copy()


# =========================================================
# PRIMO TICKET PER CONTO GIOCO
# =========================================================

def mantieni_primo_ticket_per_conto(df: pd.DataFrame) -> pd.DataFrame:
    """
    Dopo aver applicato tutti i filtri PromoLive, mantiene solo
    il primo ticket cronologico per ogni conto gioco (num_conto), usando data_ora_vend.

    Lo stesso CF può quindi comparire più volte se possiede più conti gioco.
    """

    if df.empty:
        return df.copy()

    df = df.copy()

    # data_ora_vend nel DB è nel formato YYYYMMDD HH:MM:SS.
    df["_data_ora_vend_dt"] = pd.to_datetime(
        df["data_ora_vend"],
        format="%Y%m%d %H:%M:%S",
        errors="coerce",
    )

    # Per evitare risultati casuali in caso di stessa data/ora,
    # id_ticket viene usato come secondo criterio stabile.
    df = df.sort_values(
        by=["num_conto", "_data_ora_vend_dt", "id_ticket"],
        ascending=[True, True, True],
        na_position="last",
    )

    primi_ticket = (
        df.drop_duplicates(subset=["num_conto"], keep="first")["id_ticket"]
    )

    df = df[df["id_ticket"].isin(primi_ticket)].copy()

    return df.drop(columns=["_data_ora_vend_dt"], errors="ignore")


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
        "flg_live",
        "Manifestazioni",
        "Mercato",
        "Quota",
        "Importo Giocato",
        "Importo Vincita Potenziale",
    ]

    if df.empty:
        return pd.DataFrame(columns=colonne_output)

    # Riepilogo manifestazioni presenti nel ticket.
    riepilogo_manif = (
        df.groupby("id_ticket")["manifestazione"]
        .apply(
            lambda s: ",".join(
                dict.fromkeys(
                    str(x).strip()
                    for x in s
                    if str(x).strip()
                )
            )
        )
        .rename("Manifestazioni")
        .reset_index()
    )

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
                "flg_live",
                "des_scom",
                "quota_evento",
                "importo_pagato",
                "importo_vincita_potenziale",
            ]
        ]
        .drop_duplicates(subset=["id_ticket"])
        .merge(
            riepilogo_manif,
            on="id_ticket",
            how="left",
            validate="one_to_one",
        )
        .sort_values(
            by=["nome_commerciale", "cf", "id_ticket"]
        )
        .reset_index(drop=True)
    )

    ticket = ticket.rename(
        columns={
            "des_scom": "Mercato",
            "quota_evento": "Quota",
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
        "flg_live",
        "manifestazione",
        "betradar_id",
        "des_sport",
        "des_manif",
        "Mercato",
        "des_eve",
        "Quota",
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
            "flg_live",
            "manifestazione",
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
    ].copy()

    dettaglio = dettaglio.rename(
        columns={
            "des_scom": "Mercato",
            "quota_evento": "Quota",
            "importo_pagato": "Importo Giocato",
            "importo_vincita_potenziale":
                "Importo Vincita Potenziale",
        }
    )

    return (
        dettaglio
        .sort_values(
            by=["id_ticket", "manifestazione", "betradar_id"],
            na_position="last",
        )
        .reset_index(drop=True)
    )[colonne_output]


# =========================================================
# FUNZIONE PRINCIPALE PER STREAMLIT
# =========================================================

def esegui_estrazione() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Restituisce:
    1. dataframe ticket: una riga per id_ticket
    2. dataframe dettaglio: una riga per evento
    """

    df = estrai_dati()

    if df.empty:
        return (
            crea_output_ticket(df),
            crea_output_dettaglio(df),
        )

    df = normalizza_output(df)
    df = applica_filtro_quota_tutti_eventi(df)

    # Dopo tutti i filtri PromoLive, conserva solo
    # il primo ticket cronologico per ogni conto gioco (num_conto).
    df = mantieni_primo_ticket_per_conto(df)

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
# MAIN LOCALE / GITHUB ACTIONS
# =========================================================

def main() -> None:
    print("Estrazione STARCASINO - PromoLive")
    print(f"Database: {DB_CONFIG['database']}")
    print(f"Data vendita da: {DATA_VENDITA_DA}")
    print(f"Manifestazioni: {MANIFESTAZIONE_LIST or 'NESSUNA'}")
    print("Numero eventi esatto: 1")
    print(f"flg_live: {FLG_LIVE}")
    print(f"Sport: {DES_SPORT_LIST or 'TUTTI'}")
    print(f"Filtro stato ticket: {DES_STATO or 'TUTTI'}")
    print(f"Filtro is_sistema: {IS_SISTEMA}")
    print(
        "Quota minima su tutti gli eventi: "
        f"{QUOTA_MIN_TUTTI_EVENTI}"
    )
    print(f"Mercato: {DES_SCOM_LIST or 'TUTTI'}")
    print(f"CF: {CF or 'TUTTI'}")
    print("Regola conto: solo primo ticket cronologico per ogni num_conto")

    ticket, dettaglio = esegui_estrazione()

    salva_csv(ticket, OUTPUT_CSV)
    salva_csv(dettaglio, OUTPUT_DETTAGLIO_CSV)

    print()
    print("Estrazione completata")
    print(f"Ticket trovati: {len(ticket)}")

    if not ticket.empty:
        print(f"CF unici: {ticket['cf'].nunique()}")

    print(f"Righe dettaglio eventi: {len(dettaglio)}")


if __name__ == "__main__":
    main()
