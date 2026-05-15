from __future__ import annotations

import os
import smtplib
from pathlib import Path
from email.message import EmailMessage

import pandas as pd
import pymysql


# =========================================================
# CONFIGURAZIONE PERCORSI
# =========================================================
BASE_PATH = Path(r"G:\Il mio Drive\progetti phyton\61_starcasino")
BASE_PATH.mkdir(parents=True, exist_ok=True)

OUTPUT_CSV = BASE_PATH / "1_starcasino_ticket_cf_filtrati.csv"
OUTPUT_DETTAGLIO_CSV = BASE_PATH / "2_starcasino_dettaglio_eventi_filtrati.csv"


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
# SETTING FILTRI
# =========================================================

# Estrae tutti i ticket venduti da questa data in poi
DATA_VENDITA_DA = "2026-05-01 00:00:00"

# None = prende tutti gli stati
DES_STATO = None

# 0 = ticket non sistema
# 1 = sistemi
IS_SISTEMA = 0

COD_STATO_ESITO_ESCLUSO = None

# Il ticket deve contenere ESATTAMENTE questi betradar_id.
# L'ordine non conta.
# Se metti 3 codici, cerca ticket con 3 eventi.
# Se metti 4 codici, cerca ticket con 4 eventi.
BETRADAR_ID_LIST = [
    "61526570",
    "61061655",
    "61624622",
]

# Tutti gli eventi del ticket devono avere quota >= questa soglia.
# Se vuoi disattivare il filtro, metti None.
QUOTA_MIN_TUTTI_EVENTI = 1.5

# Filtro opzionale CF singolo
CF = None


# =========================================================
# CONFIGURAZIONE EMAIL
# =========================================================
INVIA_EMAIL = True

EMAIL_SENDER = "albagamma.marketing@gmail.com"
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "INSERISCI_PASSWORD_EMAIL")
EMAIL_SMTP_SERVER = "smtp.gmail.com"
EMAIL_SMTP_PORT = 587

EMAIL_RECEIVERS = [
    "dario.guarriello@gmail.com",
]


# =========================================================
# DB
# =========================================================
def apri_connessione(cfg: dict):
    return pymysql.connect(
        host=cfg["host"],
        port=DB_PORT,
        user=cfg["user"],
        password=cfg["password"],
        database=cfg["database"],
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )


def costruisci_query() -> tuple[str, list[object]]:
    col_data = "STR_TO_DATE(tg.data_ora_vend, '%%Y%%m%%d %%H:%%i:%%s')"

    betradar_list = [
        str(x).strip()
        for x in BETRADAR_ID_LIST
        if str(x).strip()
    ]

    num_eventi_attesi = len(betradar_list)

    where_clauses = [
        "tg.is_sistema = %s",
        "tg.data_ora_vend IS NOT NULL",
        "tg.data_ora_vend <> ''",
        f"{col_data} >= %s",
    ]

    params: list[object] = [
        IS_SISTEMA,
        DATA_VENDITA_DA,
    ]

    if DES_STATO:
        where_clauses.append("tg.des_stato = %s")
        params.append(DES_STATO)

    if COD_STATO_ESITO_ESCLUSO:
        where_clauses.append(
            """
            NOT EXISTS (
                SELECT 1
                FROM Ticket_Detail td_lo
                WHERE td_lo.id_ticket = tg.id_ticket
                  AND UPPER(TRIM(COALESCE(td_lo.cod_stato_esito, ''))) = %s
            )
            """
        )
        params.append(COD_STATO_ESITO_ESCLUSO)

    if betradar_list:
        placeholders = ",".join(["%s"] * len(betradar_list))

        # Il numero eventi del ticket deve essere uguale al numero di betradar_id indicati
        where_clauses.append("tg.num_eventi = %s")
        params.append(num_eventi_attesi)

        # Il ticket deve contenere esattamente quei betradar_id, senza altri eventi fuori lista.
        # L'ordine non conta.
        where_clauses.append(
            f"""
            tg.id_ticket IN (
                SELECT td_match.id_ticket
                FROM Ticket_Detail td_match
                GROUP BY td_match.id_ticket
                HAVING
                    COUNT(*) = %s
                    AND COUNT(DISTINCT TRIM(CAST(td_match.betradar_id AS CHAR))) = %s
                    AND SUM(
                        CASE
                            WHEN TRIM(CAST(td_match.betradar_id AS CHAR)) IN ({placeholders})
                            THEN 1
                            ELSE 0
                        END
                    ) = %s
            )
            """
        )

        params.append(num_eventi_attesi)
        params.append(num_eventi_attesi)
        params.extend(betradar_list)
        params.append(num_eventi_attesi)

    filtro_cf = str(CF).strip() if CF is not None else ""
    if filtro_cf:
        where_clauses.append("tg.cf = %s")
        params.append(filtro_cf)

    where_sql = "\n        AND ".join(where_clauses)

    query = f"""
        SELECT
            tg.id_ticket,
            tg.cf,
            tg.nome_commerciale,
            tg.num_conto,
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
            td.quota
        FROM Ticket_General tg
        INNER JOIN Ticket_Detail td
            ON tg.id_ticket = td.id_ticket
        WHERE {where_sql}
        ORDER BY {col_data}, tg.cf, tg.id_ticket
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
# UTILS
# =========================================================
def normalizza_output(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

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
    df["importo_vincita_potenziale"] = (df["importo_vincita_eur"] / 100).round(2)
    df["quota_evento"] = (df["quota"] / 100).round(3)

    return df


def applica_filtro_quota_tutti_eventi(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    if QUOTA_MIN_TUTTI_EVENTI is None:
        return df

    ticket_validi = (
        df.groupby("id_ticket")["quota_evento"]
        .min()
        .reset_index()
    )

    ticket_validi = ticket_validi[
        ticket_validi["quota_evento"] >= QUOTA_MIN_TUTTI_EVENTI
    ]["id_ticket"]

    return df[df["id_ticket"].isin(ticket_validi)].copy()


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
# EMAIL
# =========================================================
def invia_email_con_allegati(
    oggetto: str,
    corpo: str,
    allegati: list[Path],
) -> None:
    if not INVIA_EMAIL:
        print("Invio email disattivato.")
        return

    if not EMAIL_PASSWORD or EMAIL_PASSWORD == "INSERISCI_PASSWORD_EMAIL":
        print("Email non inviata: password email non configurata.")
        return

    if not EMAIL_RECEIVERS:
        print("Email non inviata: nessun destinatario configurato.")
        return

    msg = EmailMessage()
    msg["From"] = EMAIL_SENDER
    msg["To"] = ", ".join(EMAIL_RECEIVERS)
    msg["Subject"] = oggetto
    msg.set_content(corpo)

    for allegato in allegati:
        if not allegato.exists():
            print(f"Allegato non trovato: {allegato}")
            continue

        with open(allegato, "rb") as f:
            file_data = f.read()

        msg.add_attachment(
            file_data,
            maintype="text",
            subtype="csv",
            filename=allegato.name,
        )

    with smtplib.SMTP(EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
        smtp.send_message(msg)

    print("Email inviata correttamente.")


# =========================================================
# MAIN
# =========================================================
def main() -> None:
    print("Estrazione dati STARCASINO")
    print(f"Database: {DB_CONFIG['database']}")
    print(f"Data vendita da: {DATA_VENDITA_DA}")
    print(f"Filtro des_stato: {DES_STATO if DES_STATO else 'TUTTI'}")
    print(f"Filtro is_sistema: {IS_SISTEMA}")
    print(f"Betradar_id richiesti: {BETRADAR_ID_LIST}")
    print(f"Numero eventi richiesto: {len(BETRADAR_ID_LIST)}")
    print(f"Quota minima su tutti gli eventi: {QUOTA_MIN_TUTTI_EVENTI}")

    df = estrai_dati()

    if df.empty:
        print("Nessun dato trovato da database.")

        ticket_vuoto = pd.DataFrame(
            columns=[
                "id_ticket",
                "cf",
                "nome_commerciale",
                "data_ora_vend",
                "importo_pagato",
                "importo_vincita_potenziale",
            ]
        )

        dettaglio_vuoto = pd.DataFrame()

        salva_csv(ticket_vuoto, OUTPUT_CSV)
        salva_csv(dettaglio_vuoto, OUTPUT_DETTAGLIO_CSV)
        return

    print(f"Righe lette da database: {len(df)}")
    print(f"Ticket unici prima filtro quota: {df['id_ticket'].nunique()}")

    df = normalizza_output(df)
    df = applica_filtro_quota_tutti_eventi(df)

    if df.empty:
        print("Nessun ticket valido dopo filtro quota minima su tutti gli eventi.")

        ticket_vuoto = pd.DataFrame(
            columns=[
                "id_ticket",
                "cf",
                "nome_commerciale",
                "data_ora_vend",
                "importo_pagato",
                "importo_vincita_potenziale",
            ]
        )

        dettaglio_vuoto = pd.DataFrame()

        salva_csv(ticket_vuoto, OUTPUT_CSV)
        salva_csv(dettaglio_vuoto, OUTPUT_DETTAGLIO_CSV)
        return

    print(f"Ticket unici dopo filtro quota: {df['id_ticket'].nunique()}")

    dettaglio_cols = [
        "id_ticket",
        "cf",
        "num_conto",
        "nome_commerciale",
        "num_eventi",
        "des_stato",
        "is_sistema",
        "data_ora_vend",
        "betradar_id",
        "des_sport",
        "des_manif",
        "des_scom",
        "des_eve",
        "quota_evento",
        "importo_pagato",
        "importo_vincita_potenziale",
    ]

    dettaglio = df[dettaglio_cols].copy()

    ticket_cf = (
        df[
            [
                "id_ticket",
                "cf",
                "num_conto",
                "nome_commerciale",
                "data_ora_vend",
                "importo_pagato",
                "importo_vincita_potenziale",
            ]
        ]
        .drop_duplicates(subset=["id_ticket", "cf"])
        .sort_values(by=["cf", "id_ticket"])
        .reset_index(drop=True)
    )

    salva_csv(ticket_cf, OUTPUT_CSV)
    salva_csv(dettaglio, OUTPUT_DETTAGLIO_CSV)

    invia_email_con_allegati(
        oggetto="Estrazione STARCASINO - Ticket filtrati",
        corpo=(
            "Ciao,\n\n"
            "in allegato trovi i CSV generati dall'estrazione STARCASINO.\n\n"
            f"Ticket unici: {ticket_cf['id_ticket'].nunique()}\n"
            f"CF unici: {ticket_cf['cf'].nunique()}\n"
            f"Righe dettaglio eventi: {len(dettaglio)}\n\n"
            f"Data vendita da: {DATA_VENDITA_DA}\n"
            f"Filtro des_stato: {DES_STATO if DES_STATO else 'TUTTI'}\n"
            f"Filtro is_sistema: {IS_SISTEMA}\n"
            f"Betradar_id richiesti: {BETRADAR_ID_LIST}\n"
            f"Numero eventi richiesto: {len(BETRADAR_ID_LIST)}\n"
            f"Quota minima tutti eventi: {QUOTA_MIN_TUTTI_EVENTI}\n\n"
            "Script automatico."
        ),
        allegati=[OUTPUT_CSV, OUTPUT_DETTAGLIO_CSV],
    )

    print("\n✅ Estrazione completata")
    print(f"File ticket/CF: {OUTPUT_CSV}")
    print(f"File dettaglio eventi: {OUTPUT_DETTAGLIO_CSV}")
    print(f"Ticket unici trovati: {ticket_cf['id_ticket'].nunique()}")
    print(f"CF unici trovati: {ticket_cf['cf'].nunique()}")
    print(f"Righe dettaglio eventi: {len(dettaglio)}")


if __name__ == "__main__":
    main()
