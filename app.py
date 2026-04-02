import os

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Walmart Sales Dashboard",
    page_icon="📈",
    layout="wide",
)

DATA_FILE = "Walmart_Sales 2.csv"

@st.cache_data
def load_data(path):
    if not os.path.exists(path):
        return None

    df = pd.read_csv(path)
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    numeric_cols = ["Weekly_Sales", "Temperature", "Fuel_Price", "CPI", "Unemployment"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "Holiday_Flag" in df.columns:
        df["Holiday"] = df["Holiday_Flag"].map({0: "Non-Holiday", 1: "Holiday"})
    else:
        df["Holiday"] = "Unknown"

    if "Date" in df.columns:
        df["Month"] = df["Date"].dt.month_name()
        df["Year"] = df["Date"].dt.year

    return df


def filter_data(df, selected_stores, selected_months, selected_years, selected_holidays, date_range):
    filtered = df.copy()

    if selected_stores:
        filtered = filtered[filtered["Store"].isin(selected_stores)]
    if selected_months:
        filtered = filtered[filtered["Month"].isin(selected_months)]
    if selected_years:
        filtered = filtered[filtered["Year"].isin(selected_years)]
    if selected_holidays:
        filtered = filtered[filtered["Holiday"].isin(selected_holidays)]
    if date_range:
        start_date, end_date = date_range
        filtered = filtered[(filtered["Date"] >= pd.to_datetime(start_date)) & (filtered["Date"] <= pd.to_datetime(end_date))]

    return filtered


def to_csv_download(df):
    return df.to_csv(index=False).encode("utf-8")


def main():
    st.title("Walmart Sales Interactive Dashboard")
    st.markdown(
        "Use the filters in the sidebar to explore weekly store sales, compare holiday periods, and analyze key economic indicators."
    )

    df = load_data(DATA_FILE)
    if df is None:
        st.error(f"Could not find dataset: `{DATA_FILE}`")
        st.info(
            "Place `Walmart_Sales 2.csv` in this folder and refresh the app.\n"
            "Expected columns: Store, Date, Weekly_Sales, Holiday_Flag, Temperature, Fuel_Price, CPI, Unemployment."
        )
        return

    df = df.dropna(subset=["Date", "Weekly_Sales"])

    stores = sorted(df["Store"].unique())
    months = list(df["Month"].dropna().unique())
    years = sorted(df["Year"].dropna().unique())
    holidays = sorted(df["Holiday"].dropna().unique())

    with st.sidebar:
        st.header("Filters")
        selected_stores = st.multiselect("Store", stores, default=stores)
        selected_months = st.multiselect("Month", months, default=months)
        selected_years = st.multiselect("Year", years, default=years)
        selected_holidays = st.multiselect("Holiday Type", holidays, default=holidays)
        date_range = st.date_input(
            "Date range",
            value=(df["Date"].min().date(), df["Date"].max().date()),
            min_value=df["Date"].min().date(),
            max_value=df["Date"].max().date(),
        )
        dark_mode = st.checkbox("Dark mode", value=False)
        if st.button("Reset filters"):
            st.experimental_rerun()

    filtered = filter_data(df, selected_stores, selected_months, selected_years, selected_holidays, date_range)

    if filtered.empty:
        st.warning("No records match the selected filters. Adjust the filters to view data.")
        return

    total_sales = filtered["Weekly_Sales"].sum()
    avg_sales = filtered["Weekly_Sales"].mean()
    highest_row = filtered.loc[filtered["Weekly_Sales"].idxmax()]
    top_week = highest_row["Date"].strftime("%Y-%m-%d") if pd.notna(highest_row["Date"]) else "N/A"
    num_stores = filtered["Store"].nunique()

    template = "plotly_dark" if dark_mode else "plotly"

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total Sales", f"${total_sales:,.0f}")
    kpi2.metric("Avg Weekly Sales", f"${avg_sales:,.0f}")
    kpi3.metric("Highest Sales Week", f"{top_week}")
    kpi4.metric("Number of Stores", f"{num_stores}")

    with st.expander("Download filtered data"):
        st.download_button(
            label="Download CSV",
            data=to_csv_download(filtered),
            file_name="filtered_walmart_sales.csv",
            mime="text/csv",
        )

    sales_by_store = (
        filtered.groupby("Store", as_index=False)["Weekly_Sales"]
        .sum()
        .sort_values("Weekly_Sales", ascending=False)
    )
    fig_store = px.bar(
        sales_by_store,
        x="Store",
        y="Weekly_Sales",
        title="Sales by Store",
        labels={"Weekly_Sales": "Total Weekly Sales"},
        template=template,
        hover_data={"Weekly_Sales": ":,.2f"},
    )

    month_order = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]
    sales_by_month = filtered.groupby("Month", as_index=False)["Weekly_Sales"].sum()
    sales_by_month["Month"] = pd.Categorical(sales_by_month["Month"], categories=month_order, ordered=True)
    sales_by_month = sales_by_month.sort_values("Month")
    fig_month = px.line(
        sales_by_month,
        x="Month",
        y="Weekly_Sales",
        title="Sales by Month",
        labels={"Weekly_Sales": "Total Weekly Sales"},
        template=template,
        markers=True,
    )

    sales_by_year = (
        filtered.groupby("Year", as_index=False)["Weekly_Sales"]
        .sum()
        .sort_values("Year")
    )
    fig_year = px.line(
        sales_by_year,
        x="Year",
        y="Weekly_Sales",
        title="Sales by Year",
        labels={"Weekly_Sales": "Total Weekly Sales"},
        template=template,
        markers=True,
    )

    fig_holiday = px.box(
        filtered,
        x="Holiday",
        y="Weekly_Sales",
        title="Holiday vs Non-Holiday Sales",
        labels={"Weekly_Sales": "Weekly Sales"},
        template=template,
        points="all",
        color="Holiday",
    )

    fig_temp = px.scatter(
        filtered,
        x="Temperature",
        y="Weekly_Sales",
        title="Temperature vs Sales",
        labels={"Weekly_Sales": "Weekly Sales"},
        template=template,
        hover_data={"Store": True, "Date": True},
    )

    fig_fuel = px.scatter(
        filtered,
        x="Fuel_Price",
        y="Weekly_Sales",
        title="Fuel Price vs Sales",
        labels={"Weekly_Sales": "Weekly Sales"},
        template=template,
        hover_data={"Store": True, "Date": True},
    )

    fig_unemployment = px.scatter(
        filtered,
        x="Unemployment",
        y="Weekly_Sales",
        title="Unemployment vs Sales",
        labels={"Weekly_Sales": "Weekly Sales"},
        template=template,
        hover_data={"Store": True, "Date": True},
    )

    fig_cpi = px.scatter(
        filtered,
        x="CPI",
        y="Weekly_Sales",
        title="CPI vs Sales",
        labels={"Weekly_Sales": "Weekly Sales"},
        template=template,
        hover_data={"Store": True, "Date": True},
    )

    top10_weeks = (
        filtered.sort_values("Weekly_Sales", ascending=False)
        .head(10)
        .assign(Week=lambda d: d["Date"].dt.strftime("%Y-%m-%d"))
    )
    fig_top10 = px.bar(
        top10_weeks,
        x="Week",
        y="Weekly_Sales",
        title="Top 10 Highest Sales Weeks",
        labels={"Weekly_Sales": "Weekly Sales"},
        template=template,
        hover_data={"Store": True, "Temperature": True, "Fuel_Price": True},
    )

    weekly_trend = (
        filtered.groupby("Date", as_index=False)["Weekly_Sales"]
        .sum()
        .sort_values("Date")
    )
    fig_trend = px.line(
        weekly_trend,
        x="Date",
        y="Weekly_Sales",
        title="Weekly Sales Trend over Time",
        labels={"Weekly_Sales": "Weekly Sales"},
        template=template,
    )

    fig_hist = px.histogram(
        filtered,
        x="Weekly_Sales",
        nbins=30,
        title="Sales Distribution",
        labels={"Weekly_Sales": "Weekly Sales"},
        template=template,
    )

    numeric_columns = [col for col in ["Weekly_Sales", "Temperature", "Fuel_Price", "CPI", "Unemployment"] if col in filtered.columns]
    corr = filtered[numeric_columns].corr()
    fig_corr = px.imshow(
        corr,
        text_auto=True,
        color_continuous_scale="RdBu",
        title="Correlation Heatmap",
        zmin=-1,
        zmax=1,
        template=template,
    )

    st.plotly_chart(fig_store, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig_month, use_container_width=True)
    with col2:
        st.plotly_chart(fig_year, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig_holiday, use_container_width=True)
    with col2:
        st.plotly_chart(fig_top10, use_container_width=True)

    st.subheader("Economic Drivers vs Weekly Sales")
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig_temp, use_container_width=True)
        st.plotly_chart(fig_fuel, use_container_width=True)
    with col2:
        st.plotly_chart(fig_unemployment, use_container_width=True)
        st.plotly_chart(fig_cpi, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig_trend, use_container_width=True)
    with col2:
        st.plotly_chart(fig_hist, use_container_width=True)

    st.plotly_chart(fig_corr, use_container_width=True)

    st.markdown(
        "---\n"
        "**Tip:** Use the sidebar filters to reuse this dashboard for store-level, month-level, year-level, and holiday comparisons."
    )


if __name__ == "__main__":
    main()
