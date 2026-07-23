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

OUTPUT_CSV = BASE_PATH / "1_5evetswin_ticket_classificati.csv"
OUTPUT_DETTAGLIO_CSV = BASE_PATH / "2_5evetswin_dettaglio_eventi.csv"


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

# Lista opzionale di Betradar ID.
# None oppure [] = nessun filtro.
BETRADAR_ID_LIST = None

# Quota minima su tutti gli eventi del ticket.
# None = nessun filtro quota.
QUOTA_MIN_TUTTI_EVENTI = 1.5

# Codice fiscale opzionale.
CF = None

# Mercato / des_scom opzionale.
# None = nessun filtro.
DES_SCOM_LIST = None


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
    Estrae SOLO ticket composti esattamente dai Betradar ID inseriti.

    Esempio:
    5 Betradar ID inseriti -> prende soltanto ticket con:
    - tg.num_eventi = 5
    - esattamente 5 righe/eventi in Ticket_Detail
    - esattamente quei 5 Betradar ID
    - nessun Betradar diverso o aggiuntivo
    """

    betradar_list = list(dict.fromkeys(
        str(x).strip()
        for x in (BETRADAR_ID_LIST or [])
        if str(x).strip()
    ))

    if not betradar_list:
        raise ValueError("Devi inserire almeno un Betradar ID.")

    num_eventi_attesi = len(betradar_list)
    col_data = "STR_TO_DATE(tg.data_ora_vend, '%%Y%%m%%d %%H:%%i:%%s')"
    placeholders = ",".join(["%s"] * len(betradar_list))

    where_clauses = [
        "tg.data_ora_vend IS NOT NULL",
        "tg.data_ora_vend <> ''",
        f"{col_data} >= %s",
        "tg.num_eventi = %s",
        "tg.is_sistema = %s",
        f"""
        tg.id_ticket IN (
            SELECT td_match.id_ticket
            FROM Ticket_Detail td_match
            GROUP BY td_match.id_ticket
            HAVING
                COUNT(*) = %s
                AND COUNT(
                    DISTINCT TRIM(CAST(td_match.betradar_id AS CHAR))
                ) = %s
                AND SUM(
                    CASE
                        WHEN TRIM(CAST(td_match.betradar_id AS CHAR))
                            IN ({placeholders})
                        THEN 1
                        ELSE 0
                    END
                ) = %s
        )
        """
    ]

    params: list[object] = [
        DATA_VENDITA_DA,
        num_eventi_attesi,
        int(IS_SISTEMA),
        num_eventi_attesi,
        num_eventi_attesi,
    ]
    params.extend(betradar_list)
    params.append(num_eventi_attesi)

    if DES_STATO:
        where_clauses.append("tg.des_stato = %s")
        params.append(DES_STATO)

    filtro_cf = str(CF).strip() if CF is not None else ""
    if filtro_cf:
        where_clauses.append("UPPER(TRIM(tg.cf)) = %s")
        params.append(filtro_cf.upper())

    if DES_SCOM_LIST:
        des_scom_list = list(dict.fromkeys(
            str(x).strip()
            for x in DES_SCOM_LIST
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

    df["quota_evento"] = (
        df["quota"] / 100
    ).round(3)

    df["cod_stato_esito"] = (
        df["cod_stato_esito"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )

    return df


# =========================================================
# FILTRO QUOTA
# =========================================================

def applica_filtro_quota_tutti_eventi(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Mantiene solo i ticket in cui TUTTI gli eventi hanno
    quota_evento >= QUOTA_MIN_TUTTI_EVENTI.
    """

    if df.empty:
        return df

    if QUOTA_MIN_TUTTI_EVENTI is None:
        return df.copy()

    ticket_validi = (
        df.groupby("id_ticket")["quota_evento"]
        .min()
        .reset_index()
    )

    ticket_validi = ticket_validi[
        ticket_validi["quota_evento"]
        >= float(QUOTA_MIN_TUTTI_EVENTI)
    ]["id_ticket"]

    return df[
        df["id_ticket"].isin(ticket_validi)
    ].copy()


# =========================================================
# CLASSIFICAZIONE EVENTS WIN
# =========================================================

def calcola_classificazione_events_win(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Per ogni id_ticket:
    - conta gli eventi totali presenti nel dettaglio
    - conta gli eventi con cod_stato_esito = WI
    - assegna classificazione:
        5 WI -> 5eventsWin
        4 WI -> 4eventsWin
        ...
        1 WI -> 1eventsWin
        0 WI -> 0eventsWin

    La classificazione dipende dal numero di WI,
    non dal numero totale di eventi del ticket.
    """

    if df.empty:
        return df

    richieste = {
        "id_ticket",
        "num_eventi",
        "cod_stato_esito",
    }

    mancanti = richieste - set(df.columns)

    if mancanti:
        raise ValueError(
            "Colonne mancanti per classificazione: "
            f"{sorted(mancanti)}"
        )

    riepilogo = (
        df.groupby("id_ticket", as_index=False)
        .agg(
            num_eventi=("num_eventi", "first"),
            eventi_dettaglio=("id_ticket", "size"),
            eventi_vinti=(
                "cod_stato_esito",
                lambda s: int(
                    s.astype(str)
                    .str.strip()
                    .str.upper()
                    .eq("WI")
                    .sum()
                ),
            ),
        )
    )

    riepilogo["eventi_sbagliati"] = (
        riepilogo["num_eventi"].astype(int)
        - riepilogo["eventi_vinti"].astype(int)
    )

    riepilogo["classificazione_events_win"] = (
        riepilogo["eventi_vinti"]
        .astype(int)
        .astype(str)
        + "eventsWin"
    )

    return riepilogo


def aggiungi_classificazione_al_dettaglio(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Aggiunge a tutte le righe di dettaglio:
    - eventi_vinti
    - classificazione_events_win
    """

    if df.empty:
        return df

    classificazione = calcola_classificazione_events_win(df)

    return df.merge(
        classificazione[
            [
                "id_ticket",
                "eventi_dettaglio",
                "eventi_vinti",
                "eventi_sbagliati",
                "classificazione_events_win",
            ]
        ],
        on="id_ticket",
        how="left",
        validate="many_to_one",
    )


# =========================================================
# OUTPUT TICKET
# =========================================================

def crea_output_ticket(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Una riga per ticket con classificazione eventsWin.
    """

    if df.empty:
        return pd.DataFrame(
            columns=[
                "id_ticket",
                "cf",
                "num_conto",
                "nome_commerciale",
                "des_stato",
                "data_ora_vend",
                "num_eventi",
                "eventi_vinti",
                "eventi_sbagliati",
                "classificazione_events_win",
                "Mercato",
                "Importo Giocato",
                "Importo Vincita Potenziale",
            ]
        )

    df_classificato = aggiungi_classificazione_al_dettaglio(df)

    colonne_ticket = [
        "id_ticket",
        "cf",
        "num_conto",
        "nome_commerciale",
        "des_stato",
        "data_ora_vend",
        "num_eventi",
        "eventi_vinti",
        "eventi_sbagliati",
        "classificazione_events_win",
        "des_scom",
        "importo_pagato",
        "importo_vincita_potenziale",
    ]

    mancanti = [
        c
        for c in colonne_ticket
        if c not in df_classificato.columns
    ]

    if mancanti:
        raise ValueError(
            "Colonne mancanti per output ticket: "
            f"{mancanti}"
        )

    ticket = (
        df_classificato[colonne_ticket]
        .drop_duplicates(subset=["id_ticket"])
        .sort_values(
            by=[
                "classificazione_events_win",
                "num_eventi",
                "cf",
                "id_ticket",
            ],
            ascending=[
                False,
                False,
                True,
                True,
            ],
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

    return ticket


# =========================================================
# OUTPUT DETTAGLIO
# =========================================================

def crea_output_dettaglio(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Mantiene tutte le righe evento dei ticket estratti.
    """

    if df.empty:
        return pd.DataFrame()

    dettaglio = aggiungi_classificazione_al_dettaglio(df)

    colonne = [
        "id_ticket",
        "cf",
        "num_conto",
        "nome_commerciale",
        "des_stato",
        "data_ora_vend",
        "num_eventi",
        "eventi_vinti",
        "eventi_sbagliati",
        "classificazione_events_win",
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
        c
        for c in colonne
        if c in dettaglio.columns
    ]

    dettaglio = dettaglio[colonne_presenti].copy()

    dettaglio = dettaglio.rename(
        columns={
            "des_scom": "Mercato",
            "importo_pagato": "Importo Giocato",
            "importo_vincita_potenziale":
                "Importo Vincita Potenziale",
        }
    )

    dettaglio = dettaglio.sort_values(
        by=[
            "id_ticket",
            "betradar_id",
        ],
        na_position="last",
    ).reset_index(drop=True)

    return dettaglio


# =========================================================
# SALVATAGGIO CSV
# =========================================================

def salva_csv(
    df: pd.DataFrame,
    path: Path,
) -> None:
    df.to_csv(
        path,
        sep=";",
        index=False,
        encoding="utf-8-sig",
        decimal=",",
    )

    print(f"Salvato: {path}")


# =========================================================
# FUNZIONE COMPLETA PER STREAMLIT
# =========================================================

def esegui_estrazione() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Funzione principale pensata per essere richiamata
    da app_starcasino.py.

    Restituisce:
    1. dataframe ticket: una riga per id_ticket
    2. dataframe dettaglio: tutte le righe evento
    """

    df = estrai_dati()

    if df.empty:
        return (
            crea_output_ticket(df),
            crea_output_dettaglio(df),
        )

    df = normalizza_output(df)
    df = applica_filtro_quota_tutti_eventi(df)

    if df.empty:
        return (
            crea_output_ticket(df),
            crea_output_dettaglio(df),
        )

    ticket = crea_output_ticket(df)
    dettaglio = crea_output_dettaglio(df)

    return ticket, dettaglio


# =========================================================
# MAIN LOCALE / GITHUB ACTIONS
# =========================================================

def main() -> None:
    print("Estrazione STARCASINO - 5evetsWin")
    print(f"Database: {DB_CONFIG['database']}")
    print(f"Data vendita da: {DATA_VENDITA_DA}")
    print(f"Numero eventi esatto: {len(BETRADAR_ID_LIST or [])}")
    print(
        "Regola eventi: "
        f"num_eventi = {len(BETRADAR_ID_LIST or [])}"
    )
    print(f"Filtro stato ticket: {DES_STATO or 'TUTTI'}")
    print(f"Filtro is_sistema: {IS_SISTEMA}")
    print(
        f"Quota minima su tutti gli eventi: "
        f"{QUOTA_MIN_TUTTI_EVENTI}"
    )
    print(
        f"Betradar ID: "
        f"{BETRADAR_ID_LIST if BETRADAR_ID_LIST else 'TUTTI'}"
    )
    print(
        f"Mercato: "
        f"{DES_SCOM_LIST if DES_SCOM_LIST else 'TUTTI'}"
    )
    print(f"CF: {CF if CF else 'TUTTI'}")

    ticket, dettaglio = esegui_estrazione()

    salva_csv(ticket, OUTPUT_CSV)
    salva_csv(dettaglio, OUTPUT_DETTAGLIO_CSV)

    print()
    print("Estrazione completata")
    print(f"Ticket trovati: {len(ticket)}")

    if not ticket.empty:
        print(
            f"CF unici: "
            f"{ticket['cf'].nunique()}"
        )

        print()
        print("Classificazioni:")

        print(
            ticket[
                "classificazione_events_win"
            ]
            .value_counts()
            .sort_index(ascending=False)
            .to_string()
        )

    print(
        f"Righe dettaglio eventi: "
        f"{len(dettaglio)}"
    )


if __name__ == "__main__":
    main()
