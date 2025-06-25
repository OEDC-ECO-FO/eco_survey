import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from collections import Counter
import pandas as pd



def get_regions_to_countries(df):
    """
    Returns a dictionary mapping each region to a sorted list of unique countries in that region.
    """
    regions_to_countries = (
        df.groupby("region")["country"]
        .unique()
        .apply(sorted)
        .to_dict()
    )
    return regions_to_countries


def filter_data(df, countries=None, topic=None, year_from=2000, year_to=2026):
    filtered = df.copy()
    if countries:
        filtered = filtered[filtered["country"].isin(countries)]
    if topic:
        filtered = filtered[filtered["assigned_topic"].apply(
            lambda d: isinstance(d, dict) and topic in d
        )]
    filtered = filtered[(filtered["year"] >= year_from) & (filtered["year"] <= year_to)]
    return filtered

def relevant_topics(df, text_type):
    if text_type == "finding":
        if "finding_topics" in df.columns:
            df = df.drop(columns=["recommendation_topics", "assigned_topic"], errors="ignore")
            return df.rename(columns={"finding_topics": "assigned_topic"})
    elif text_type == "recommendation":
        if "recommendation_topics" in df.columns:
            df = df.drop(columns=["finding_topics", "assigned_topic"], errors="ignore")
            return df.rename(columns={"recommendation_topics": "assigned_topic"})
    else:
        return df



def group_by_country_year(records):
    grouped = {}
    for rec in records:
        key = (rec["country"], rec["year"])
        if key not in grouped:
            grouped[key] = {
                "country": rec["country"],
                "year": rec["year"],
                "region": rec.get("region", ""),
                "recommendations": []
            }
        grouped[key]["recommendations"].append({
            "criterion": rec.get("criterion", ""),
            "finding": rec.get("finding", ""),
            "recommendation": rec.get("recommendation", ""),
            "assigned_topic": rec.get("assigned_topic", {})
        })
    return list(grouped.values())
