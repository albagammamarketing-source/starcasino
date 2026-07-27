from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import pymysql

BASE_PATH = Path("output")
BASE_PATH.mkdir(parents=True, exist_ok=True)
OUTPUT_CSV = BASE_PATH / "1_promo_betradar_ticket.csv"
OUTPUT_DETTAGLIO_CSV = BASE_PATH / "2_promo_betradar_dettaglio_eventi.csv"

DB_PORT = int(os.getenv("PIPELINE_DB_PORT", "3306"))
DB_CONFIG = {
    "user": os.getenv("PIPELINE_DB_USER", "dbalba11"),
    "password": os.getenv("DB_PASSWORD") or os.getenv("PIPELINE_DB_PASSWORD"),
    "host": os.getenv("PIPELINE_DB_HOST", "194.163.157.255"),
    "database": "AnalisiTickets_STARCASINO",
}

DATA_VENDITA_DA = "2026-05-01 00:00:00"
DES_STATO = None
IS_SISTEMA = 0
BETRADAR_ID_LIST = ["61526570", "61061655", "61624622"]
QUOTA_MIN_TUTTI_EVENTI = 1.5
CF = None
DES_SCOM_LIST = None


def _lista_pulita(valori) -> list[str]:
    return list(dict.fromkeys(str(x).strip() for x in (valori or []) if str(x).strip()))


def apri_connessione(cfg: dict):
    if not cfg.get("password"):
        raise RuntimeError("Password database non configurata: imposta DB_PASSWORD o PIPELINE_DB_PASSWORD.")
    return pymysql.connect(
        host=cfg["host"], port=DB_PORT, user=cfg["user"], password=cfg["password"],
        database=cfg["database"], charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor,
    )


def costruisci_query() -> tuple[str, list[object]]:
    betradar = _lista_pulita(BETRADAR_ID_LIST)
    if not betradar:
        raise ValueError("Devi inserire almeno un Betradar ID.")

    n = len(betradar)
    col_data = "STR_TO_DATE(tg.data_ora_vend, '%%Y%%m%%d %%H:%%i:%%s')"
    ph = ",".join(["%s"] * n)
    where = [
        "tg.data_ora_vend IS NOT NULL", "tg.data_ora_vend <> ''", f"{col_data} >= %s",
        "tg.num_eventi = %s", "tg.is_sistema = %s",
        f"""tg.id_ticket IN (
            SELECT td_match.id_ticket FROM Ticket_Detail td_match
            GROUP BY td_match.id_ticket
            HAVING COUNT(*) = %s
               AND COUNT(DISTINCT TRIM(CAST(td_match.betradar_id AS CHAR))) = %s
               AND SUM(CASE WHEN TRIM(CAST(td_match.betradar_id AS CHAR)) IN ({ph}) THEN 1 ELSE 0 END) = %s
        )""",
    ]
    params: list[object] = [DATA_VENDITA_DA, n, int(IS_SISTEMA), n, n, *betradar, n]

    if DES_STATO:
        where.append("tg.des_stato = %s")
        params.append(DES_STATO)
    if CF and str(CF).strip():
        where.append("UPPER(TRIM(tg.cf)) = %s")
        params.append(str(CF).strip().upper())

    mercati = _lista_pulita(DES_SCOM_LIST)
    if mercati:
        mph = ",".join(["%s"] * len(mercati))
        where.append(f"""tg.id_ticket IN (
            SELECT td_scom.id_ticket FROM Ticket_Detail td_scom
            GROUP BY td_scom.id_ticket
            HAVING COUNT(DISTINCT TRIM(COALESCE(td_scom.des_scom, ''))) = 1
               AND MAX(TRIM(COALESCE(td_scom.des_scom, ''))) IN ({mph})
        )""")
        params.extend(mercati)

    query = f"""
        SELECT tg.id_ticket, tg.num_conto, tg.cf, tg.nome_commerciale, tg.num_eventi,
               tg.des_stato, tg.is_sistema, tg.data_ora_vend,
               tg.importo_pagato_eur, tg.importo_vincita_eur,
               td.betradar_id, td.des_sport, td.cod_manif, td.des_manif,
               td.des_scom, td.des_eve, td.quota, td.cod_stato_esito
        FROM Ticket_General tg
        INNER JOIN Ticket_Detail td ON tg.id_ticket = td.id_ticket
        WHERE {' AND '.join(where)}
        ORDER BY {col_data}, tg.cf, tg.id_ticket, td.betradar_id
    """
    return query, params


def estrai_dati() -> pd.DataFrame:
    query, params = costruisci_query()
    conn = apri_connessione(DB_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return pd.DataFrame(cur.fetchall())
    finally:
        conn.close()


def normalizza_output(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    df = df.copy()
    for col in ["id_ticket", "num_conto", "cf", "nome_commerciale", "des_stato", "data_ora_vend",
                "betradar_id", "des_sport", "cod_manif", "des_manif", "des_scom", "des_eve", "cod_stato_esito"]:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()
    for col in ["num_eventi", "is_sistema", "importo_pagato_eur", "importo_vincita_eur", "quota"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["importo_pagato"] = (df["importo_pagato_eur"] / 100).round(2)
    df["importo_vincita_potenziale"] = (df["importo_vincita_eur"] / 100).round(2)
    df["quota_evento"] = (df["quota"] / 100).round(3)
    return df


def applica_filtro_quota_tutti_eventi(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or QUOTA_MIN_TUTTI_EVENTI is None:
        return df.copy()
    validi = df.groupby("id_ticket")["quota_evento"].min()
    validi = validi[validi >= float(QUOTA_MIN_TUTTI_EVENTI)].index
    return df[df["id_ticket"].isin(validi)].copy()


def crea_output_ticket(df: pd.DataFrame) -> pd.DataFrame:
    cols = ["id_ticket", "cf", "num_conto", "nome_commerciale", "des_stato", "data_ora_vend",
            "num_eventi", "Mercato", "Importo Giocato", "Importo Vincita Potenziale"]
    if df.empty:
        return pd.DataFrame(columns=cols)
    out = df[["id_ticket", "cf", "num_conto", "nome_commerciale", "des_stato", "data_ora_vend",
              "num_eventi", "des_scom", "importo_pagato", "importo_vincita_potenziale"]].drop_duplicates("id_ticket")
    return out.rename(columns={"des_scom": "Mercato", "importo_pagato": "Importo Giocato",
                               "importo_vincita_potenziale": "Importo Vincita Potenziale"})[cols].reset_index(drop=True)


def crea_output_dettaglio(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    cols = ["id_ticket", "cf", "num_conto", "nome_commerciale", "des_stato", "data_ora_vend", "num_eventi",
            "is_sistema", "betradar_id", "des_sport", "cod_manif", "des_manif", "des_scom", "des_eve",
            "quota_evento", "cod_stato_esito", "importo_pagato", "importo_vincita_potenziale"]
    return df[cols].rename(columns={"des_scom": "Mercato", "importo_pagato": "Importo Giocato",
                                    "importo_vincita_potenziale": "Importo Vincita Potenziale"}).reset_index(drop=True)


def esegui_estrazione() -> tuple[pd.DataFrame, pd.DataFrame]:
    df = applica_filtro_quota_tutti_eventi(normalizza_output(estrai_dati()))
    return crea_output_ticket(df), crea_output_dettaglio(df)


def salva_csv(df: pd.DataFrame, path: Path) -> None:
    df.to_csv(path, sep=";", index=False, encoding="utf-8-sig", decimal=",")


def main() -> None:
    ticket, dettaglio = esegui_estrazione()
    salva_csv(ticket, OUTPUT_CSV); salva_csv(dettaglio, OUTPUT_DETTAGLIO_CSV)
    print(f"Ticket: {len(ticket)} | Dettaglio: {len(dettaglio)}")


if __name__ == "__main__":
    main()
