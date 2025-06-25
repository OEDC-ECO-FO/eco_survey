#  OECD NLP Recommendation Search

Imagine you have **hundreds of policy recommendations** from around the world. They're all written in long paragraphs and talk about very different topics — like education, climate, gender, or health.

But there’s a problem:
> These recommendations don’t come with a label telling us what topic they belong to.

So… how can we **teach a computer** to read these and figure out which topic they match?

This project builds a **semantic search and classification system** for OECD country recommendations using Natural Language Processing (NLP).

We transform raw policy texts into meaningful insights by:
- Understanding the meaning behind recommendations and findings
- Matching each to **predefined policy topics**
- Powering search, dashboards, and analysis — without manual labeling

## Project Structure

```
econ_surveys_app/
├── .venv/                  ← Virtual environment
├── app/                    ← Main application folder
│   ├── app.py              ← Flask routes (GET/POST)
│   ├── wsgi.py             ← WSGI server entry point
│   ├── Dockerfile          ← Container config (optional)
│   ├── templates/          ← HTML templates
│   └── utils/              ← (Optional) helper functions
├── data/                   ← Raw and cleaned data
│   ├── scraping/           ← Scraping logic
│   ├── oecd_findings_and_recommendations.json
│   └── oecd_recommendations_with_topics.json
├── NLP/                    ← Natural Language Processing logic
│   ├── chroma_topic_db/    ← Saved vector embeddings
│   ├── models/             ← Local model cache (if needed)
│   ├── nlp.ipynb           ← NLP model implementation
├── topic_categories.json   ← Dictionary of topics and definitions
├── requirements.txt        ← Python dependencies
└── README.md               ← You're here!
```

## 🔧 How to Run This App Locally

### 1. Clone the Repo
```bash
git clone https://github.com/yourname/econ_surveys_app.git
cd econ_surveys_app
```

### 2. Set Up Your Python Environment
```bash
python -m venv .venv
.venv\Scripts\activate  # On Windows
pip install -r requirements.txt
```

### 3. Download the Embedding Model (Optional)
Use this helper to avoid proxy/network issues:
```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("all-MiniLM-L6-v2")
model.save("models/all-MiniLM-L6-v2")
```

### 4. Run the App
```bash
python app/app.py
```
Or use `wsgi.py` with a server like Gunicorn or waitress.

---

## 💡 Notes on Architecture & Flexibility

- The app combines **Elasticsearch** (for metadata filtering) and **ChromaDB** (for semantic ranking).
- Model download and ChromaDB creation are **only run once**.
- Structure supports `app/` folder to encapsulate all web logic (great for modularity).
- You can later split routes into multiple files or add an `api.py` if needed.

---

## Credits
Created by Daniela Ayala (OECD ECO, 2025) with 💙 for NLP and civic tech.

---

Let us know if you'd like to contribute or expand to other OECD datasets!


