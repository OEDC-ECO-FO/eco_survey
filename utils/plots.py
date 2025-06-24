import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from collections import Counter
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


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

def plot_time_series(df, topic=None):
    if df.empty:
        return None

    unique_countries = df["country"].nunique()

    if unique_countries <= 10:
        by_country = df.groupby(["year", "country"]).size().reset_index(name="count")

        fig = go.Figure()

        # Add lines for each country
        for country in by_country["country"].unique():
            subset = by_country[by_country["country"] == country]
            fig.add_trace(go.Scatter(
                x=subset["year"], y=subset["count"],
                mode="lines+markers",
                name=country,
                line=dict(width=2)
            ))

        fig.update_layout(
            title=f"Recommendations on '{topic}' by Country and Year" if topic else "Recommendations by Country and Year",
            xaxis_title="Year",
            yaxis_title="Recommendation Count",
            template="plotly_white",
            legend=dict(bordercolor="gray", borderwidth=1),
            margin=dict(t=60, l=50, r=30, b=50),
            font=dict(family="Segoe UI", size=14)
        )

    else:
        # Fallback for large number of countries: total volume only
        counts = df.groupby("year").size().reset_index(name="count")
        fig = px.line(
            counts,
            x="year", y="count", markers=True,
            title=f"Recommendations on '{topic}' per Year" if topic else "Recommendations per Year"
        )
        fig.update_layout(
            template="plotly_white",
            margin=dict(t=60, l=50, r=30, b=50),
            xaxis_title="Year",
            yaxis_title="Recommendation Count",
            font=dict(family="Segoe UI", size=14)
        )

    return fig.to_html(full_html=False)



def plot_by_country(df, topic=None):
    if df.empty:
        return None

    counts = df["country"].value_counts().reset_index()
    counts.columns = ["country", "count"]

    fig = px.bar(counts, x="country", y="count",
                 title=f"Recommendations on '{topic}' by Country" if topic else "Recommendations by Country",
                 text_auto=True,
                 color_discrete_sequence=["#4C78A8"])  # nice blue

    fig.update_layout(
        template="plotly_white",
        margin=dict(t=60, l=50, r=30, b=50),
        xaxis_title="Country",
        yaxis_title="Recommendation Count",
        xaxis_tickangle=-20,
        font=dict(family="Segoe UI", size=14)
    )

    return fig.to_html(full_html=False)


def plot_topic_area(df, title=""):
    if df.empty:
        return None

    # Convert assigned_topic dict to a list of topic names
    df = df.copy()
    df["topics"] = df["assigned_topic"].apply(lambda d: list(d.keys()) if isinstance(d, dict) else [])

    # Explode the topics for plotting
    topic_counts = (
        df.explode("topics")
        .groupby(["year", "topics"])
        .size()
        .reset_index(name="count")
    )

    fig = px.area(
        topic_counts, x="year", y="count", color="topics",
        title=f"Topic Trends in {title}",
        category_orders={"topics": sorted(topic_counts["topics"].dropna().unique())},
        labels={"count": "Recommendation Count", "topics": "Topic"}
    )
    fig.update_layout(
        template="plotly_white",
        font=dict(family="Segoe UI", size=14),
        margin=dict(t=50, l=50, r=30, b=40)
    )
    return fig.to_html(full_html=False)

def plot_year_line(df, title=""):
    if df.empty or "year" not in df.columns or "country" not in df.columns:
        return None

    # Group by year and country, count recommendations
    year_counts = (
        df.groupby(["year", "country"])
        .size()
        .reset_index(name="count")
    )

    fig = px.line(
        year_counts, x="year", y="count", color="country",
        title=f"Yearly Recommendation Volume in {title}",
        markers=True,
        labels={"count": "Recommendation Count", "country": "Country"}
    )
    fig.update_layout(
        template="plotly_white",
        font=dict(family="Segoe UI", size=14),
        margin=dict(t=50, l=50, r=30, b=40)
    )
    return fig.to_html(full_html=False)

def plot_region_topic_heatmap(df, region_name):
    if df.empty:
        return None

    exploded = df.explode("topics")
    grouped = exploded.groupby(["year", "topics"]).size().reset_index(name="count")

    fig = px.density_heatmap(
        grouped,
        x="year",
        y="topics",
        z="count",
        color_continuous_scale="Blues",
        title=f"Heatmap of Topics in {region_name} Over Time"
    )
    fig.update_layout(template="plotly_white", font=dict(family="Segoe UI", size=14))
    return fig.to_html(full_html=False)


def plot_region_streamgraph(df, region_name):
    if df.empty:
        return None

    exploded = df.explode("topics")
    grouped = exploded.groupby(["year", "topics"]).size().reset_index(name="count")

    fig = px.area(
        grouped,
        x="year",
        y="count",
        color="topics",
        title=f"Topic Stream in {region_name}",
        line_group="topics"
    )
    fig.update_layout(template="plotly_white", font=dict(family="Segoe UI", size=14))
    return fig.to_html(full_html=False)


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


