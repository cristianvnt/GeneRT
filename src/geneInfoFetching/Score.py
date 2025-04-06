from pandas.core.interchange.dataframe_protocol import DataFrame
import pandas as pd


relation_score_map = {
    "activation": 1.0,
    "inhibition": -1.0,
    "phosphorylation": 0.75,
    "binding/association": 0.5,
    "expression": 0.8,
    "indirect effect": 0.3,
    "other": 0.0
}

def mappingScore(df):
    df["relation_score"] = df["relation_type"].map(relation_score_map)

    df.drop(columns=["relation_type"], inplace=True)