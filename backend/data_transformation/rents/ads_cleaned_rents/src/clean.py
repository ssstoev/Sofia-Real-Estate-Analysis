import pandas as pd
import numpy as np


def clean_data(conn):
    """
    Clean the ads_rents_raw table.
    - Convert fields to numeric
    - Convert fields to bool
    """

    print("Begin cleaning... \n")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ads_rents_raw WHERE status = 'done'")
    columns = [description[0] for description in cursor.description]
    rows = cursor.fetchall()

    df = pd.DataFrame(rows, columns=columns).copy()

    for col in ["price_m2_eur", "price_m2_bgn", "total_price_eur"]:
        if col in df:
            df[col] = (
                df[col]
                .astype("string")
                .str.replace(" ", "", regex=False)
                .str.replace(",", "", regex=False)
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "size_m2" in df:
        df["size_m2"] = pd.to_numeric(df["size_m2"], errors="coerce")

    for col in ["akt16", "broker_commision"]:
        if col in df:
            df[col] = df[col].apply(convert_to_bool)

    print("Finished cleaning! \n")
    return df


def convert_to_bool(value: str):
    if pd.isna(value):
        return np.nan

    normalized = str(value).strip().casefold()
    if normalized == "да":
        return True
    if normalized == "не":
        return False

    return np.nan
