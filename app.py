import os
import streamlit as st
import pandas as pd
import comtradeapicall
import plotly.graph_objects as go
from datetime import datetime
import time

from dotenv import load_dotenv

# load API key

load_dotenv()
API_KEY = os.getenv("API_KEY")


# Define sectors dictionary
sectors = {
    "84": "Macchinari e apparecchi meccanici",
    "85": "Macchinari e apparecchiature elettriche",
    "87": "Veicoli",
    "39": "Materie plastiche",
    "73": "Articoli in ferro e acciaio",
    "94": "Mobili",
    "64": "Calzature",
    "42": "Articoli in pelle",
    "69": "Prodotti ceramici",
    "33": "Profumeria e cosmetici",
    "71": "Pietre e metalli preziosi",
    "62": "Abbigliamento",
    "30": "Prodotti farmaceutici",
    "88": "Aeromobili e parti",
    "22": "Bevande alcoliche e spiriti",
    "70": "Vetro e articoli in vetro",
    "9004": "Occhiali e dispositivi simili",
    "9003": "Montature per occhiali",
    "9001": "Fibre ottiche, lenti e prismi",
    "68": "Articoli in pietra, gesso, cemento",
    "49": "Libri e giornali stampati",
    "19": "Preparazioni di cereali, pasticceria, pane",
    "20": "Preparazioni di ortaggi e frutta",
    "61": "Abbigliamento a maglia",
    "9506": "Attrezzature sportive e per il fitness",
    "89": "Navi, imbarcazioni e strutture galleggianti",
    "8432": "Macchine agricole per la preparazione del terreno",
    "8433": "Macchine per la raccolta e la trebbiatura",
    "8438": "Macchinari per l'industria alimentare",
}


@st.cache_data
def get_trade_data(year, sector_code):
    """
    Fetch trade data for a specific year and sector
    """
    try:
        df = comtradeapicall.getFinalData(
            API_KEY,
            typeCode="C",
            freqCode="A",
            clCode="HS",
            period=str(year),
            reporterCode=None,
            cmdCode=sector_code,
            flowCode="X",
            partnerCode="0",
            partner2Code=None,
            customsCode=None,
            motCode=None,
            maxRecords=500,
            format_output="JSON",
            aggregateBy=None,
            breakdownMode="classic",
            countOnly=None,
            includeDesc=True,
        )

        if df is not None and not df.empty:
            simplified_df = df[["reporterCode", "reporterDesc", "primaryValue"]].copy()
            simplified_df.columns = ["Country Code", "Country", "Exports (USD)"]
            simplified_df["Country Code"] = pd.to_numeric(simplified_df["Country Code"])
            simplified_df = simplified_df.sort_values(
                "Exports (USD)", ascending=False
            ).reset_index(drop=True)
            return simplified_df
        return None
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        return None


def create_top_10_chart(df, sector_name):
    """
    Create a bar chart of top 10 exporters with Italy highlighted
    Values shown in millions of USD and market share percentage
    """
    top_10 = df.head(10).copy()

    # Convert values to millions and calculate market share
    top_10["Exports (Millions USD)"] = top_10["Exports (USD)"] / 1_000_000
    total_value = df["Exports (USD)"].sum()
    top_10["Market Share"] = (top_10["Exports (USD)"] / total_value) * 100

    # Create text with both value and market share, including a line separator
    # Using HTML formatting for different styles
    text_labels = [
        f'<b>${value:,.0f}M</b><br><span style="color: gray;">─────</span><br><span style="font-family: Arial; font-weight: normal;">{share:.1f}%</span>'
        for value, share in zip(
            top_10["Exports (Millions USD)"], top_10["Market Share"]
        )
    ]

    # Find Italy's position and value
    italy_data = df[df["Country Code"] == 380]
    italy_position = (
        df.index[df["Country Code"] == 380][0] + 1 if not italy_data.empty else None
    )

    # Create colors array (blue for others, red for Italy)
    colors = ["rgb(49, 130, 189)"] * 10  # Default blue
    if not italy_data.empty and italy_position <= 10:
        colors[italy_position - 1] = "rgb(204, 0, 0)"  # Red for Italy

    fig = go.Figure()

    # Add bars with values in millions and rounded corners
    fig.add_trace(
        go.Bar(
            x=top_10["Country"],
            y=top_10["Exports (Millions USD)"],
            marker_color=colors,
            text=text_labels,
            textposition="auto",
            textfont=dict(size=16, family="Arial Black"),
            marker=dict(line_width=0, cornerradius=8),
            textangle=0,
            insidetextanchor="middle",
        )
    )

    # Update layout
    fig.update_layout(
        title=f"Top 10 Exporters - {sector_name}",
        xaxis_title="Country",
        yaxis_title="Exports (Millions USD)",
        showlegend=False,
        height=600,
        bargap=0.2,
        # Ensure enough space for the three-line text
        margin=dict(t=100, b=100),
    )

    return fig, italy_position


def create_position_trend_chart(historical_df, sector_name):
    """
    Create a trend chart showing Italy's position over time
    """
    fig = go.Figure()

    # Create position trend
    fig.add_trace(
        go.Scatter(
            x=historical_df["Year"],
            y=historical_df["Position"],
            name="Position",
            line=dict(color="red", width=3),
            mode="lines+markers",
            marker=dict(size=10),
        )
    )

    # Update layout with two-line title
    fig.update_layout(
        title=dict(
            text="Italy's<br>Competitive Position",
            y=0.95,  # Adjust title position
            x=0.5,
            xanchor="center",
            yanchor="top",
            font=dict(size=14),
        ),
        xaxis=dict(title="Year", dtick=1),
        yaxis=dict(
            title="Global Ranking",
            autorange="reversed",
            tickmode="linear",
            dtick=1,
            range=[historical_df["Position"].max() + 1, 0],
        ),
        height=350,
        showlegend=False,
        margin=dict(t=60),  # Increase top margin for title
    )

    return fig


def create_value_trend_chart(historical_df, sector_name):
    """
    Create a trend chart showing Italy's export value over time with interpolation
    """
    fig = go.Figure()

    # Create value trend with interpolation
    fig.add_trace(
        go.Scatter(
            x=historical_df["Year"],
            y=historical_df["Value"],
            name="Export Value",
            line=dict(color="blue", width=3, shape="spline"),
            mode="lines+markers",
            marker=dict(size=8),
        )
    )

    # Update layout with two-line title
    fig.update_layout(
        title=dict(
            text="Export Value<br>Trend",
            y=0.95,  # Adjust title position
            x=0.5,
            xanchor="center",
            yanchor="top",
            font=dict(size=14),
        ),
        xaxis=dict(title="Year", dtick=1),
        yaxis=dict(title="Exports (Millions USD)", tickformat=",.0f"),
        height=350,
        showlegend=False,
        margin=dict(t=60),  # Increase top margin for title
    )

    return fig


@st.cache_data
def get_historical_data(sector_code, end_year, years=5):
    """
    Fetch historical data for Italy's position over several years
    """
    historical_data = []

    for year in range(end_year - years + 1, end_year + 1):
        try:
            df = get_trade_data(year, sector_code)
            if df is not None:
                italy_data = df[df["Country Code"] == 380]
                if not italy_data.empty:
                    position = df.index[df["Country Code"] == 380][0] + 1
                    value = (
                        italy_data["Exports (USD)"].iloc[0] / 1_000_000
                    )  # Convert to millions
                    historical_data.append(
                        {"Year": year, "Position": position, "Value": value}
                    )
                time.sleep(1)  # Respect API rate limits
        except Exception as e:
            st.warning(f"Could not fetch data for {year}: {str(e)}")

    return pd.DataFrame(historical_data)


def main():
    st.title("🌍 International Trade Analysis")
    st.write("Analyze top exporters by sector with focus on Italy's position")

    # Add citation
    st.markdown(
        """
    <div style='font-size: small; color: gray;'>
    Data source: United Nations Comtrade Database (UN Comtrade)<br>
    Retrieved from https://comtradeplus.un.org
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Sidebar controls
    st.sidebar.header("Settings")
    selected_year = st.sidebar.selectbox(
        "Select Year", range(datetime.now().year - 1, 2017, -1)
    )

    selected_sector = st.sidebar.selectbox(
        "Select Sector",
        options=list(sectors.keys()),
        format_func=lambda x: f"{sectors[x]} ({x})",
    )

    # Main content
    if st.button("Analyze Sector"):
        with st.spinner("Fetching trade data..."):
            # Get current year data
            df = get_trade_data(selected_year, selected_sector)

            if df is not None:
                # Create and display current year chart
                fig_current, italy_position = create_top_10_chart(
                    df, sectors[selected_sector]
                )
                st.plotly_chart(fig_current, use_container_width=True)

                # Get and display historical trends
                with st.spinner("Fetching historical data..."):
                    historical_df = get_historical_data(selected_sector, selected_year)
                    if not historical_df.empty:
                        # Create two columns for the trend charts
                        col1, col2 = st.columns(2)

                        with col1:
                            fig_position = create_position_trend_chart(
                                historical_df, sectors[selected_sector]
                            )
                            st.plotly_chart(fig_position, use_container_width=True)

                        with col2:
                            fig_value = create_value_trend_chart(
                                historical_df, sectors[selected_sector]
                            )
                            st.plotly_chart(fig_value, use_container_width=True)


if __name__ == "__main__":
    main()
