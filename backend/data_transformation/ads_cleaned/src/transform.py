import re

import numpy as np
import pandas as pd


def transform_data(df: pd.DataFrame):
    """
    Transform raw listings into the ads_cleaned shape.
    """

    print("Begin transformation of data...\n")
    df = df.copy()

    if "floor" in df:
        df["floor"] = df["floor"].apply(extract_floor_number)

    df["neighbourhood"] = df["title"].str.extract(
        r"в София,\s*(.*)",
        expand=False,
    )

    df["type_of_estate"] = np.select(
        [
            df["title"].str.contains("Гараж", na=False),
            df["title"].str.contains("Парцел", na=False),
            df["title"].str.contains("Магазин", na=False),
        ],
        [
            "гараж",
            "парцел",
            "магазин",
        ],
        default="жилище",
    )

    df["nr_of_rooms"] = df["title"].apply(extract_number_of_rooms)

    df["total_price_eur"] = df["total_price_eur"].fillna(df["price_m2_eur"] * df["size_m2"])

    cleaned_dict = df.to_dict("records")
    print("Finished transformation of data!\n")

    return cleaned_dict


def extract_floor_number(floor_string: str):
    '''Extract the floor number from a string'''
    if pd.isna(floor_string):
        return np.nan

    match = re.search(r"-?\d+", str(floor_string))
    return int(match.group()) if match else np.nan


def extract_number_of_rooms(text):
    if pd.isna(text):
        return np.nan

    text = str(text)
    if "Едностаен" in text:
        return 1
    if "Двустаен" in text:
        return 2
    if "Тристаен" in text:
        return 3
    if "Четиристаен" in text:
        return 4
    if "Многостаен" in text:
        return 5

    return np.nan
