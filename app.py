from flask import Flask, render_template, request, jsonify
import pandas as pd
from utils.plots import filter_data, plot_time_series, plot_by_country, group_by_country_year, get_regions_to_countries, plot_topic_area, plot_year_line 
from utils.categories import TOPICS
df = pd.read_json("oecd_recommendations_with_topics.json", lines=True)


app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

# === Region and country options ===
topics = TOPICS
regions_to_countries = get_regions_to_countries(df)
all_regions = list(regions_to_countries.keys())
regions = list(regions_to_countries.keys())
MIN_YEAR = int(df["year"].min())
MAX_YEAR = int(df["year"].max())
years = list(range(MIN_YEAR, MAX_YEAR + 1))

@app.route("/", methods=["GET", "POST"])
def home():
    selected_regions = []
    selected_countries = []
    selected_topic = ""
    results = []
    time_plot = None
    country_plot = None
    year_start = MIN_YEAR 
    year_end = MAX_YEAR

    if request.method == "POST":
        selected_regions = request.form.getlist("regions")
        selected_countries = request.form.getlist("countries")
        selected_topic = request.form.get("topic", "")
        year_start = int(request.form.get("year_from") or MIN_YEAR)
        year_end = int(request.form.get("year_to") or MAX_YEAR)

        # If only regions selected, expand to countries
        if selected_regions and not selected_countries:
            for region in selected_regions:
                selected_countries.extend(regions_to_countries.get(region, []))

        # Filter data and create plots
        filtered = filter_data(df, selected_countries, selected_topic, year_start, year_end)
        results = group_by_country_year(filtered.to_dict(orient="records"))
        time_plot = plot_time_series(filtered, selected_topic)
        country_plot = plot_by_country(filtered, selected_topic)

    return render_template(
        "index.html",
        query="",
        results=results,
        regions=regions,
        years=years,
        topics=topics,
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
    
        # If only regions selected, expand to countries
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
    # Use your filtered DataFrame or the full DataFrame
    # For demo, using the full DataFrame:
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    return send_file(
        io.BytesIO(csv_buffer.getvalue().encode()),
        mimetype="text/csv",
        as_attachment=True,
        download_name="oecd_recommendations.csv"
    )

if __name__ == "__main__":
    app.run(debug=True)
