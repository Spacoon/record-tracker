import os
import glob
import json
from typing import List, Dict, Optional
from datetime import datetime

import pandas as pd

# Configuration
DATA_DIR = 'data'
WATCHLIST_FILE = 'watchlist.json'


def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def parse_price(price_str) -> Optional[float]:
    """Parse price format (e.g. 49,99 zł) to float"""
    if pd.isna(price_str):
        return None
    price_str = str(price_str).strip()
    price_str = price_str.replace('zł', '').replace(',', '.').strip()
    try:
        return round(float(price_str), 2)
    except (ValueError, TypeError):
        return None


def load_all_snapshots() -> pd.DataFrame:
    """Load all album snapshots from data directory and merge into one DataFrame."""
    ensure_data_dir()
    frames = []
    for fp in sorted(glob.glob(os.path.join(DATA_DIR, 'albums_*.parquet'))):
        frames.append(pd.read_parquet(fp))

    if not frames:
        return pd.DataFrame(columns=[
            'title', 'band', 'price', 'url', 'category',
            'scrape_date', 'price_numeric'
        ])

    combined = pd.concat(frames, ignore_index=True)
    combined['scrape_date'] = pd.to_datetime(combined['scrape_date'])
    combined['price_numeric'] = combined['price'].apply(parse_price)
    combined = combined.drop_duplicates(
        subset=['title', 'band', 'scrape_date'], keep='last'
    )
    return combined.sort_values('scrape_date')


def get_latest_snapshot(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    return df[df['scrape_date'] == df['scrape_date'].max()]


def get_snapshot_dates(df: pd.DataFrame) -> list:
    if df.empty:
        return []
    return sorted(df['scrape_date'].dt.date.unique())


def search_albums(df: pd.DataFrame, query: str) -> pd.DataFrame:
    """Case-insensitive substring search across title + band."""
    if not query or not query.strip():
        return df
    q = query.strip().lower()
    mask = (
        df['title'].str.lower().str.contains(q, na=False, regex=False) |
        df['band'].fillna('').str.lower().str.contains(q, na=False, regex=False)
    )
    return df[mask]


def get_price_history(df: pd.DataFrame, title: str, band) -> pd.DataFrame:
    mask = df['title'] == title
    if pd.notna(band) and band:
        mask &= df['band'] == band
    return (
        df[mask]
        .sort_values('scrape_date')
        [['scrape_date', 'price', 'price_numeric', 'category', 'url']]
        .drop_duplicates(subset=['scrape_date'])
    )


def get_sold_out_albums(df: pd.DataFrame) -> pd.DataFrame:
    """Albums present in older scrapes but missing from the latest one."""
    dates = get_snapshot_dates(df)
    if len(dates) < 2:
        return pd.DataFrame()

    latest_date = df['scrape_date'].max()
    latest = df[df['scrape_date'] == latest_date]
    previous = df[df['scrape_date'] < latest_date]

    latest_ids = set(zip(latest['title'], latest['band'].fillna('')))
    prev_ids = set(zip(previous['title'], previous['band'].fillna('')))
    sold_out = prev_ids - latest_ids

    if not sold_out:
        return pd.DataFrame()

    rows = []
    for title, band in sold_out:
        mask = (previous['title'] == title) & (previous['band'].fillna('') == band)
        rec = previous[mask].sort_values('scrape_date', ascending=False).iloc[0]
        rows.append({
            'title': rec['title'], 'band': rec['band'],
            'last_price': rec['price'],
            'last_price_numeric': parse_price(rec['price']),
            'category': rec['category'],
            'last_seen': rec['scrape_date'], 'url': rec['url'],
        })
    return pd.DataFrame(rows).sort_values('last_seen', ascending=False)


def get_new_arrivals(df: pd.DataFrame) -> pd.DataFrame:
    """Albums in the latest scrape not present in any earlier snapshot"""
    dates = get_snapshot_dates(df)
    if len(dates) < 2:
        return pd.DataFrame()

    latest_date = df['scrape_date'].max()
    latest = df[df['scrape_date'] == latest_date]
    previous = df[df['scrape_date'] < latest_date]

    new_ids = set(zip(latest['title'], latest['band'].fillna(''))) - \
              set(zip(previous['title'], previous['band'].fillna('')))

    if not new_ids:
        return pd.DataFrame()

    rows = []
    for title, band in new_ids:
        mask = (latest['title'] == title) & (latest['band'].fillna('') == band)
        rec = latest[mask].iloc[0]
        rows.append({
            'title': rec['title'], 'band': rec['band'],
            'price': rec['price'],
            'price_numeric': parse_price(rec['price']),
            'category': rec['category'], 'url': rec['url'],
        })
    return pd.DataFrame(rows)


def get_price_changes(df: pd.DataFrame) -> pd.DataFrame:
    """Albums whose price changed between the last two snapshots"""
    dates = get_snapshot_dates(df)
    if len(dates) < 2:
        return pd.DataFrame()

    sorted_dates = sorted(df['scrape_date'].unique())
    latest = df[df['scrape_date'] == sorted_dates[-1]][['title', 'band', 'price_numeric', 'category']].copy()
    prev = df[df['scrape_date'] == sorted_dates[-2]][['title', 'band', 'price_numeric']].copy()

    merged = latest.merge(prev, on=['title', 'band'], suffixes=('_new', '_old'))
    merged = merged[merged['price_numeric_new'] != merged['price_numeric_old']].copy()
    merged['change'] = merged['price_numeric_new'] - merged['price_numeric_old']
    merged['change_pct'] = (merged['change'] / merged['price_numeric_old'] * 100).round(1)
    return merged.sort_values('change', ascending=False)


def get_stats(df: pd.DataFrame) -> dict:
    latest = get_latest_snapshot(df)
    empty = {
        'total_albums': 0, 'total_artists': 0, 'total_categories': 0,
        'avg_price': 0, 'min_price': 0, 'max_price': 0,
        'median_price': 0, 'latest_date': None, 'num_snapshots': 0,
    }

    if latest.empty:
        return empty
    return {
        'total_albums': len(latest),
        'total_artists': latest['band'].dropna().nunique(),
        'total_categories': latest['category'].nunique(),
        'avg_price': round(latest['price_numeric'].mean(), 2),
        'min_price': latest['price_numeric'].min(),
        'max_price': latest['price_numeric'].max(),
        'median_price': latest['price_numeric'].median(),
        'latest_date': latest['scrape_date'].max(),
        'num_snapshots': len(get_snapshot_dates(df)),
    }


# Watchlist
def load_watchlist() -> dict:
    if os.path.exists(WATCHLIST_FILE):
        with open(WATCHLIST_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'keywords': [], 'last_checked_date': None}


def save_watchlist(data: dict):
    with open(WATCHLIST_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_to_watchlist(keyword: str):
    wl = load_watchlist()
    kw = keyword.strip()
    if kw and kw.lower() not in [k.lower() for k in wl['keywords']]:
        wl['keywords'].append(kw)
        save_watchlist(wl)


def remove_from_watchlist(keyword: str):
    wl = load_watchlist()
    wl['keywords'] = [k for k in wl['keywords'] if k.lower() != keyword.lower()]
    save_watchlist(wl)


def get_watchlist_keywords() -> list:
    return load_watchlist().get('keywords', [])


def check_watchlist_matches(df: pd.DataFrame) -> pd.DataFrame:
    """Check latest snapshot for keyword matches from the watchlist"""
    keywords = get_watchlist_keywords()
    if not keywords:
        return pd.DataFrame()

    latest = get_latest_snapshot(df)
    if latest.empty:
        return pd.DataFrame()

    results = []
    for kw in keywords:
        kw_l = kw.lower()
        mask = (
            latest['title'].str.lower().str.contains(kw_l, na=False, regex=False) |
            latest['band'].fillna('').str.lower().str.contains(kw_l, na=False, regex=False)
        )
        matches = latest[mask].copy()
        if not matches.empty:
            matches['matched_keyword'] = kw
            results.append(matches)

    if not results:
        return pd.DataFrame()
    return pd.concat(results, ignore_index=True).drop_duplicates(
        subset=['title', 'band', 'matched_keyword']
    )
