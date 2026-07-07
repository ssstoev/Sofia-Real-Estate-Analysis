import re

import numpy as np
import pandas as pd


FURNISHED_NEGATIVE_PATTERNS = [
    r"\bнеобзаведен(?:а|о|и)?\b",
    r"\bне\s+е\s+обзаведен(?:а|о|и)?\b",
    r"\bбез\s+обзавеждане\b",
]

FURNISHED_POSITIVE_PATTERNS = [
    r"\bобзаведен(?:а|о|и)?\b",
    r"\bобзаведено\b",
    r"\bнапълно\s+обзаведен(?:а|о|и)?\b",
]

PUBLIC_TRANSPORT_PATTERNS = [
    r"до\s+метростанция\s*-?\s*до\s*10\s*мин(?:\.|ути)?\s*пеш",
    r"\bметро\b",
    r"\bметростанц(?:ия|ии)\b",
    r"\bавтобус(?:на\s+линия|на\s+спирка)?\b",
    r"\bспирка\b",
    r"\bтрамва(?:й|йна\s+спирка)\b",
    r"\bтролей(?:бус|бусна\s+спирка)?\b",
    r"\bградски\s+транспорт\b",
]


def transform_data(df: pd.DataFrame):
    """
    Transform raw listings into the ads_cleaned shape.
    """

    print("Begin transformation of data...\n")
    df = df.copy()

    if "floor" in df:
        df["building_total_floors"] = df["floor"].apply(extract_building_total_floors)
        df["is_first_floor"] = df["floor"].apply(extract_is_first_floor)
        df["is_last_floor"] = df["floor"].apply(extract_is_last_floor)
        df["floor"] = df["floor"].apply(extract_floor_number)

    if "extras" not in df:
        df["extras"] = ""
    if "description" not in df:
        df["description"] = ""

    text_blob = (df["extras"].fillna("").astype(str) + " " + df["description"].fillna("").astype(str))
    df["is_furnished"] = text_blob.apply(extract_is_furnished)
    df["near_public_transport"] = text_blob.apply(extract_near_public_transport)

    df["neighbourhood"] = (
        df["title"]
        .str.extract(r"в София,\s*(.*)", expand=False)
        .str.replace(r"\s*\([^)]*\)", "", regex=True)
        .str.strip()
    )

    df["type_of_estate"] = np.select(
        [
            df["title"].str.contains("Офис", na=False),
            df["title"].str.contains("Къща", na=False),
            df["title"].str.contains("Гараж", na=False),
            df["title"].str.contains("Парцел", na=False),
            df["title"].str.contains("Магазин", na=False),
        ],
        [   
            "офис",
            "къща",
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
    if pd.isna(floor_string):
        return np.nan
    match = re.search(r"-?\d+", str(floor_string))
    return int(match.group()) if match else np.nan


def extract_building_total_floors(floor_string: str):
    if pd.isna(floor_string):
        return np.nan
    normalized = str(floor_string).casefold().replace("\xa0", " ")
    numbers = re.findall(r"-?\d+", normalized)
    if not numbers:
        return np.nan
    return int(numbers[-1])


def extract_is_first_floor(floor_string: str):
    if pd.isna(floor_string):
        return None
    match = re.search(r"(-?\d+)", str(floor_string))
    if not match:
        return None
    return int(match.group(1)) == 1


def extract_is_last_floor(floor_string: str):
    if pd.isna(floor_string):
        return None
    normalized = str(floor_string).casefold().replace("\xa0", " ")
    normalized = re.sub(r"\s+", " ", normalized).strip()
    match = re.search(r"(-?\d+)\s*(?:от|ot|/|\\|-)+\s*(\d+)", normalized)
    if not match:
        return None
    return int(match.group(1)) == int(match.group(2))


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
    if "Мезонет" in text:
        return 5
    return np.nan


def extract_is_furnished(text: str) -> bool:
    if pd.isna(text):
        return False
    normalized = str(text).casefold()
    for pattern in FURNISHED_NEGATIVE_PATTERNS:
        if re.search(pattern, normalized):
            return False
    for pattern in FURNISHED_POSITIVE_PATTERNS:
        if re.search(pattern, normalized):
            return True
    return False


def extract_near_public_transport(text: str) -> bool:
    if pd.isna(text):
        return False
    normalized = str(text).casefold()
    return any(re.search(pattern, normalized) for pattern in PUBLIC_TRANSPORT_PATTERNS)
