
from functools import lru_cache
from pathlib import Path

import pandas as pd


# Find the main project folder
PROJECT_ROOT = Path(__file__).resolve().parents[1]
INTEGRATED_DIR = PROJECT_ROOT / "Data" / "Integrated"


@lru_cache(maxsize=1)
def load_data():

    required_files = [
        "order_level_analytics.csv",
        "order_items_enriched.csv",
        "geolocation_lookup.csv"
    ]

    missing_files = [
        filename
        for filename in required_files
        if not (INTEGRATED_DIR / filename).exists()
    ]

    if missing_files:
        raise FileNotFoundError(
            f"Missing integrated files: {missing_files}"
        )

    # Load integrated datasets
    order_level = pd.read_csv(
        INTEGRATED_DIR / "order_level_analytics.csv"
    )

    order_items = pd.read_csv(
        INTEGRATED_DIR / "order_items_enriched.csv"
    )

    geolocation = pd.read_csv(
        INTEGRATED_DIR / "geolocation_lookup.csv"
    )

    # Restore datetime format
    order_level["order_purchase_timestamp"] = pd.to_datetime(
        order_level["order_purchase_timestamp"],
        errors="coerce"
    )

    # Ensure financial and review columns are numeric
    numeric_columns = [
        "total_product_value",
        "total_freight_value",
        "total_payment_value",
        "average_review_score"
    ]

    for column in numeric_columns:
        if column in order_level.columns:
            order_level[column] = pd.to_numeric(
                order_level[column],
                errors="coerce"
            )

    if "price" in order_items.columns:
        order_items["price"] = pd.to_numeric(
            order_items["price"],
            errors="coerce"
        )

    print("Olist integrated datasets loaded successfully.")

    return order_level, order_items, geolocation

@lru_cache(maxsize=1)
def load_payments():

    payments_path = PROJECT_ROOT / "Data" / "Processed" / "payments_cleaned.csv"

    if not payments_path.exists():
        raise FileNotFoundError(
            f"Payment file not found: {payments_path}"
        )

    payments = pd.read_csv(payments_path)

    payments["payment_value"] = pd.to_numeric(
        payments["payment_value"],
        errors="coerce"
    )

    payments["payment_installments"] = pd.to_numeric(
        payments["payment_installments"],
        errors="coerce"
    )

    return payments
