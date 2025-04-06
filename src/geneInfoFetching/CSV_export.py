import logging

import pandas as pd


def export_to_csv(df: pd.DataFrame, filename: str):
    df.to_csv(filename, index=False)
    logging.info(f"Exported to {filename}")