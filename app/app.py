from flask import Flask, render_template, request, jsonify, send_file, session
import pandas as pd
import os
import json
import io
import csv
import uuid
from .utils.plots import plot_time_series, plot_by_country, plot_topic_area, plot_year_line, plot_time_series_percentage
from .utils.data_management import filter_data, get_regions_to_countries, group_by_country_year, relevant_topics
from topic_categories import TOPICS

# Get the full path to the root directory
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
file_path = os.path.join(ROOT_DIR, "data", "oecd_recommendations_with_topics.json")
df = pd.read_json(file_path, lines=True)

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.secret_key = "temp"

results_cache = {}

# === Region and country options ===
topics = TOPICS
regions_to_countries = get_regions_to_countries(df)
regions = list(regions_to_countries.keys())
MIN_YEAR = int(df["year"].min())
MAX_YEAR = int(df["year"].max())
years = list(range(MIN_YEAR, MAX_YEAR + 1))

@app.route("/", methods=["GET", "POST"])
def home():
    selected_regions = []
    selected_countries = []
    selected_topic = ""
    text_type = "full_text"
    results = []
    time_plot = None
    country_plot = None
    year_start = MIN_YEAR
    year_end = MAX_YEAR

    if request.method == "POST":
        selected_regions = request.form.getlist("regions")
        selected_countries = request.form.getlist("countries")
        selected_topic = request.form.get("topic", "")
        text_type = request.form.get("text_type", "recommendation")
        year_start = int(request.form.get("year_from") or MIN_YEAR)
        year_end = int(request.form.get("year_to") or MAX_YEAR)

        if selected_regions and not selected_countries:
            for region in selected_regions:
                selected_countries.extend(regions_to_countries.get(region, []))

        text_type_df = relevant_topics(df, text_type)
        filtered = filter_data(text_type_df, selected_countries, selected_topic, year_start, year_end)
        results = group_by_country_year(filtered.to_dict(orient="records"))

        # Cache results using UUID key
        results_key = str(uuid.uuid4())
        results_cache[results_key] = results
        session["last_results_key"] = results_key 

        time_plot = plot_time_series(filtered, selected_topic)
        country_plot = plot_time_series_percentage(df, selected_topic, selected_countries)

    return render_template(
        "index.html",
        query="",
        results=results,
        regions=regions,
        years=years,
        topics=topics,
        text_type=text_type,
        selected_regions=selected_regions,
        selected_countries=selected_countries,
        selected_topic=selected_topic,
        year_from=year_start,
        year_to=year_end,
        time_plot=time_plot,
        country_plot=country_plot
    )

@app.route("/country", methods=["GET", "POST"])
def explore_country():
    selected_regions = []
    selected_countries = []
    regional_country_analysis = {}
    year_start = MIN_YEAR
    year_end = MAX_YEAR

    if request.method == "POST":
        selected_regions = request.form.getlist("regions")
        selected_countries = request.form.getlist("countries")
        year_start = int(request.form.get("year_from") or MIN_YEAR)
        year_end = int(request.form.get("year_to") or MAX_YEAR)

        filtered = filter_data(df, countries=selected_countries, year_from=year_start, year_to=year_end)

        if selected_regions:
            for region in selected_regions:
                selected_countries.extend(regions_to_countries.get(region, []))

                region_data = filtered[filtered["region"] == region]
                topic_area_html = plot_topic_area(region_data, region)
                year_line_html = plot_year_line(region_data, region)

                country_plots = {}
                for country in sorted(region_data["country"].unique()):
                    country_data = region_data[region_data["country"] == country]
                    if country_data.empty:
                        continue
                    c_topic_html = plot_topic_area(country_data, country)
                    c_line_html = plot_year_line(country_data, country)
                    country_plots[country] = [c_topic_html, c_line_html]

                regional_country_analysis[region] = {
                    "region_graphs": [topic_area_html, year_line_html],
                    "countries": country_plots
                }

    return render_template(
        "country.html",
        years=years,
        regions=regions,
        selected_regions=selected_regions,
        selected_countries=selected_countries,
        countries=sorted(df["country"].unique()),
        year_from=year_start,
        year_to=year_end,
        regional_country_analysis=regional_country_analysis
    )

@app.route("/get_countries")
def get_countries():
    regions_selected = request.args.getlist("region")
    countries = set()
    for region in regions_selected:
        countries.update(regions_to_countries.get(region, []))
    return jsonify(sorted(countries))

@app.route("/download_csv")
def download_csv():
    
    key = session.get("last_results_key")
    results = results_cache.get(key)

    if not key or not results:
        return "No results available. Please run a search first.", 400

    rows = []
    for block in results:
        year = block["year"]
        country = block["country"]
        for r in block["recommendations"]:
            row = {
                "year": year,
                "country": country,
                "criterion": r.get("criterion", ""),
                "finding": r.get("finding", ""),
                "recommendation": r.get("recommendation", ""),
                **{f"topic_{k}": v for k, v in r.get("assigned_topic", {}).items()}
            }
            rows.append(row)

    csv_buffer = io.StringIO()
    # Dynamically gather all possible fieldnames from all rows
    all_keys = set()
    for row in rows:
        all_keys.update(row.keys())
    fieldnames = sorted(all_keys)  # Optional: sort for consistency

    writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    csv_buffer.seek(0)

    return send_file(
        io.BytesIO(csv_buffer.getvalue().encode()),
        mimetype="text/csv",
        as_attachment=True,
        download_name="filtered_recommendations.csv"
    )


if __name__ == "__main__":
    app.run(debug=True)
