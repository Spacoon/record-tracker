import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

import data_manager as dm


# Page Config
st.set_page_config(
    page_title="Record Inventory Tracker",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded",
)


# CSS code
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stApp {
    background: linear-gradient(160deg, #0a0a12 0%, #12101f 40%, #0e1117 100%);
}

#MainMenu, footer, header { visibility: hidden; }

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d0b14 0%, #151320 100%);
    border-right: 1px solid rgba(139,92,246,0.1);
}

[data-testid="stMetric"] {
    background: linear-gradient(135deg, rgba(139,92,246,0.08) 0%, rgba(6,182,212,0.05) 100%);
    border: 1px solid rgba(139,92,246,0.15);
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.3);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(139,92,246,0.15);
}

[data-testid="stMetricLabel"] {
    color: #a0a0b0 !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

[data-testid="stMetricValue"] {
    color: #f0f0f5 !important;
    font-size: 1.8rem !important;
    font-weight: 700 !important;
}

.stButton > button {
    background: linear-gradient(135deg, #8B5CF6 0%, #6D28D9 100%);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 8px 24px;
    font-weight: 600;
    transition: all 0.3s ease;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #7C3AED 0%, #5B21B6 100%);
    box-shadow: 0 4px 20px rgba(139,92,246,0.4);
    transform: translateY(-1px);
}

div[data-testid="stDataFrame"] {
    border: 1px solid rgba(139,92,246,0.1);
    border-radius: 12px;
    overflow: hidden;
}

.hero-title {
    font-size: 2.8rem;
    font-weight: 700;
    background: linear-gradient(135deg, #8B5CF6 0%, #06B6D4 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0;
    line-height: 1.2;
}

.hero-sub {
    color: #8888a0;
    font-size: 1.1rem;
    margin-top: 4px;
}

.card {
    background: linear-gradient(135deg, rgba(139,92,246,0.06) 0%, rgba(6,182,212,0.03) 100%);
    border: 1px solid rgba(139,92,246,0.12);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 16px;
}

.badge-sold { background: #EF4444; color: white; padding: 2px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
.badge-new { background: #10B981; color: white; padding: 2px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
.badge-watch { background: #F59E0B; color: #1a1a2e; padding: 2px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }

.price-up { color: #EF4444; font-weight: 600; }
.price-down { color: #10B981; font-weight: 600; }

.section-header {
    font-size: 1.5rem;
    font-weight: 600;
    color: #e0e0f0;
    margin-bottom: 16px;
    padding-bottom: 8px;
    border-bottom: 2px solid rgba(139,92,246,0.2);
}
</style>
""", unsafe_allow_html=True)


# Chart helpers
CHART_COLORS = ['#8B5CF6', '#06B6D4', '#F59E0B', '#10B981', '#EF4444',
                '#3B82F6', '#EC4899', '#14B8A6', '#F97316', '#A78BFA']


def chart_layout(**kwargs):
    base = dict(
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif", color="#c0c0d0"),
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(gridcolor='rgba(255,255,255,0.04)'),
        yaxis=dict(gridcolor='rgba(255,255,255,0.04)'),
    )
    base.update(kwargs)
    return base



# Data Loading
@st.cache_data(ttl=300)
def load_data():
    return dm.load_all_snapshots()


data = load_data()
stats = dm.get_stats(data)


# Watchlist toast (once per session)
if 'wl_notified' not in st.session_state:
    wl_matches = dm.check_watchlist_matches(data)
    if not wl_matches.empty:
        st.toast(f"⭐ {len(wl_matches)} watchlist match(es) in current inventory!", icon="🎵")
    st.session_state.wl_notified = True


# Sidebar
with st.sidebar:
    st.markdown('<p class="hero-title" style="font-size:1.8rem">🎵 Record Inventory Tracker</p>', unsafe_allow_html=True)
    st.caption("Agrochowski record store tracker")
    st.divider()

    page = st.radio(
        "Navigation",
        ["🏠 Dashboard", "🔍 Search", "📈 Price History",
         "📦 Sold Out", "🆕 New Arrivals", "📊 Categories",
         "⭐ Watchlist", "🔄 Refresh Data"],
        label_visibility="collapsed",
    )

    st.divider()
    st.metric("Albums", stats['total_albums'])
    if stats['latest_date']:
        st.metric("Latest Scrape", stats['latest_date'].strftime('%Y-%m-%d'))
    st.metric("Snapshots", stats['num_snapshots'])



# PAGE: Dashboard
if page == "🏠 Dashboard":
    st.markdown('<p class="hero-title">🏠 Dashboard</p>', unsafe_allow_html=True)
    st.markdown('<p class="hero-sub">Overview of Agrochowski record store inventory</p>', unsafe_allow_html=True)
    st.markdown("")

    # KPI cards
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Albums", f"{stats['total_albums']:,}")
    c2.metric("Artists", f"{stats['total_artists']:,}")
    c3.metric("Categories", stats['total_categories'])
    c4.metric("Avg Price", f"{stats['avg_price']:.2f} zł" if stats['avg_price'] else "—")

    st.markdown("")

    # Charts row
    col_left, col_right = st.columns(2)

    latest = dm.get_latest_snapshot(data)

    with col_left:
        st.markdown('<p class="section-header">💰 Price Distribution</p>', unsafe_allow_html=True)
        if not latest.empty:
            fig = px.histogram(
                latest, x='price_numeric', nbins=40,
                color_discrete_sequence=['#8B5CF6'],
                labels={'price_numeric': 'Price (zł)', 'count': 'Albums'},
            )
            fig.update_layout(**chart_layout(title="", showlegend=False))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available yet. Scrape some albums first!")

    with col_right:
        st.markdown('<p class="section-header">🎶 Albums by Category</p>', unsafe_allow_html=True)
        if not latest.empty:
            cat_counts = latest['category'].value_counts().reset_index()
            cat_counts.columns = ['Category', 'Count']
            fig = px.bar(
                cat_counts, y='Category', x='Count', orientation='h',
                color='Count', color_continuous_scale=['#1e1b4b', '#8B5CF6', '#06B6D4'],
            )
            fig.update_layout(**chart_layout(title="", showlegend=False, coloraxis_showscale=False))
            fig.update_layout(yaxis=dict(categoryorder='total ascending'))
            st.plotly_chart(fig, use_container_width=True)

    # Price changes (if multiple snapshots)
    price_changes = dm.get_price_changes(data)
    if not price_changes.empty:
        st.markdown('<p class="section-header">📊 Recent Price Changes</p>', unsafe_allow_html=True)
        display = price_changes.head(15).copy()
        display['Change'] = display.apply(
            lambda r: f"{'🔴' if r['change'] > 0 else '🟢'} {r['change']:+.2f} zł ({r['change_pct']:+.1f}%)", axis=1
        )
        st.dataframe(
            display[['title', 'band', 'price_numeric_new', 'Change', 'category']].rename(columns={
                'title': 'Title', 'band': 'Artist', 'price_numeric_new': 'Current Price (zł)',
                'category': 'Category'
            }),
            use_container_width=True, hide_index=True,
        )

    # Top expensive albums
    if not latest.empty:
        st.markdown('<p class="section-header">💎 Most Expensive Records</p>', unsafe_allow_html=True)
        top = latest.nlargest(10, 'price_numeric')[['title', 'band', 'price', 'category']].copy()
        top.columns = ['Title', 'Artist', 'Price', 'Category']
        st.dataframe(top, use_container_width=True, hide_index=True)



# PAGE: Search
elif page == "🔍 Search":
    st.markdown('<p class="hero-title">🔍 Search</p>', unsafe_allow_html=True)
    st.markdown('<p class="hero-sub">Find albums and artists in the current inventory</p>', unsafe_allow_html=True)
    st.markdown("")

    latest = dm.get_latest_snapshot(data)

    query = st.text_input("Search by album title or artist name", placeholder="e.g. Pink Floyd, Dark Side...")

    # Filters
    fc1, fc2 = st.columns(2)
    with fc1:
        categories = ['All'] + sorted(latest['category'].unique().tolist()) if not latest.empty else ['All']
        selected_cat = st.selectbox("Category", categories)
    with fc2:
        if not latest.empty and latest['price_numeric'].notna().any():
            min_p, max_p = float(latest['price_numeric'].min()), float(latest['price_numeric'].max())
            price_range = st.slider("Price range (zł)", min_p, max_p, (min_p, max_p), step=1.0)
        else:
            price_range = (0.0, 9999.0)

    # Apply filters
    results = latest.copy() if not latest.empty else pd.DataFrame()
    if query:
        results = dm.search_albums(results, query)
    if selected_cat != 'All' and not results.empty:
        results = results[results['category'] == selected_cat]
    if not results.empty:
        results = results[
            (results['price_numeric'] >= price_range[0]) &
            (results['price_numeric'] <= price_range[1])
        ]

    st.markdown(f"**{len(results)} album(s) found**")

    if not results.empty:
        display = results[['title', 'band', 'price', 'category', 'url']].copy()
        display.columns = ['Title', 'Artist', 'Price', 'Category', 'Store Link']
        st.dataframe(
            display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Store Link": st.column_config.LinkColumn("Store Link", display_text="🔗 View"),
            },
        )

        # Quick add to watchlist from search
        with st.expander("➕ Add search term to watchlist"):
            if query:
                if st.button(f'Watch "{query}"', key="watch_from_search"):
                    dm.add_to_watchlist(query)
                    st.success(f'Added "{query}" to watchlist!')
                    st.rerun()
    elif query:
        st.warning("No albums found matching your search.")



# PAGE: Price History
elif page == "📈 Price History":
    st.markdown('<p class="hero-title">📈 Price History</p>', unsafe_allow_html=True)
    st.markdown('<p class="hero-sub">Track how album prices change over time</p>', unsafe_allow_html=True)
    st.markdown("")

    snapshot_dates = dm.get_snapshot_dates(data)

    if len(snapshot_dates) < 2:
        st.info("📌 Price history requires at least 2 data snapshots. Use **Refresh Data** to scrape current inventory and start tracking changes.")

    # Album selector with search
    search_q = st.text_input("Search for an album", placeholder="Type to filter albums...", key="ph_search")
    filtered = dm.search_albums(data, search_q) if search_q else data

    unique_albums = filtered.drop_duplicates(subset=['title', 'band'])[['title', 'band']].copy()
    unique_albums['label'] = unique_albums.apply(
        lambda r: f"{r['title']} — {r['band']}" if pd.notna(r['band']) and r['band'] else r['title'], axis=1
    )

    if unique_albums.empty:
        st.warning("No albums found.")
    else:
        selected_label = st.selectbox("Select album", unique_albums['label'].tolist())

        if selected_label:
            sel = unique_albums[unique_albums['label'] == selected_label].iloc[0]
            history = dm.get_price_history(data, sel['title'], sel['band'])

            if not history.empty:
                st.markdown(f"### {sel['title']}")
                if pd.notna(sel['band']) and sel['band']:
                    st.markdown(f"**Artist:** {sel['band']}")
                st.markdown(f"**Category:** {history['category'].iloc[-1]}")

                mc1, mc2, mc3 = st.columns(3)
                mc1.metric("Current Price", f"{history['price_numeric'].iloc[-1]:.2f} zł")
                if len(history) > 1:
                    change = history['price_numeric'].iloc[-1] - history['price_numeric'].iloc[0]
                    mc2.metric("Price Change", f"{change:+.2f} zł")
                    mc3.metric("Data Points", len(history))

                # Chart
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=history['scrape_date'], y=history['price_numeric'],
                    mode='lines+markers',
                    line=dict(color='#8B5CF6', width=3),
                    marker=dict(size=10, color='#8B5CF6', line=dict(width=2, color='#06B6D4')),
                    hovertemplate='%{x|%Y-%m-%d}<br>Price: %{y:.2f} zł<extra></extra>',
                ))
                fig.update_layout(**chart_layout(
                    title="Price Over Time",
                    xaxis_title="Date", yaxis_title="Price (zł)",
                    height=400,
                ))
                st.plotly_chart(fig, use_container_width=True)

                # Link to store
                if history['url'].iloc[-1]:
                    st.link_button("🔗 View in Store", history['url'].iloc[-1])



# PAGE: Sold Out
elif page == "📦 Sold Out":
    st.markdown('<p class="hero-title">📦 Sold Out</p>', unsafe_allow_html=True)
    st.markdown('<p class="hero-sub">Albums that were previously available but are no longer in stock</p>', unsafe_allow_html=True)
    st.markdown("")

    sold_out = dm.get_sold_out_albums(data)

    if sold_out.empty:
        snapshot_dates = dm.get_snapshot_dates(data)
        if len(snapshot_dates) < 2:
            st.info("📌 Sold-out detection requires at least 2 snapshots. The current data is from **{}**. Use **Refresh Data** to scrape the current inventory and compare.".format(
                snapshot_dates[0] if snapshot_dates else "N/A"
            ))
        else:
            st.success("🎉 No albums have been removed since the last scrape!")
    else:
        st.markdown(f"**{len(sold_out)} album(s) no longer available**")

        # Category filter
        cats = ['All'] + sorted(sold_out['category'].unique().tolist())
        sel_cat = st.selectbox("Filter by category", cats)
        display = sold_out if sel_cat == 'All' else sold_out[sold_out['category'] == sel_cat]

        st.dataframe(
            display[['title', 'band', 'last_price', 'category', 'last_seen', 'url']].rename(columns={
                'title': 'Title', 'band': 'Artist', 'last_price': 'Last Price',
                'category': 'Category', 'last_seen': 'Last Seen', 'url': 'Store Link',
            }),
            use_container_width=True, hide_index=True,
            column_config={
                "Store Link": st.column_config.LinkColumn("Store Link", display_text="🔗"),
                "Last Seen": st.column_config.DateColumn("Last Seen", format="YYYY-MM-DD"),
            },
        )

        if display['last_price_numeric'].notna().any():
            total_val = display['last_price_numeric'].sum()
            st.markdown(f"💰 **Total last-known value:** {total_val:,.2f} zł")



# PAGE: New Arrivals
elif page == "🆕 New Arrivals":
    st.markdown('<p class="hero-title">🆕 New Arrivals</p>', unsafe_allow_html=True)
    st.markdown('<p class="hero-sub">Albums that appeared in the latest scrape for the first time</p>', unsafe_allow_html=True)
    st.markdown("")

    arrivals = dm.get_new_arrivals(data)

    if arrivals.empty:
        snapshot_dates = dm.get_snapshot_dates(data)
        if len(snapshot_dates) < 2:
            st.info("📌 New arrivals detection requires at least 2 snapshots. Use **Refresh Data** to scrape and compare.")
        else:
            st.info("No new arrivals since the last scrape.")
    else:
        st.markdown(f"**{len(arrivals)} new album(s) added!**")

        cats = ['All'] + sorted(arrivals['category'].unique().tolist())
        sel_cat = st.selectbox("Filter by category", cats, key="na_cat")
        display = arrivals if sel_cat == 'All' else arrivals[arrivals['category'] == sel_cat]

        st.dataframe(
            display[['title', 'band', 'price', 'category', 'url']].rename(columns={
                'title': 'Title', 'band': 'Artist', 'price': 'Price',
                'category': 'Category', 'url': 'Store Link',
            }),
            use_container_width=True, hide_index=True,
            column_config={
                "Store Link": st.column_config.LinkColumn("Store Link", display_text="🔗 View"),
            },
        )



# PAGE: Categories
elif page == "📊 Categories":
    st.markdown('<p class="hero-title">📊 Category Explorer</p>', unsafe_allow_html=True)
    st.markdown('<p class="hero-sub">Browse albums by genre and compare category statistics</p>', unsafe_allow_html=True)
    st.markdown("")

    latest = dm.get_latest_snapshot(data)

    if latest.empty:
        st.info("No data available.")
    else:
        # Category stats
        cat_stats = latest.groupby('category').agg(
            albums=('title', 'count'),
            avg_price=('price_numeric', 'mean'),
            min_price=('price_numeric', 'min'),
            max_price=('price_numeric', 'max'),
            artists=('band', 'nunique'),
        ).round(2).sort_values('albums', ascending=False)
        cat_stats.index.name = 'Category'

        st.markdown('<p class="section-header">📋 Category Statistics</p>', unsafe_allow_html=True)
        st.dataframe(
            cat_stats.rename(columns={
                'albums': 'Albums', 'avg_price': 'Avg Price (zł)',
                'min_price': 'Min (zł)', 'max_price': 'Max (zł)', 'artists': 'Artists',
            }),
            use_container_width=True,
        )

        # Price comparison chart
        fig = px.box(
            latest, x='category', y='price_numeric',
            color='category', color_discrete_sequence=CHART_COLORS,
            labels={'price_numeric': 'Price (zł)', 'category': 'Category'},
        )
        fig.update_layout(**chart_layout(title="Price Distribution by Category", showlegend=False, height=450))
        fig.update_xaxes(tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

        # Browse a category
        st.markdown('<p class="section-header">🎵 Browse Category</p>', unsafe_allow_html=True)
        selected_cat = st.selectbox("Pick a category", sorted(latest['category'].unique().tolist()))

        cat_albums = latest[latest['category'] == selected_cat].sort_values('band')
        st.markdown(f"**{len(cat_albums)} albums in {selected_cat}**")
        st.dataframe(
            cat_albums[['title', 'band', 'price', 'url']].rename(columns={
                'title': 'Title', 'band': 'Artist', 'price': 'Price', 'url': 'Store Link',
            }),
            use_container_width=True, hide_index=True,
            column_config={
                "Store Link": st.column_config.LinkColumn("Store Link", display_text="🔗 View"),
            },
        )



# PAGE: Watchlist
elif page == "⭐ Watchlist":
    st.markdown('<p class="hero-title">⭐ Watchlist</p>', unsafe_allow_html=True)
    st.markdown('<p class="hero-sub">Track keywords — get notified when matching albums appear</p>', unsafe_allow_html=True)
    st.markdown("")

    # Add keyword
    col_add, col_btn = st.columns([3, 1])
    with col_add:
        new_kw = st.text_input("Add a keyword to watch", placeholder="e.g. Pink Floyd, Radiohead, Jazz...")
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➕ Add", use_container_width=True):
            if new_kw and new_kw.strip():
                dm.add_to_watchlist(new_kw.strip())
                st.success(f'Added "{new_kw.strip()}" to watchlist!')
                st.rerun()
            else:
                st.warning("Please enter a keyword.")

    # Current keywords
    keywords = dm.get_watchlist_keywords()

    st.markdown('<p class="section-header">📋 Your Keywords</p>', unsafe_allow_html=True)
    if not keywords:
        st.info("No keywords yet. Add some above to start tracking!")
    else:
        for kw in keywords:
            kc1, kc2 = st.columns([4, 1])
            kc1.markdown(f'<span class="badge-watch">{kw}</span>', unsafe_allow_html=True)
            if kc2.button("🗑️", key=f"rm_{kw}"):
                dm.remove_from_watchlist(kw)
                st.rerun()

    # Current matches
    st.markdown('<p class="section-header">🔔 Current Matches</p>', unsafe_allow_html=True)
    matches = dm.check_watchlist_matches(data)

    if matches.empty:
        if keywords:
            st.info("No matches found in current inventory. Matches will appear here after a refresh if any keyword matches new albums.")
        else:
            st.info("Add keywords above to see matches.")
    else:
        st.success(f"**{len(matches)} match(es) found in current inventory!**")
        st.dataframe(
            matches[['matched_keyword', 'title', 'band', 'price', 'category', 'url']].rename(columns={
                'matched_keyword': 'Keyword', 'title': 'Title', 'band': 'Artist',
                'price': 'Price', 'category': 'Category', 'url': 'Store Link',
            }),
            use_container_width=True, hide_index=True,
            column_config={
                "Store Link": st.column_config.LinkColumn("Store Link", display_text="🔗 View"),
            },
        )



# PAGE: Refresh Data
elif page == "🔄 Refresh Data":
    st.markdown('<p class="hero-title">🔄 Refresh Data</p>', unsafe_allow_html=True)
    st.markdown('<p class="hero-sub">Scrape the latest inventory from the record store</p>', unsafe_allow_html=True)
    st.markdown("")

    snapshot_dates = dm.get_snapshot_dates(data)
    st.markdown(f"**Current snapshots:** {len(snapshot_dates)}")
    if snapshot_dates:
        st.markdown(f"**Date range:** {snapshot_dates[0]} → {snapshot_dates[-1]}")

    st.markdown("")
    st.warning(
        "⏱️ **Heads up:** Scraping takes **10–20 minutes** depending on inventory size "
        "(the scraper pauses between pages to be polite to the server). "
        "The app will be unresponsive during this time."
    )

    if st.button("🚀 Start Scraping", type="primary", use_container_width=True):
        progress_bar = st.progress(0, text="Initializing...")
        status = st.status("Scraping in progress...", expanded=True)

        def update_progress(pct, msg):
            progress_bar.progress(min(pct, 1.0), text=msg)
            status.write(msg)

        try:
            from scraper import scrape_fresh
            output_path, result_df = scrape_fresh(progress_callback=update_progress)
            status.update(label="✅ Scraping complete!", state="complete")
            progress_bar.progress(1.0, text="Done!")

            st.success(f"Saved **{len(result_df)}** albums to `{output_path}`")
            st.cache_data.clear()
            st.balloons()

            st.info("🔄 Reload the page to see updated data across all sections.")
            if st.button("Reload Now"):
                st.rerun()

        except Exception as e:
            status.update(label="❌ Scraping failed", state="error")
            st.error(f"Error during scraping: {e}")
