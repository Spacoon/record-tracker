# 🎵 Record Inventory Tracker

A Streamlit-powered dashboard for tracking prices and inventory at a local Polish record store ([agrochowski.pl](https://agrochowski.pl)). Scrape the store's catalog, monitor price changes over time, spot sold-out records, and get notified when albums you care about appear in stock.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?logo=streamlit&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-Charts-3F4F75?logo=plotly&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

| Page | Description |
|------|-------------|
| **🏠 Dashboard** | KPI cards, price distribution, category breakdown, top expensive records, recent price changes |
| **🔍 Search** | Real-time filtering by artist/album name with category & price range filters |
| **📈 Price History** | Interactive line chart tracking an album's price across scrape snapshots |
| **📦 Sold Out** | Albums that disappeared from the store since last scrape |
| **🆕 New Arrivals** | Albums that appeared for the first time in the latest scrape |
| **📊 Categories** | Per-genre statistics, box-plot price comparison, and browsable album lists |
| **⭐ Watchlist** | Add keyword alerts — get notified when matching albums are in stock |
| **🔄 Refresh Data** | One-click scrape with a live progress bar |

## 🏗️ Architecture

```
record-inventory-tracker/
├── app.py                # Streamlit GUI
├── data_manager.py       # Data loading, search, analytics, watchlist logic
├── scraper.py            # Web scraper for agrochowski.pl
├── config.json           # Genre list to scrape
├── categories.parquet    # List of categories
├── requirements.txt
├── .streamlit/
│   └── config.toml       # Theme config
└── data/
    ├── albums_2026-02-04.parquet   # Historical snapshot
    ├── albums_2026-03-30.parquet   # Another snapshot
    └── ...                         # One file per scrape date
```

**Data flow:**
1. `scraper.py` crawls the store's paginated catalog and saves a dated Parquet file into `data/`
2. `data_manager.py` loads all snapshots, merges them and exposes query functions (search, price history, diff detection)
3. `app.py` renders everything through Streamlit with Plotly charts

## 🚀 Quick Start

### 1. Clone & install

```bash
git clone https://github.com/<your-username>/record-inventory-tracker.git
cd record-inventory-tracker
pip install -r requirements.txt
```

### Optional: Scrape the store manually (categories are already scraped)

```bash
python scraper.py --albums
```

### 2. Launch the app

```bash
streamlit run app.py
```

### 3. Track changes

Come back any time and hit **🔄 Refresh Data** in the app (or re-run `python scraper.py --albums`) to create a new snapshot. The app auto-detects all snapshots and enables:

- **Price History** charts (2+ snapshots needed)
- **Sold Out** detection
- **New Arrivals** detection
- **Price Changes** tracking

## ⭐ Watchlist

Add keywords (artist names, album titles, or any search term) via the **Watchlist** page. On every app load, if any keyword matches an album in the current inventory, you'll receive a toast notification. Keywords persist in `watchlist.json`.

## ⚙️ Configuration

Edit `config.json` to control which genres are scraped:

```json
{
  "genres_to_scrape": [
    "Rock",
    "Jazz",
    "Hip-hop",
    "Elektroniczna"
  ]
}
```

The full list of available genres is scraped via `python scraper.py --categories`.

## 🛠️ Tech Stack

- **[Streamlit](https://streamlit.io/)** — UI framework
- **[Plotly](https://plotly.com/python/)** — Interactive charts
- **[Pandas](https://pandas.pydata.org/)** — Data manipulation
- **[BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/)** — Web scraping
- **[Pandera](https://pandera.readthedocs.io/)** — Data validation
- **[Apache Parquet](https://parquet.apache.org/)** — Efficient columnar storage

## 📝 License

MIT
